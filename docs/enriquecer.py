import os
import pandas as pd
import requests
import urllib.parse
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Rutas
BASE_DIR = r'C:\Users\javal\OneDrive\Escritorio\InteligenciaArtificial\papers'
INPUT_CSV        = os.path.join(BASE_DIR, 'papers_metadata.csv')
OUTPUT_ENRICHED  = os.path.join(BASE_DIR, 'papers_metadata_enriched.csv')
OUTPUT_TOPICS    = os.path.join(BASE_DIR, 'papers_metadata_with_topics.csv')
OUTPUT_FINAL     = os.path.join(BASE_DIR, 'papers_metadata_final.csv')

# Columnas a añadir
OA_COLS  = ['oa_id','venue_id','venue_name','concept_ids','concept_labels','citation_count']
ROR_COLS = ['ror_id','ror_name','ror_country']

# --- Funciones de enriquecimiento ---
def enrich_openalex(doi):
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        r = requests.get(url, timeout=10); r.raise_for_status()
        j = r.json()
        return {
            'oa_id': j.get('id','').split('/')[-1],
            'venue_id': j.get('host_venue',{}).get('id','').split('/')[-1],
            'venue_name': j.get('host_venue',{}).get('display_name',''),
            'concept_ids': ';'.join(c.get('id','').split('/')[-1] for c in j.get('concepts',[])),
            'concept_labels': ';'.join(c.get('display_name','') for c in j.get('concepts',[])),
            'citation_count': j.get('cited_by_count',0)
        }
    except Exception as e:
        print(f"Error OpenAlex DOI={doi}: {e}")
        return dict(zip(OA_COLS, ['']*len(OA_COLS)))

def enrich_ror(aff_text):
    inst = aff_text.split(',')[0]
    q = urllib.parse.quote(inst)
    url = f"https://api.ror.org/organizations?query={q}"
    try:
        r = requests.get(url, timeout=10); r.raise_for_status()
        items = r.json().get('items',[])
        if items:
            top = items[0]
            return {
                'ror_id': top.get('id',''),
                'ror_name': top.get('name',''),
                'ror_country': top.get('country',{}).get('country_name','')
            }
    except Exception as e:
        print(f"Error ROR affiliation={aff_text}: {e}")
    return dict(zip(ROR_COLS, ['']*len(ROR_COLS)))

# --- 1) Leer CSV brutos ---
df = pd.read_csv(INPUT_CSV, encoding='utf-8')

# --- 2) Enriquecer OpenAlex y ROR ---
for col in OA_COLS + ROR_COLS:
    df[col] = ''

for idx, row in df.iterrows():
    doi = row['doi']
    oa = enrich_openalex(doi)
    for c in OA_COLS: df.at[idx, c] = oa.get(c,'')
    aff0 = (str(row.get('affiliations','')).split(';') or [''])[0]
    ror = enrich_ror(aff0)
    for c in ROR_COLS: df.at[idx, c] = ror.get(c,'')

df.to_csv(OUTPUT_ENRICHED, index=False, encoding='utf-8')
print(f"Enriquecimiento completado: {OUTPUT_ENRICHED}")

# --- 3) Topic Modeling ---
docs = df['abstract'].fillna('').tolist()
tm = BERTopic(language='english')
topics, _ = tm.fit_transform(docs)
df['topic_id']    = topics
df['topic_label'] = [
    tm.get_topic(t)[0][0] if t != -1 and tm.get_topic(t) else ''
    for t in topics
]
df.to_csv(OUTPUT_TOPICS, index=False, encoding='utf-8')
print(f"Topic modeling completado: {OUTPUT_TOPICS}")

# --- 4) Similaridad entre papers (top 5 abstracts más parecidos) ---
# Vectorizamos los abstracts
st_model = SentenceTransformer('all-mpnet-base-v2')
docs = df['abstract'].fillna('').tolist()
embeddings = st_model.encode(docs, convert_to_tensor=True)

# Calculamos la matriz de similitud coseno
cos_sim = util.cos_sim(embeddings, embeddings)

# Para cada paper, extraemos los 5 más similares (sin contar a sí mismo)
top_k = 5
similar_lists = []
for i in range(len(df)):
    # topk devuelve (scores, índices)
    scores, idxs = cos_sim[i].topk(top_k + 1)
    # descartamos el primero (auto-similitud) y nos quedamos con top_k
    idxs = idxs.tolist()[1:top_k+1]
    # mapeamos índices a DOIs
    similars = [ df.iloc[j]['doi'] for j in idxs ]
    similar_lists.append(';'.join(similars))

# Añadimos la columna al DataFrame
df['top5_similar'] = similar_lists


# --- 5) NER en acknowledgements ---
ner = pipeline('ner', model='dslim/bert-base-NER', grouped_entities=True)
persons, orgs = [], []
for text in df['acknowledgements'].fillna(''):
    ents = ner(text)
    pers = sorted({e['word'] for e in ents if e['entity_group']=='PER'})
    org_ = sorted({e['word'] for e in ents if e['entity_group']=='ORG'})
    persons.append(';'.join(pers))
    orgs.append(';'.join(org_))
df['ner_persons'] = persons
df['ner_orgs']    = orgs

# --- 6) Guardar CSV final ---
df.to_csv(OUTPUT_FINAL, index=False, encoding='utf-8')
print(f"Pipeline completo: CSV final generado en {OUTPUT_FINAL}")