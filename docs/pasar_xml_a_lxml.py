import os
import glob
import pandas as pd
from lxml import etree

# Directorio de entrada de XMLs
XML_DIR = r'C:\Users\javal\OneDrive\Escritorio\InteligenciaArtificial\papers'
# Patrón de archivos
XML_PATTERN = os.path.join(XML_DIR, '*.xml')

# Espacio de nombres TEI
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

records = []

for xml_path in glob.glob(XML_PATTERN):
    tree = etree.parse(xml_path)
    rec = {'file': os.path.basename(xml_path)}

    # 1. Título principal
    title = tree.findtext('.//tei:titleStmt/tei:title[@type="main"]', namespaces=NS)
    if not title:
        title = tree.findtext('.//tei:titleStmt/tei:title', namespaces=NS) or ''
    rec['title'] = title

    # 2. Autores (solo del artículo, no de referencias)
    authors = []
    author_elems = tree.xpath('.//tei:sourceDesc//tei:analytic//tei:author', namespaces=NS)
    for author in author_elems:
        pers = author.find('tei:persName', namespaces=NS)
        if pers is not None:
            forenames = [fn.text for fn in pers.findall('tei:forename', namespaces=NS) if fn.text]
            surname = pers.findtext('tei:surname', namespaces=NS) or ''
            full_name = ' '.join(forenames + [surname]).strip()
            authors.append(full_name)
    rec['authors'] = ';'.join(authors)

    # 3. Afiliaciones (orgName y country en affiliation)
    affiliations = []
    aff_path = './/tei:sourceDesc//tei:analytic//tei:author/tei:affiliation'
    for aff in tree.findall(aff_path, namespaces=NS):
        org_names = [on.text for on in aff.findall('tei:orgName', namespaces=NS) if on.text]
        country = aff.findtext('.//tei:country', namespaces=NS)
        parts = org_names + ([country] if country else [])
        affiliations.append(', '.join(parts))
    rec['affiliations'] = ';'.join(affiliations)

    # 3b. Países del artículo (todos los country de las afiliaciones)
    countries = []
    for aff in tree.findall(aff_path, namespaces=NS):
        c = aff.findtext('.//tei:country', namespaces=NS)
        if c:
            countries.append(c)
    rec['countries'] = ';'.join(sorted(set(countries)))

    # 4. Abstract
    abs_elem = tree.find('.//tei:abstract//tei:p', namespaces=NS)
    rec['abstract'] = ''.join(abs_elem.itertext()).strip() if abs_elem is not None else ''

    # 5. Acknowledgements (texto plano de todos los <p>)
    ack_ps = tree.xpath('.//tei:div[@type="acknowledgement"]//tei:p', namespaces=NS)
    if ack_ps:
        rec['acknowledgements'] = ' '.join(
            ''.join(p.itertext()).strip() for p in ack_ps
        )
    else:
        rec['acknowledgements'] = ''

    # 6. Fecha de publicación (monogr/imprint/date)
    pub_date = tree.findtext('.//tei:monogr//tei:imprint//tei:date', namespaces=NS)
    rec['publication_date'] = pub_date or ''

    # 7. DOI (idno type DOI)
    doi = tree.findtext('.//tei:idno[@type="DOI"]', namespaces=NS)
    rec['doi'] = doi or ''

    records.append(rec)

# Crear DataFrame y exportar a CSV
if records:
    df = pd.DataFrame(records)
    output_csv = os.path.join(XML_DIR, 'papers_metadata.csv')
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Metadata extraída de {len(df)} papers. CSV generado en: {output_csv}")
else:
    print("No se encontraron ficheros XML en el directorio especificado.")