from rdflib import Graph, Namespace, URIRef, Literal
import json

# Step 1: Load ChEBI Ontology (Local)
CHEBI_FILE = "/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl"
ontology_graph = Graph()
ontology_graph.parse(CHEBI_FILE, format="xml")

# Step 2: Define ChEBI Namespace
CHEBI = Namespace("http://purl.obolibrary.org/obo/CHEBI_")
ontology_graph.bind("chebi", CHEBI)

# Step 3: Define Relevant Relationships
RELEVANT_RELATIONS = {
    URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf"): "is a subclass of",
    URIRef("http://purl.obolibrary.org/obo/RO_0000087"): "has role",
    URIRef("http://purl.obolibrary.org/obo/BFO_0000050"): "is part of",
    URIRef("http://purl.obolibrary.org/obo/CHEBI_50906"): "has functional parent",
    URIRef("http://purl.obolibrary.org/obo/CHEBI_33232"): "has application",
    URIRef("http://purl.obolibrary.org/obo/CHEBI_50906"): "has biological role",
}

# Step 4: Extract Labels for All Entities
chebi_labels = {}
for s, _, o in ontology_graph.triples((None, URIRef("http://www.w3.org/2000/01/rdf-schema#label"), None)):
    chebi_id = str(s).split("/")[-1]
    chebi_labels[chebi_id] = str(o)

# Step 5: Extract All Inferable Facts
all_facts = []
for s, p, o in ontology_graph.triples((None, None, None)):
    if p in RELEVANT_RELATIONS:
        fact = {
            "subject_id": str(s).split("/")[-1],
            "subject_label": chebi_labels.get(str(s).split("/")[-1], str(s)),
            "predicate": RELEVANT_RELATIONS[p],
            "object_id": str(o).split("/")[-1],
            "object_label": chebi_labels.get(str(o).split("/")[-1], str(o)),
        }
        all_facts.append(fact)

# Step 6: Save All Facts to a JSON File
with open("chebi_inferred_facts.json", "w") as f:
    json.dump(all_facts, f, indent=4)

print(f"Precomputed {len(all_facts)} ChEBI facts saved to 'chebi_inferred_facts.json'.")



# Load the precomputed ChEBI facts
with open("chebi_inferred_facts.json", "r") as f:
    chebi_facts = json.load(f)

# Function to Query Facts by Subject, Predicate, or Object
def query_chebi_facts(subject=None, predicate=None, object_=None):
    results = []
    for fact in chebi_facts:
        if (subject and subject.lower() not in fact["subject_label"].lower()) and subject:
            continue
        if (predicate and predicate.lower() not in fact["predicate"].lower()) and predicate:
            continue
        if (object_ and object_.lower() not in fact["object_label"].lower()) and object_:
            continue
        results.append(fact)
    return results

# Example Queries
print("\n🔎 Query: Facts about 'Aspirin'")
for fact in query_chebi_facts(subject="Aspirin"):
    print(f'{fact["subject_label"]} {fact["predicate"]} {fact["object_label"]}.')

print("\n🔎 Query: Facts where predicate is 'has role'")
for fact in query_chebi_facts(predicate="has role"):
    print(f'{fact["subject_label"]} {fact["predicate"]} {fact["object_label"]}.')
