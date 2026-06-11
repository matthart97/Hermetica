import json

def formulize_wikidata_annotation(annotation):
    """
    Converts a single Wikidata annotation result into logical statements
    and writes them to a JSON file.
    """
    logical_statements = {"entities": [], "relationships": []}
    
    sentence = annotation["original_sentence"]
    entities = annotation["annotations"]
    relationships = annotation["relationships"]
    sentence = annotation['original_sentence']
    logical_statements['original_sentence'] = sentence
    entity_mappings = {}

    # Process entities
    for entity in entities:
        qid = entity["wikidata_id"]
        label = entity["label"].replace(" ", "_")  # Logical format
        entity_mappings[entity["entity"].lower()] = qid  # Store mapping (case-insensitive)
        
        logical_statements["entities"].append({
            "qid": qid,
            "label": label
        })

    # Process relationships
    for relation in relationships:
        subject_text = relation["subject"].lower()
        predicate = relation["property_id"]  # Wikidata property
        object_text = relation["object"].lower()
        
        # Convert subject and object to QID if found in entity mappings
        subject_qid = entity_mappings.get(subject_text, subject_text)
        object_qid = entity_mappings.get(object_text, object_text)
        
        logical_statements["relationships"].append({
            "subject": subject_qid,
            "predicate": predicate,
            "object": object_qid
        })

    return logical_statements


