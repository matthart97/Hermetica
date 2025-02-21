import json
import os
import sys


# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the project root relative to this script
project_root = os.path.abspath(os.path.join(current_dir, "../../src/"))
sys.path.append(project_root)  # Append the correct relative path


from ontology.Annotation.ChEBIAnnotator import annotate_text, load_chebi_ontology
# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))



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
        annotation = annotate_text(sentence, chebi_dict)
        results.append(json.loads(annotation))  # Ensure JSON format
    except Exception as e:
        print(f"Error processing sentence: {sentence}")
        print(f"Exception: {e}")

# Save to a JSON file
output_file = "chebi_annotations.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Annotation completed. Results saved in {output_file}")
