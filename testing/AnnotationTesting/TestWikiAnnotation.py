import json
import sys
import os

# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the project root relative to this script
project_root = os.path.abspath(os.path.join(current_dir, "../../src/"))
sys.path.append(project_root)  # Append the correct relative path

# Import the annotation function
from ontology.Annotation.WikiDataAnnotator import annotate_text  # Adjusted import

# Define the relative path for the dataset
dataset_path = os.path.join(current_dir, "TestSentancesGeneral.txt")
output_path = os.path.join(current_dir, "annotations.json")

# Load sentences from the dataset
with open(dataset_path, "r", encoding="utf-8") as f:
    sentences = [line.strip() for line in f.readlines()]

# Annotate all sentences
results = []
for sentence in sentences:
    try:
        annotation = annotate_text(sentence)
        results.append(json.loads(annotation))  # Ensure JSON format
    except Exception as e:
        print(f"Error processing sentence: {sentence}")
        print(f"Exception: {e}")

# Save to a JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Annotation completed. Results saved in {output_path}")
