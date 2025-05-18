from SPARQLWrapper import SPARQLWrapper, JSON
import streamlit as st

# URL del endpoint SPARQL de Fuseki
endpoint = "http://localhost:3030/IA/sparql"

def run_query(query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

st.title("Consultas SPARQL a la base de datos")

# Selector de consulta
options = [
    "Todos los papers",
    "Papers sin fecha valida",
    "Papers por número de Topics",
    "Autores de un paper específico",
    "Listar todos los Topics de un Paper",
    "Buscar Papers que pertenecen al Topic",
    "Contar cuántos Autores tiene cada Paper",
    "Listar todas las Instituciones con su País de origen y nombre",
    "Contar cuántas Instituciones hay por País",
    "Listar todos los Países definidos",
    "Instituciones de un País concreto"
]
selected_query = st.selectbox("Selecciona la consulta que quieres ejecutar:", options)

# Input si selecciona "Autores de un paper específico"
if selected_query == "Autores de un paper específico" or selected_query == "Listar todos los Topics de un Paper":
    doi_input = st.text_input("Introduce el identificador del paper (por ejemplo: 10.1007_s11036-021-01777-7)")
elif selected_query == "Buscar Papers que pertenecen al Topic":
    label_input = st.text_input("Introduce el topic que quieras buscar")
elif selected_query == "Contar cuántos Autores tiene cada Paper":
    num_input = st.text_input("Introduce el numero máximo de autores")
elif selected_query == "Instituciones de un País concreto":
    country_input = st.text_input("Introduce el pais").replace(" ", "_")


if st.button("Ejecutar consulta"):
    if selected_query == "Todos los papers":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?paper ?doi ?title ?citas WHERE {
          ?paper rdf:type ex:Paper ;
            ex:doi ?doi ;
            ex:titulo ?title ;
            ex:numeroCitas ?citas .
        }
        ORDER BY DESC(?citas)
        """
    elif selected_query == "Papers sin fecha valida":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?paper ?doi WHERE {
        ?paper rdf:type ex:Paper ;
                ex:doi ?doi ;
                ex:fechaPublicacion ?f .
        FILTER(str(?f) = "nan")
        }
        """
    elif selected_query == "Papers por número de Topics":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?paper (COUNT(?topic) AS ?numTopics) WHERE {
        ?paper rdf:type ex:Paper ;
                ex:perteneceA ?topic .
        }
        GROUP BY ?paper
        ORDER BY DESC(?numTopics)
        """
    elif selected_query == "Autores de un paper específico":
        if not doi_input:
            st.warning("Por favor, introduce el identificador del paper.")
            st.stop()

        query = f"""
        PREFIX ex: <https://grupo6.org/ontology#>
        PREFIX paper: <https://grupo6.org/paper/>

        SELECT ?autor ?name
        WHERE {{
            paper:{doi_input} ex:paperEscritos ?autor .
            ?autor ex:nombreAutor ?name .
        }}
        """
    elif selected_query == "Listar todos los Topics de un Paper":
        if not doi_input:
            st.warning("Por favor, introduce el identificador del paper.")
            st.stop()

        query = f"""
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?topic ?label WHERE {{
            paper:{doi_input} ex:perteneceA ?topic .
            OPTIONAL {{ ?topic rdfs:label ?label }}
        }}
            
        """
    elif selected_query == "Buscar Papers que pertenecen al Topic":
        if not label_input:
            st.warning("Por favor, introduce el topic.")
            st.stop()

        query = f"""
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?paper ?doi ?title WHERE {{
        ?paper ex:perteneceA ?topic ;
                ex:doi ?doi ;
                ex:titulo ?title .
        ?topic rdfs:label "{label_input}" .
        }}
            
        """
    elif selected_query == "Contar cuántos Autores tiene cada Paper":
        if not num_input:
            st.warning("Por favor, introduce el número.")
            st.stop()

        query = f"""
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?paper (COUNT(?author) AS ?nAuthors) WHERE {{
        ?paper rdf:type ex:Paper ;
                ex:paperEscritos ?author .
        }}
        GROUP BY ?paper
        HAVING(?nAuthors <= {num_input})
        """
    elif selected_query == "Listar todas las Instituciones con su País de origen y nombre":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?inst ?instName ?country ?countryName WHERE {
        ?inst rdf:type ex:Institution ;
                ex:nombreInstitucion ?instName ;
                ex:origenEn ?country .
        ?country ex:nombrePais ?countryName .
        }
        ORDER BY ?countryName ?instName
        """
    elif selected_query == "Contar cuántas Instituciones hay por País":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?countryName (COUNT(?inst) AS ?numInst) WHERE {
        ?inst rdf:type ex:Institution ;
                ex:origenEn ?country .
        ?country ex:nombrePais ?countryName .
        }
        GROUP BY ?countryName
        ORDER BY DESC(?numInst)
        """
    elif selected_query == "Listar todos los Países definidos":
        query = """
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?country ?countryName WHERE {
        ?country rdf:type ex:Country ;
            ex:nombrePais ?countryName .
        }
        ORDER BY ?countryName
        """
    elif selected_query == "Instituciones de un País concreto":
        if not country_input:
            st.warning("Por favor, introduce el pais.")
            st.stop()

        query = f"""
        PREFIX ex:     <https://grupo6.org/ontology#>
        PREFIX paper:  <https://grupo6.org/paper/>
        PREFIX author: <https://grupo6.org/author/>
        PREFIX topic:  <https://grupo6.org/topic/>
        PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ex:    <https://grupo6.org/ontology#>
        PREFIX ror:   <https://ror.org/>
        PREFIX ctry:  <https://grupo6.org/country/>
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        
        SELECT ?inst ?instName WHERE {{
        ?inst rdf:type ex:Institution ;
            ex:nombreInstitucion ?instName ;
            ex:origenEn ctry:{country_input} .
        }}
        ORDER BY ?instName
        """


    results = run_query(query)

    # Mostrar resultados
    if "bindings" in results["results"]:
        rows = results["results"]["bindings"]
        if rows:
            data = []
            cols = list(rows[0].keys())
            for row in rows:
                data.append({col: row[col]["value"] for col in cols})
            st.write(f"Resultados de: **{selected_query}**")
            st.dataframe(data)
        else:
            st.warning("No se encontraron resultados.")
    else:
        st.error("Error en la respuesta del endpoint.")
