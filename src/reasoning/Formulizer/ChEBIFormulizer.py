import json

def formulize_chebi_annotations(annotations):
    """
    Converts ChEBI entity annotations and relationships into logical statements.
    Handles ChEBI-specific ontology relationships like 'is_a', 'has_role', etc.
    """
    logical_statements = []
    
    for entry in annotations:
        sentence = entry["original_sentence"]
        entities = entry["annotations"]
        relationships = entry.get("relationships", [])
        
        entity_mappings = {}
        
        # Process ChEBI entities
        for entity in entities:
            chebi_id = entity["chebi_id"]  # Expected format: "CHEBI:XXXXX"
            label = entity["label"].replace(" ", "_")  # Format for logical expressions
            
            # Store both original text and normalized form
            entity_mappings[entity["entity"]] = {
                "id": chebi_id,
                "label": label
            }
            
            # Add type assertion and label
            logical_statements.append(f"chebi_entity({chebi_id}, '{label}').")
        
        # Process ChEBI-specific relationships
        for relation in relationships:
            subj_text = relation["subject"]
            pred = relation["predicate"]  # ChEBI relationship type
            obj_text = relation["object"]
            
            # Get normalized IDs/labels
            subj = entity_mappings.get(subj_text, {}).get("id", f'"{subj_text}"')
            obj = entity_mappings.get(obj_text, {}).get("id", f'"{obj_text}"')
            
            # Map common ChEBI relationships
            if pred.lower() in ["is a", "is_a"]:
                logical_statements.append(f"is_a({subj}, {obj}).")
            elif pred.lower() in ["has part", "has_part"]:
                logical_statements.append(f"has_part({subj}, {obj}).")
            elif pred.lower() in ["has role", "has_role"]:
                logical_statements.append(f"has_role({subj}, {obj}).")
            else:  # Generic relationship
                pred = pred.replace(" ", "_").lower()
                logical_statements.append(f"chebi_relation({subj}, {pred}, {obj}).")
    
    return "\n".join(logical_statements)

# Example Usage:
if __name__ == "__main__":
    # Load your local ChEBI annotations
    with open("/home/matt/Proj/Hermeticav2/testing/AnnotationTesting/chebiRelAnnotations.json", "r") as f:
        chebi_annotations = json.load(f)
    
    logic_output = formulize_chebi_annotations(chebi_annotations)
    print(logic_output)