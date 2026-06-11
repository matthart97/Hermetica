import re
import spacy
from typing import List, Dict, Optional

class ChEBIRelationshipExtractor:
    """
    Extracts relationships between ChEBI entities from text.
    Only focuses on ChEBI-defined relationship types.
    """
    
    def __init__(self):
        """Initialize the relationship extractor with spaCy model and ChEBI relationship types."""
        self.nlp = spacy.load("en_core_web_lg")
        
        # Standard ChEBI relationship types
        self.chebi_relationships = {
            "is_a",                     # Entity A is an instance of Entity B
            "has_part",                 # Relationship between a part and the whole 
            "is_conjugate_base_of",     # Relationship between conjugate bases and their acids
            "is_conjugate_acid_of",     # Relationship between conjugate acids and their bases
            "is_tautomer_of",           # Cyclic relationship between tautomers
            "is_enantiomer_of",         # Cyclic relationship between enantiomers
            "has_functional_parent",    # Relationship between derived compounds and parent compounds
            "has_parent_hydride",       # Relationship between an entity and its parent hydride
            "is_substituent_group_from", # Relationship between substituent group and parent entity
            "has_role"                  # Relationship between an entity and its role
        }
        
        # Define relationship patterns mapping to ChEBI relationship types
        self.relationship_patterns = {
            "is_a": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:an?|the)?\s*(?P<object>[\w\s-]+?)\b'
            ],
            "has_part": [
                r'\b(?P<subject>[\w\s-]+?)\s+(?:has|contains|possesses|includes)\s+(?:a|an|the)?\s*(?:part|molecule|atom)?\s*(?P<object>[\w\s-]+?)\b'
            ],
            "is_conjugate_base_of": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:a|an|the)?\s*conjugate\s+base\s+of\s+(?P<object>[\w\s-]+?)\b'
            ],
            "is_conjugate_acid_of": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:a|an|the)?\s*conjugate\s+acid\s+of\s+(?P<object>[\w\s-]+?)\b'
            ],
            "is_tautomer_of": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:a|an|the)?\s*tautomer\s+of\s+(?P<object>[\w\s-]+?)\b'
            ],
            "is_enantiomer_of": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:a|an|the)?\s*enantiomer\s+of\s+(?P<object>[\w\s-]+?)\b'
            ],
            "has_functional_parent": [
                r'\b(?P<subject>[\w\s-]+?)\s+has\s+(?:a|an|the)?\s*functional\s+parent\s+(?P<object>[\w\s-]+?)\b'
            ],
            "has_parent_hydride": [
                r'\b(?P<subject>[\w\s-]+?)\s+has\s+(?:a|an|the)?\s*parent\s+hydride\s+(?P<object>[\w\s-]+?)\b'
            ],
            "is_substituent_group_from": [
                r'\b(?P<subject>[\w\s-]+?)\s+is\s+(?:a|an|the)?\s*substituent\s+group\s+from\s+(?P<object>[\w\s-]+?)\b'
            ],
            "has_role": [
                r'\b(?P<subject>[\w\s-]+?)\s+has\s+(?:a|an|the)?\s*role\s+(?:as)?\s*(?P<object>[\w\s-]+?)\b'
            ]
        }
    
    def _find_entity_at_span(self, entities: List[Dict], start: int, end: int) -> Optional[Dict]:
        """Find entity that covers or substantially overlaps with the given span."""
        for entity in entities:
            entity_start, entity_end = entity["span"]
            # Check if entity contains span or has significant overlap
            if (entity_start <= start and entity_end >= end) or \
               (entity_start <= start < entity_end) or \
               (entity_start < end <= entity_end):
                return entity
        return None
    
    def extract_relationships(self, text: str, entities: List[Dict]) -> List[Dict]:
        """
        Extract relationships between entities that match ChEBI relationship types.
        
        Args:
            text: Original text
            entities: List of entity dictionaries from ChEBI_NER
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        text_lower = text.lower()
        
        # Extract relationships using pattern matching
        for relationship_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                
                for match in matches:
                    subject_start, subject_end = match.span("subject")
                    object_start, object_end = match.span("object")
                    
                    # Find corresponding entities
                    subject_entity = self._find_entity_at_span(entities, subject_start, subject_end)
                    object_entity = self._find_entity_at_span(entities, object_start, object_end)
                    
                    # Only create relationship if both entities are found and they're different
                    if subject_entity and object_entity and subject_entity["id"] != object_entity["id"]:
                        relationship = {
                            "subject": {
                                "name": subject_entity["name"],
                                "id": subject_entity["id"]
                            },
                            "relationship": relationship_type,
                            "object": {
                                "name": object_entity["name"],
                                "id": object_entity["id"]
                            }
                        }
                        
                        # Check if relationship already exists
                        key = (subject_entity["id"], relationship_type, object_entity["id"])
                        if all(not(r["subject"]["id"] == subject_entity["id"] and 
                                   r["relationship"] == relationship_type and 
                                   r["object"]["id"] == object_entity["id"]) for r in relationships):
                            relationships.append(relationship)
        
        return relationships

# Example usage
if __name__ == "__main__":
    # Assume ChEBI_NER has been imported and entities extracted
    extractor = ChEBIRelationshipExtractor()
    
    test_sentences = [
        "Water contains hydrogen and oxygen.",
        "Lactic acid is tautomer of pyruvic acid.",
        "Acetic acid is conjugate acid of acetate.",
        "Methanol has functional parent methane.",
        "Benzene has parent hydride cyclohexane.",
        "D-glucose is enantiomer of L-glucose.",
        "Caffeine has role psychoactive drug."
    ]
    
    # For testing, assume we have entities
    mock_entities = [
        {"name": "Water", "id": "CHEBI:15377", "span": (0, 5)},
        {"name": "Hydrogen", "id": "CHEBI:49637", "span": (15, 23)},
        {"name": "Oxygen", "id": "CHEBI:25805", "span": (28, 34)}
    ]
    
    relationships = extractor.extract_relationships(test_sentences[0], mock_entities)
    for rel in relationships:
        print(f"{rel['subject']['name']} {rel['relationship']} {rel['object']['name']}")