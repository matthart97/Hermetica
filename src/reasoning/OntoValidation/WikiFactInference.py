from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON
from owlrl import DeductiveClosure, OWLRL_Semantics
import pandas as pd

# Define the Wikidata namespace
WIKIDATA = Namespace("http://www.wikidata.org/entity/")
ontology_graph = Graph()
ontology_graph.bind("wd", WIKIDATA)

# Define Wikidata SPARQL endpoint
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# Function to query Wikidata for meaningful entity relationships
def query_wikidata(entity_id):
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(f"""
        SELECT ?property ?value WHERE {{
            wd:{entity_id} ?property ?value .
            FILTER (STRSTARTS(STR(?property), "http://www.wikidata.org/prop/")) # Only meaningful properties
            FILTER (STRSTARTS(STR(?value), "http://www.wikidata.org/entity/")) # Only entity relationships
        }} 
        LIMIT 20
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    triples = []
    for result in results["results"]["bindings"]:
        prop = result["property"]["value"]
        val = result["value"]["value"]
        triples.append((URIRef(f"http://www.wikidata.org/entity/{entity_id}"), URIRef(prop), URIRef(val)))

    return triples

# Entities extracted by the formulizer (example subset)
entities = [
    "Q937",       # Albert Einstein
    "Q983751",    # Relativity
    "Q27877266",  # The Theory
    "Q28865",     # Python (programming language)
    "Q19018512",  # The Eiffel Tower
]

# Query and add only relevant triples to the graph
for entity in entities:
    triples = query_wikidata(entity)
    for triple in triples:
        ontology_graph.add(triple)

# Apply OWL reasoning only to relevant facts
DeductiveClosure(OWLRL_Semantics).expand(ontology_graph)

# Filter out schema-level information from output
filtered_triples = [
    (s, p, o) for s, p, o in ontology_graph
    if "www.w3.org" not in str(s) and "www.w3.org" not in str(p) and "www.w3.org" not in str(o)  # Remove RDF/OWL/XSD data
]

# Convert to DataFrame for easy visualization
df = pd.DataFrame(filtered_triples, columns=["Subject", "Predicate", "Object"])

# Save and display results
df.to_csv("wikidata_filtered_output.csv", index=False)
print("Filtered Wikidata ontology reasoning output saved to 'wikidata_filtered_output.csv'.")
