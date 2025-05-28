import os
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

# --- Configuración de rutas ---
BASE_DIR = r'C:\Users\javal\OneDrive\Escritorio\InteligenciaArtificial\papers'
INPUT_CSV = os.path.join(BASE_DIR, 'papers_metadata_final_2.csv')
OUTPUT_TTL = os.path.join(BASE_DIR, 'rkg_final_2.ttl')

# --- Namespaces ---
EX      = Namespace("https://grupo6.org/ontology#")
PAPER   = Namespace("https://grupo6.org/paper/")
AUTHOR  = Namespace("https://grupo6.org/author/")
TOPIC   = Namespace("https://grupo6.org/topic/")
MEDIOS  = Namespace("https://grupo6.org/venue/")
ROR_NS  = Namespace("https://grupo6.org/institution/")
COUNTRY = Namespace("https://grupo6.org/country/")
SCHEMA  = Namespace("http://schema.org/")

# --- Función auxiliar para IDs seguras ---
def safe_id(raw) -> str:
    """
    Convierte cualquier valor raw en un identificador URI seguro:
    - Convierte a str, en minúsculas, reemplaza '/', ' ', '-' por '_'.
    """
    s = str(raw) if raw is not None else ''
    return s.strip().lower().replace('/', '_').replace(' ', '_').replace('-', '_')

# 1) Cargar CSV final
df = pd.read_csv(INPUT_CSV, encoding='utf-8')

g = Graph()
# 2) Registrar prefijos
for prefix, ns in [
    ("ex", EX), ("paper", PAPER), ("author", AUTHOR),
    ("topic", TOPIC), ("venue", MEDIOS), ("ror", ROR_NS), ("ctry", COUNTRY)
]:
    g.bind(prefix, ns)
g.bind("schema", SCHEMA)

# 3) Recorrer cada fila y crear triples
for _, row in df.iterrows():
    doi = str(row.get('doi','')).strip()
    if not doi:
        continue
    pid = safe_id(doi)
    paper_uri = URIRef(PAPER + pid)
    g.add((paper_uri, RDF.type, EX.Paper))
    # Data properties de Paper
    g.add((paper_uri, EX.doi, Literal(doi, datatype=XSD.string)))
    title = row.get('title','')
    if pd.notna(title) and title:
        g.add((paper_uri, EX.titulo, Literal(title, datatype=XSD.string)))
    pub_date = row.get('publication_date','')
    if pd.notna(pub_date) and pub_date:
        g.add((paper_uri, EX.fechaPublicacion, Literal(pub_date, datatype=XSD.string)))
    cit_count = row.get('citation_count')
    if pd.notna(cit_count):
        try:
            g.add((paper_uri, EX.numeroCitas, Literal(int(cit_count), datatype=XSD.integer)))
        except:
            pass

    # Authors
    for name in str(row.get('authors','')).split(';'):
        if name:
            aid = safe_id(name)
            author_uri = URIRef(AUTHOR + aid)
            g.add((author_uri, RDF.type, EX.Author))
            g.add((author_uri, EX.nombreAutor, Literal(name, datatype=XSD.string)))
            g.add((paper_uri, EX.paperEscritos, author_uri))

    # Affiliation / Institution via ROR con custom ID
    ror_id = row.get('ror_id','')
    if pd.notna(ror_id) and ror_id:
        inst_name = row.get('ror_name','')
        inst_local = safe_id(inst_name) if pd.notna(inst_name) and inst_name else safe_id(ror_id)
        inst_uri = URIRef(ROR_NS + inst_local)
        g.add((inst_uri, RDF.type, EX.Institution))
        # nombre humano
        if pd.notna(inst_name) and inst_name:
            g.add((inst_uri, EX.nombreInstitucion, Literal(inst_name, datatype=XSD.string)))
        # conservar ROR original
        g.add((inst_uri, EX.rorId, Literal(ror_id, datatype=XSD.string)))
        # país de origen
        country_name = row.get('ror_country','')
        if pd.notna(country_name) and country_name:
            country_local = safe_id(country_name)
            country_uri = URIRef(COUNTRY + country_local)
            g.add((country_uri, RDF.type, EX.Country))
            g.add((country_uri, EX.nombrePais, Literal(country_name, datatype=XSD.string)))
            g.add((inst_uri, EX.origenEn, country_uri))
        # vincular autores con institución
        for author_name in str(row.get('authors','')).split(';'):
            if author_name:
                auth_uri = URIRef(AUTHOR + safe_id(author_name))
                g.add((auth_uri, EX.trabajaEn, inst_uri))

    # Venue
    venue_id = row.get('venue_id','')
    if pd.notna(venue_id) and venue_id:
        v_uri = URIRef(MEDIOS + safe_id(venue_id))
        g.add((v_uri, RDF.type, EX.Venue))
        vname = row.get('venue_name','')
        if pd.notna(vname) and vname:
            g.add((v_uri, EX.nombreMedio, Literal(vname, datatype=XSD.string)))
        g.add((paper_uri, EX.publicadoEn, v_uri))

    # Topics
    ids = str(row.get('concept_ids','')).split(';')
    labels = str(row.get('concept_labels','')).split(';')
    for cid, lbl in zip(ids, labels):
        if cid:
            t_uri = URIRef(TOPIC + safe_id(cid))
            g.add((t_uri, RDF.type, EX.Topic))
            if lbl:
                g.add((t_uri, RDFS.label, Literal(lbl, datatype=XSD.string)))
            g.add((paper_uri, EX.perteneceA, t_uri))

    # Similarity
    for sdoi in str(row.get('top_similar','')).split(';'):
        if sdoi:
            s_uri = URIRef(PAPER + safe_id(sdoi))
            g.add((paper_uri, EX.similarA, s_uri))

# 4) Serializar grafo a Turtle
data = g.serialize(format='turtle')
with open(OUTPUT_TTL, 'w', encoding='utf-8') as f:
    f.write(data)
print(f"RDF serializado en: {OUTPUT_TTL}")