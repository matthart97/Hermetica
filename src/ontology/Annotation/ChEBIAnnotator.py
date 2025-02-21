import json
import spacy
import rdflib
import os
from difflib import SequenceMatcher

# ---------------------------
# Load spaCy Model
# ---------------------------
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_lg")
print("spaCy model loaded.")

# ---------------------------
# Load ChEBI Ontology from OWL
# ---------------------------
def load_chebi_ontology(owl_file):
    """
    Parses the ChEBI OWL file and extracts concepts with their labels, synonyms, and descriptions.
    Returns a dictionary {label/synonym: (CHEBI ID, description)}.
    """
    g = rdflib.Graph()
    
    print(f"Loading ChEBI ontology from {owl_file}...")
    g.parse(owl_file, format="xml")  # OWL files use RDF/XML format
    print("Ontology loaded.")

    chebi_concepts = {}

    for s, p, o in g:
        s = str(s)
        p = str(p)
        o = str(o)

        # Extract ChEBI ID
        if "purl.obolibrary.org/obo/CHEBI_" in s:
            chebi_id = s.split("/")[-1].replace("_", ":")

            # Extract Labels (Names)
            if p.endswith("label"):
                chebi_concepts[o.lower()] = (chebi_id, "")

            # Extract Synonyms
            elif p.endswith("hasExactSynonym") or p.endswith("hasRelatedSynonym"):
                chebi_concepts[o.lower()] = (chebi_id, "")

            # Extract Definitions
            elif p.endswith("definition") and chebi_id in chebi_concepts.values():
                chebi_concepts[o.lower()] = (chebi_id, o)

    print(f"Extracted {len(chebi_concepts)} concepts from the ontology.")
    return chebi_concepts

# ---------------------------
# String Similarity Function
# ---------------------------
def string_similarity(a, b):
    """Compute similarity between two strings using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# ---------------------------
# Extract Entities from Text
# ---------------------------
def extract_entities(text):
    """
    Extract entities using spaCy's Named Entity Recognition (NER).
    Returns a list of detected entities.
    """
    doc = nlp(text)
    entities = set(ent.text for ent in doc.ents)
    
    # Include noun chunks as well
    for chunk in doc.noun_chunks:
        if len(chunk.text) > 2:  # Avoid short words
            entities.add(chunk.text)

    return list(entities)

# ---------------------------
# Search ChEBI for Matching Concepts
# ---------------------------
def search_chebi(entity, chebi_dict):
    """
    Search the ChEBI dictionary for the best match.
    Returns the most relevant ChEBI concept.
    """
    best_match = None
    highest_score = 0.0

    for label, (chebi_id, description) in chebi_dict.items():
        similarity = string_similarity(entity, label)
        if similarity > highest_score:
            highest_score = similarity
            best_match = {
                "entity": entity,
                "chebi_id": chebi_id,
                "label": label,
                "description": description,
                "similarity_score": round(similarity, 3)
            }

    return best_match if best_match and best_match["similarity_score"] > 0.7 else None  # Threshold for quality

# ---------------------------
# Annotate Text with ChEBI Concepts
# ---------------------------
def annotate_text(text, chebi_dict):
    """
    Annotate a natural language statement with ChEBI concepts.
    Returns a JSON-formatted string.
    """
    entities = extract_entities(text)
    annotations = []

    for entity in entities:
        match = search_chebi(entity, chebi_dict)
        if match:
            annotations.append(match)

    return json.dumps({"original_sentence": text, "annotations": annotations}, indent=4)

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == "__main__":
    # Path to the ChEBI OWL file (Update this path if needed)
    chebi_owl_file = "/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl"

    if not os.path.exists(chebi_owl_file):
        print(f"Error: {chebi_owl_file} not found. Please provide the correct OWL file.")
        exit(1)

    # Load ChEBI ontology
    chebi_dict = load_chebi_ontology(chebi_owl_file)

    # Example natural language statement
    sentence = "Water and glucose are essential for biological functions."
    annotated_result = annotate_text(sentence, chebi_dict)

    # Output the result
    print("Annotation Result:")
    print(annotated_result)
