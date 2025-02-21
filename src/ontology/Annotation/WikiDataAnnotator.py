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

def search_wikidata(entity):
    """Search Wikidata for an entity and return the best match based on relevance."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "search": entity
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

def annotate_text(text):
    """Annotate text with Wikidata concepts using general relevance filtering."""
    entities = extract_entities(text)
    
    annotations = []
    for entity in entities:
        result = search_wikidata(entity)
        if result and result["relevance_score"] > 0.7:  # Set a threshold for filtering
            annotations.append(result)

    output = {
        "original_sentence": text,
        "annotations": annotations
    }

    return json.dumps(output, indent=4)  # Convert to JSON format

# Example Usage
if __name__ == "__main__":
    sentence = "Sigmund Freud"
    json_output = annotate_text(sentence)
    print(json_output)
