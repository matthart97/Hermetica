import spacy
import requests
import re
import json
from difflib import SequenceMatcher

# Load spaCy's English model
nlp = spacy.load("en_core_web_lg")

def string_similarity(a, b):
    """Compute string similarity score using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_wikidata(entity, entity_type="item"):
    """Search Wikidata for an entity/property and return the best match."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "search": entity,
        "type": entity_type  # Search for "item" (entity) or "property"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "search" in data and data["search"]:
            best_match = None
            highest_score = 0.0
            
            for result in data["search"]:
                label = result.get("label", "")
                description = result.get("description", "")
                wikidata_id = result["id"]

                # Compute similarity score
                similarity = string_similarity(entity, label)

                # Final score
                final_score = similarity
                
                if final_score > highest_score:
                    highest_score = final_score
                    best_match = {
                        "entity": entity,
                        "wikidata_id": wikidata_id,
                        "label": label,
                        "description": description,
                        "wikidata_url": f"https://www.wikidata.org/wiki/{wikidata_id}",
                        "relevance_score": round(final_score, 3)
                    }
            
            return best_match  # Return only the best match
    return None

def clean_entity(entity):
    """Clean entity by removing stop words and special characters."""
    entity = entity.lower().strip()
    entity = re.sub(r'[^\w\s]', '', entity)  # Remove punctuation
    return entity

def extract_entities(text):
    """Extract entities using both NER and keyword extraction."""
    doc = nlp(text)
    entities = set(ent.text for ent in doc.ents)  # Extract named entities
    
    # Extract additional keywords (noun chunks)
    for chunk in doc.noun_chunks:
        clean_chunk = clean_entity(chunk.text)
        if clean_chunk and len(clean_chunk) > 2:  # Avoid short words
            entities.add(chunk.text)

    return list(entities)

def extract_relationships(doc):
    """Extract subject-predicate-object triples using dependency parsing."""
    relationships = []
    for token in doc:
        if token.pos_ == "VERB":
            subj = None
            obj = None
            # Find subject (nsubj or nsubjpass)
            subj_tokens = [child for child in token.children if child.dep_ in ("nsubj", "nsubjpass")]
            if subj_tokens:
                subj = ' '.join([t.text for t in subj_tokens[0].subtree])
            
            # Find object (dobj, attr, or prepositional object)
            obj_tokens = [child for child in token.children if child.dep_ in ("dobj", "attr", "prep")]
            if obj_tokens:
                obj = ' '.join([t.text for t in obj_tokens[0].subtree])
            
            if subj and obj:
                relationships.append({
                    "subject": subj,
                    "predicate": token.lemma_,  # Use lemma (e.g., "found" instead of "founded")
                    "object": obj
                })
    return relationships

def annotate_text(text):
    """Annotate text with entities and relationships."""
    doc = nlp(text)
    entities = extract_entities(text)
    
    # Annotate entities
    annotations = []
    for entity in entities:
        result = search_wikidata(entity)
        if result and result["relevance_score"] > 0.7:
            annotations.append(result)
    
    # Extract and annotate relationships
    relationships = []
    for rel in extract_relationships(doc):
        # Search for the predicate as a Wikidata property
        predicate_property = search_wikidata(rel["predicate"], entity_type="property")
        if predicate_property and predicate_property["relevance_score"] > 0.5:
            relationships.append({
                "subject": rel["subject"],
                "predicate": rel["predicate"],
                "object": rel["object"],
                "property_id": predicate_property["wikidata_id"],
                "property_label": predicate_property["label"]
            })
    
    output = {
        "original_sentence": text,
        "annotations": annotations,
        "relationships": relationships
    }
    return json.dumps(output, indent=4)

# Example Usage
if __name__ == "__main__":
    sentence = "Einstien developed the theory of relativity"
    json_output = annotate_text(sentence)
    print(json_output)