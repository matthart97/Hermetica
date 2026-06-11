import re
import spacy
from typing import List, Dict, Set
import string

class ChEBI_NER:
    def __init__(self, obo_path: str):
        """
        Initializes the ChEBI Named Entity Recognizer by loading the full ontology.

        :param obo_path: Path to the ChEBI OBO ontology file.
        """
        # Common verbs to exclude even if they appear in ChEBI
        self.excluded_terms = {
            "is", "are", "was", "were", "be", "being", "been",
            "has", "have", "had", "having",
            "do", "does", "did", "doing",
            "can", "could", "may", "might", "must", "should", "would"
        }
        
        self.entity_map = self.load_chebi_ontology(obo_path)
        self.nlp = spacy.load("en_core_web_lg")

    def load_chebi_ontology(self, file_path: str) -> Dict:
        """
        Parses the ChEBI OBO file and extracts entity names with their ChEBI IDs.
        - Normalizes entity names for case-insensitive matching.
        - Handles alternative naming variations.
        - Excludes common verbs like "is" and "has"

        :param file_path: Path to the ChEBI OBO file.
        :return: Dictionary mapping entity names to ChEBI IDs.
        """
        entity_map = {}
        current_term = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if line == "[Term]":
                    if "id" in current_term and "name" in current_term:
                        term_id = current_term["id"]
                        term_name = current_term["name"].lower()

                        # Skip common verbs and auxiliary words
                        if term_name not in self.excluded_terms:
                            # Store the main name
                            entity_map[term_name] = term_id

                            # Store alternative variations (remove "atom", etc.)
                            simplified_name = re.sub(r'\s+atom$', '', term_name)
                            if simplified_name not in self.excluded_terms:
                                entity_map[simplified_name] = term_id
                    
                    current_term = {}

                elif line.startswith("id: CHEBI:"):
                    current_term["id"] = line.split(": ")[1].strip()

                elif line.startswith("name:"):
                    current_term["name"] = line.split(": ", 1)[1].strip()
                    
                elif line.startswith("synonym:"):
                    # Extract synonym from the line
                    synonym_match = re.search(r'"([^"]+)"', line)
                    if synonym_match:
                        synonym = synonym_match.group(1).lower()
                        if synonym not in self.excluded_terms:
                            entity_map[synonym] = current_term.get("id", "")

        print(f"✅ Loaded ChEBI ontology: {len(entity_map)} entities extracted.")
        return entity_map

    def find_entities(self, text: str) -> List[Dict]:
        """
        Identifies ChEBI entities in a given text and maps them to their ChEBI IDs.
        Excludes common verb forms like "is" and "has" that may be in ChEBI.

        :param text: Input sentence.
        :return: List of detected entities with their ChEBI IDs.
        """
        detected_entities = []
        text_lower = text.lower()
        
        # Process text through spaCy for POS tagging
        doc = self.nlp(text)
        verb_tokens = [token for token in doc if token.pos_ == "VERB" or token.pos_ == "AUX"]
        verb_spans = [(token.idx, token.idx + len(token.text)) for token in verb_tokens]
        
        # Look for matches, prioritizing longer terms
        for term, term_id in sorted(self.entity_map.items(), key=lambda x: len(x[0]), reverse=True):
            for match in re.finditer(rf'\b{re.escape(term)}\b', text_lower):
                start, end = match.span()
                
                # Skip if overlap with a verb
                is_verb = False
                for v_start, v_end in verb_spans:
                    if (start <= v_start and end > v_start) or (start < v_end and end >= v_end):
                        is_verb = True
                        break
                
                if is_verb:
                    continue
                
                # Get original text
                original_text = text[start:end]
                if original_text.islower():
                    original_text = original_text.capitalize()
                
                detected_entities.append({
                    "name": original_text,
                    "id": term_id,
                    "span": (start, end)
                })
                
                # Once we find a match, break to avoid overlapping entities
                # This prioritizes longer matches due to the sorting
                break
        
        # Filter overlapping entities, keeping longest ones
        detected_entities.sort(key=lambda x: (x["span"][0], -(x["span"][1] - x["span"][0])))
        
        non_overlapping = []
        last_end = -1
        
        for entity in detected_entities:
            start, end = entity["span"]
            if start >= last_end:
                non_overlapping.append(entity)
                last_end = end
        
        return non_overlapping

# Example Usage
if __name__ == "__main__":
    obo_path = "/home/matt/Proj/Hermeticav2/notebooks/prototyping/QAReasoning/chebi.obo"  # Replace with actual path
    ner = ChEBI_NER(obo_path)

    test_sentences = [
        "Water contains hydrogen and oxygen.",
        "Lactic acid is tautomer of pyruvic acid.",
        "Acetic acid is conjugate acid of acetate.",
        "Methanol has functional parent methane.",
        "Benzene has parent hydride cyclohexane.",
        "D-glucose is enantiomer of L-glucose.",
        "Caffeine has role psychoactive drug."
    ]

    for sentence in test_sentences:
        print("\n==============================")
        print(f"🔬 Processing: \"{sentence}\"")
        entities = ner.find_entities(sentence)
        for entity in entities:
            print(f"  - {entity['name']} ({entity['id']}) at position {entity['span']}")