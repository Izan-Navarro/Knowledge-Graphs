import os
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

# --- Configuración de rutas ---
BASE_DIR = r'C:\Users\javal\OneDrive\Escritorio\InteligenciaArtificial\papers'
INPUT_CSV = os.path.join(BASE_DIR, 'papers_metadata_final.csv')
OUTPUT_TTL = os.path.join(BASE_DIR, 'rkg_final_3.ttl')

# --- Namespaces ---
EX      = Namespace("https://grupo6.org/ontology#")
PAPER   = Namespace("https://grupo6.org/paper/")
AUTHOR  = Namespace("https://grupo6.org/author/")
TOPIC   = Namespace("https://grupo6.org/topic/")
MEDIOS   = Namespace("https://grupo6.org/venue/")
ROR_NS  = Namespace("https://ror.org/")
COUNTRY = Namespace("https://grupo6.org/country/")
SCHEMA  = Namespace("http://schema.org/")

# --- Función auxiliar para IDs seguras ---
def safe_id(raw: str) -> str:
    return raw.strip().replace('/', '_').replace(' ', '_')

# 1) Cargar CSV final
df = pd.read_csv(INPUT_CSV, encoding='utf-8')

# 2) Crear grafo e importar ontología
g = Graph()
# Registrar prefijos
for prefix, ns in [
    ("ex", EX), ("paper", PAPER), ("author", AUTHOR),
    ("topic", TOPIC), ("venue", MEDIOS), ("ror", ROR_NS), ("ctry", COUNTRY),
]:
    g.bind(prefix, ns)
g.bind("schema", SCHEMA)

# 3) Recorrer cada fila y crear triples
for _, row in df.iterrows():
    doi = str(row.get('doi', ''))
    if not doi:
        continue
    pid = safe_id(doi)
    paper_uri = URIRef(PAPER + pid)
    # Tipo
    g.add((paper_uri, RDF.type, EX.Paper))
    # Data properties de Paper
    g.add((paper_uri, EX.doi, Literal(doi, datatype=XSD.string)))
    title = row.get('title', '')
    if title:
        g.add((paper_uri, EX.titulo, Literal(title, datatype=XSD.string)))
    pub_date = row.get('publication_date', '')
    if pub_date:
        # Guardar fecha como string para evitar errores de formato xsd:date
        g.add((paper_uri, EX.fechaPublicacion, Literal(pub_date, datatype=XSD.string)))
    cit_count = row.get('citation_count')
    if pd.notna(cit_count):
        try:
            g.add((paper_uri, EX.numeroCitas, Literal(int(cit_count), datatype=XSD.integer)))
        except:
            pass

    # Authors
    for name in str(row.get('authors', '')).split(';'):
        if not name:
            continue
        aid = safe_id(name)
        author_uri = URIRef(AUTHOR + aid)
        g.add((author_uri, RDF.type, EX.Author))
        g.add((author_uri, EX.nombreAutor, Literal(name, datatype=XSD.string)))
        g.add((paper_uri, EX.paperEscritos, author_uri))

    # Affiliation / Institution via ROR
    ror_id = row.get('ror_id', '')
    if pd.notna(ror_id) and ror_id:
        inst_uri = URIRef(ror_id)
        g.add((inst_uri, RDF.type, EX.Institution))
        ror_name = row.get('ror_name', '')
        if ror_name:
            g.add((inst_uri, EX.nombreInstitucion, Literal(ror_name, datatype=XSD.string)))
        ror_country = row.get('ror_country', '')
        if ror_country:
            cid = safe_id(ror_country)
            c_uri = URIRef(COUNTRY + cid)
            g.add((c_uri, RDF.type, EX.Country))
            g.add((c_uri, EX.nombrePais, Literal(ror_country, datatype=XSD.string)))
            g.add((inst_uri, EX.origenEn, c_uri))
        for name in str(row.get('authors', '')).split(';'):
            if not name:
                continue
            a_uri = URIRef(AUTHOR + safe_id(name))
            g.add((a_uri, EX.trabajaEn, inst_uri))

    # Medios
    venue_id = row.get('venue_id', '')
    if pd.notna(venue_id) and venue_id:
        v_uri = URIRef(MEDIOS + safe_id(venue_id))
        g.add((v_uri, RDF.type, EX.Venue))
        vname = row.get('venue_name', '')
        if vname:
            g.add((v_uri, EX.nombreMedio, Literal(vname, datatype=XSD.string)))
        g.add((paper_uri, EX.publicadoEn, v_uri))

    # Topics
    ids = str(row.get('concept_ids', '')).split(';')
    labels = str(row.get('concept_labels', '')).split(';')
    for cid, lbl in zip(ids, labels):
        if not cid:
            continue
        t_uri = URIRef(TOPIC + safe_id(cid))
        g.add((t_uri, RDF.type, EX.Topic))
        if lbl:
            g.add((t_uri, RDFS.label, Literal(lbl, datatype=XSD.string)))
        g.add((paper_uri, EX.perteneceA, t_uri))

    # Similarity (top5 similar DOIs)
    sim = str(row.get('top5_similar', '')).split(';')
    for sdoi in sim:
        if not sdoi:
            continue
        s_uri = URIRef(PAPER + safe_id(sdoi))
        g.add((paper_uri, EX.similarA, s_uri))

# 4) Serializar grafo a Turtle (modo texto)
with open(OUTPUT_TTL, 'w', encoding='utf-8') as f:
    f.write(g.serialize(format='turtle'))
print(f"RDF serializado en: {OUTPUT_TTL}")