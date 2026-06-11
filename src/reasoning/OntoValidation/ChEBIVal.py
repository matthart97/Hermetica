import re
import os
from typing import List, Dict, Tuple, Optional
from owlready2 import *

class ChEBIOntologyChecker:
    """
    Checks the consistency of extracted relationships against the ChEBI ontology.
    """
    
    def __init__(self, owl_path: str):
        """
        Initialize the ontology checker with the ChEBI ontology.
        
        Args:
            owl_path: Path to the ChEBI OWL file
        """
        self.onto = self._load_ontology(owl_path)
        self.entity_cache = {}  # Cache for faster entity lookups
        
        # Map relationship types to checking functions
        self.relationship_checkers = {
            "is_a": self._check_is_a,
            "has_part": self._check_has_part,
            "is_conjugate_base_of": self._check_is_conjugate_base_of,
            "is_conjugate_acid_of": self._check_is_conjugate_acid_of,
            "is_tautomer_of": self._check_is_tautomer_of,
            "is_enantiomer_of": self._check_is_enantiomer_of,
            "has_functional_parent": self._check_has_functional_parent,
            "has_parent_hydride": self._check_has_parent_hydride,
            "is_substituent_group_from": self._check_is_substituent_group_from,
            "has_role": self._check_has_role
        }
        
        # Build a cache of all entities for faster lookups
        self._build_entity_cache()
        
    def _load_ontology(self, file_path: str):
        """Load the ChEBI ontology using owlready2."""
        try:
            # Extract directory path
            directory = os.path.dirname(file_path)
            if directory:
                onto_path.append(directory)
            
            onto = get_ontology(file_path).load()
            print(f"✅ Loaded ChEBI ontology with {len(list(onto.classes()))} classes.")
            return onto
        except Exception as e:
            print(f"Error loading ontology: {e}")
            # Create an empty ontology as fallback
            return get_ontology("http://purl.obolibrary.org/obo/chebi.owl")
    
    def _build_entity_cache(self):
        """Build a cache of entity IDs to ontology classes for faster lookups."""
        for entity in self.onto.classes():
            # Extract ChEBI ID from IRI
            iri = entity.iri
            if "CHEBI_" in iri:
                id_match = re.search(r'CHEBI_(\d+)', iri)
                if id_match:
                    chebi_id = f"CHEBI:{id_match.group(1)}"
                    self.entity_cache[chebi_id] = entity
        
        print(f"✅ Built entity cache with {len(self.entity_cache)} entries.")
    
    def _get_entity_by_id(self, chebi_id: str) -> Optional:
        """Get an entity from the ontology by its ChEBI ID."""
        # Try cache first
        if chebi_id in self.entity_cache:
            return self.entity_cache[chebi_id]
        
        # Extract numeric part and try alternative formats
        id_match = re.search(r'CHEBI:(\d+)', chebi_id)
        if id_match:
            id_number = id_match.group(1)
            
            # Try different formats
            alt_id = f"CHEBI:{id_number}"
            if alt_id in self.entity_cache:
                return self.entity_cache[alt_id]
            
            # Try searching by IRI pattern
            search_iri = f"http://purl.obolibrary.org/obo/CHEBI_{id_number}"
            for entity in self.onto.classes():
                if entity.iri == search_iri:
                    self.entity_cache[chebi_id] = entity
                    return entity
        
        return None
    
    def _check_is_a(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is a subclass of object."""
        try:
            # Direct subclass check
            if object_entity in subject_entity.is_a:
                return True, f"{subject_entity.name} is correctly classified as {object_entity.name}."
            
            # Check ancestors (indirect relationships)
            for ancestor in subject_entity.ancestors():
                if ancestor == object_entity:
                    return True, f"{subject_entity.name} is indirectly a {object_entity.name} (through inheritance)."
                    
            return False, f"{subject_entity.name} is not classified as {object_entity.name} in the ontology."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_has_part(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject has part object."""
        try:
            if hasattr(subject_entity, "has_part") and object_entity in subject_entity.has_part:
                return True, f"{subject_entity.name} correctly has part {object_entity.name}."
            
            return False, f"No 'has_part' relationship between {subject_entity.name} and {object_entity.name} found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_is_conjugate_base_of(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is conjugate base of object."""
        try:
            if hasattr(subject_entity, "is_conjugate_base_of") and object_entity in subject_entity.is_conjugate_base_of:
                return True, f"{subject_entity.name} is correctly the conjugate base of {object_entity.name}."
            
            return False, f"No 'is_conjugate_base_of' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_is_conjugate_acid_of(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is conjugate acid of object."""
        try:
            if hasattr(subject_entity, "is_conjugate_acid_of") and object_entity in subject_entity.is_conjugate_acid_of:
                return True, f"{subject_entity.name} is correctly the conjugate acid of {object_entity.name}."
            
            return False, f"No 'is_conjugate_acid_of' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_is_tautomer_of(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is tautomer of object."""
        try:
            if hasattr(subject_entity, "is_tautomer_of") and object_entity in subject_entity.is_tautomer_of:
                return True, f"{subject_entity.name} is correctly a tautomer of {object_entity.name}."
            
            return False, f"No 'is_tautomer_of' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_is_enantiomer_of(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is enantiomer of object."""
        try:
            if hasattr(subject_entity, "is_enantiomer_of") and object_entity in subject_entity.is_enantiomer_of:
                return True, f"{subject_entity.name} is correctly an enantiomer of {object_entity.name}."
            
            return False, f"No 'is_enantiomer_of' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_has_functional_parent(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject has functional parent object."""
        try:
            if hasattr(subject_entity, "has_functional_parent") and object_entity in subject_entity.has_functional_parent:
                return True, f"{subject_entity.name} correctly has functional parent {object_entity.name}."
            
            return False, f"No 'has_functional_parent' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_has_parent_hydride(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject has parent hydride object."""
        try:
            if hasattr(subject_entity, "has_parent_hydride") and object_entity in subject_entity.has_parent_hydride:
                return True, f"{subject_entity.name} correctly has parent hydride {object_entity.name}."
            
            return False, f"No 'has_parent_hydride' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_is_substituent_group_from(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject is substituent group from object."""
        try:
            if hasattr(subject_entity, "is_substituent_group_from") and object_entity in subject_entity.is_substituent_group_from:
                return True, f"{subject_entity.name} is correctly a substituent group from {object_entity.name}."
            
            return False, f"No 'is_substituent_group_from' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"
    
    def _check_has_role(self, subject_entity, object_entity) -> Tuple[bool, str]:
        """Check if subject has role object."""
        try:
            if hasattr(subject_entity, "has_role") and object_entity in subject_entity.has_role:
                return True, f"{subject_entity.name} correctly has role {object_entity.name}."
            
            return False, f"No 'has_role' relationship found."
        except Exception as e:
            return False, f"Error checking relationship: {str(e)}"

    def check_relationship(self, relationship: Dict) -> Dict:
        """
        Check if a relationship is consistent with the ChEBI ontology.
        
        Args:
            relationship: Dictionary containing subject, relationship, and object
            
        Returns:
            Dictionary with consistency check results
        """
        subject_id = relationship["subject"]["id"]
        object_id = relationship["object"]["id"]
        relationship_type = relationship["relationship"]
        
        # Get entities from the ontology
        subject_entity = self._get_entity_by_id(subject_id)
        object_entity = self._get_entity_by_id(object_id)
        
        # Check if entities were found
        if not subject_entity:
            return {
                "is_consistent": False,
                "explanation": f"Subject entity with ID {subject_id} not found in the ontology."
            }
        
        if not object_entity:
            return {
                "is_consistent": False,
                "explanation": f"Object entity with ID {object_id} not found in the ontology."
            }
        
        # Check the specific relationship type
        if relationship_type in self.relationship_checkers:
            check_func = self.relationship_checkers[relationship_type]
            is_consistent, explanation = check_func(subject_entity, object_entity)
        else:
            is_consistent = False
            explanation = f"Relationship type '{relationship_type}' is not supported for consistency checking."
        
        return {
            "is_consistent": is_consistent,
            "explanation": explanation
        }
    
    def check_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """
        Check multiple relationships for consistency with the ChEBI ontology.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            List of dictionaries with consistency check results
        """
        results = []
        
        for rel in relationships:
            check_result = self.check_relationship(rel)
            results.append({
                "relationship": rel,
                "consistency_check": check_result
            })
        
        return results

# Example usage
if __name__ == "__main__":
    # Sample relationship to check
    relationship = {
        "subject": {
            "name": "Methanol",
            "id": "CHEBI:17790"
        },
        "relationship": "has_functional_parent",
        "object": {
            "name": "Methane",
            "id": "CHEBI:16183"
        }
    }
    
    # Check consistency
    checker = ChEBIOntologyChecker("/home/matt/Proj/Hermeticav2/notebooks/prototyping/QAReasoning/chebi.obo")
    result = checker.check_relationship(relationship)
    
    print(f"Consistency check: {'Passed' if result['is_consistent'] else 'Failed'}")
    print(f"Explanation: {result['explanation']}")