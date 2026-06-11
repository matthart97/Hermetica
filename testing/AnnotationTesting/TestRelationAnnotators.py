import json
import sys
import os

# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the project root relative to this script
project_root = os.path.abspath(os.path.join(current_dir, "../../src/"))
sys.path.append(project_root)  # Append the correct relative path

# Import the annotation function
from ontology.Annotation.WikiDataRelationsAnn import annotate_text as WikiAnn
from ontology.Annotation.ChEBIRelationsAnn import annotate_text as ChEBIAnn
from ontology.Annotation.ChEBIRelationsAnn import load_chebi_ontology

# test the wikidata relationships annotator


# Define the relative path for the dataset
dataset_path = os.path.join(current_dir, "TestSentancesGeneral.txt")
output_path = os.path.join(current_dir, "WikiRelAnnotations.json")
#Load sentences from the dataset
with open(dataset_path, "r", encoding="utf-8") as f:
    sentences = [line.strip() for line in f.readlines()]

# Annotate all sentences
results = []
for sentence in sentences:
    try:
        annotation = WikiAnn(sentence)
        results.append(json.loads(annotation))  # Ensure JSON format
    except Exception as e:
        print(f"Error processing sentence: {sentence}")
        print(f"Exception: {e}")

# Save to a JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Wiki Annotation completed. Results saved in {output_path}")

# test ChEBI Relationships annotation 

# Path to the ChEBI ontology OWL file
chebi_owl_file = "../../data/ontologies/Chemistry/chebi.owl"

if not os.path.exists(chebi_owl_file):
    print(f"Error: {chebi_owl_file} not found. Ensure the ChEBI OWL file is in the correct directory.")
    exit(1)

# Load the ChEBI ontology
chebi_dict = load_chebi_ontology(chebi_owl_file)

# Load example sentences
sentences_file = "ChEBITesting.txt"
if not os.path.exists(sentences_file):
    print(f"Error: {sentences_file} not found. Ensure the test sentences file is in the correct directory.")
    exit(1)

with open(sentences_file, "r", encoding="utf-8") as f:
    sentences = [line.strip() for line in f.readlines()]

# Annotate all sentences
results = []
for sentence in sentences:
    try:
        annotation = ChEBIAnn(sentence, chebi_dict)
        results.append(json.loads(annotation))  # Ensure JSON format
    except Exception as e:
        print(f"Error processing sentence: {sentence}")
        print(f"Exception: {e}")

# Save to a JSON file
output_file = "chebiRelAnnotations.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Annotation completed. Results saved in {output_file}")

