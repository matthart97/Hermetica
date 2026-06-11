import owlready2 as owl
import os
from typing import List, Dict, Any, Optional, Set
import json

class ChEBIReasoner:
    """
    A reasoning system that uses the ChEBI ontology to infer facts about chemical entities.
    All reasoning is derived directly from the ontology structure.
    """
    
    def __init__(self, chebi_owl_path: str):
        """
        Initialize the reasoner by loading the ChEBI ontology.
        
        Args:
            chebi_owl_path: Path to the ChEBI OWL file
        """
        self.onto = self._load_ontology(chebi_owl_path)
        self.entity_cache = {}
        self._build_entity_cache()
    
    def _load_ontology(self, file_path: str):
        """Load the ChEBI ontology using owlready2."""
        try:
            # Extract directory path
            directory = os.path.dirname(file_path)
            if directory:
                owl.onto_path.append(directory)
            
            # Make sure we're using the OWL file, not OBO
            if file_path.endswith('.obo'):
                print("Warning: OBO file format provided. ChEBI reasoning requires OWL format.")
                # Try to find an OWL file in the same directory
                owl_path = file_path.replace('.obo', '.owl')
                if os.path.exists(owl_path):
                    file_path = owl_path
                    print(f"Found OWL file at {owl_path}, using that instead.")
            
            onto = owl.get_ontology(file_path).load()
            print(f"✅ Successfully loaded ChEBI ontology with {len(list(onto.classes()))} classes.")
            return onto
        except Exception as e:
            print(f"Error loading ontology: {e}")
            raise ValueError(f"Failed to load the ChEBI ontology: {e}")
    
    def _build_entity_cache(self):
        """Build a cache of entity IDs to ontology classes for faster lookups."""
        import re
        
        # Track how many entities are successfully mapped
        found_count = 0
        
        for entity in self.onto.classes():
            # Extract ChEBI ID from IRI
            iri = entity.iri
            if "CHEBI_" in iri:
                id_match = re.search(r'CHEBI_(\d+)', iri)
                if id_match:
                    chebi_id = f"CHEBI:{id_match.group(1)}"
                    self.entity_cache[chebi_id] = entity
                    found_count += 1
            
            # Also check annotations that might have ChEBI IDs
            if hasattr(entity, "hasDbXref"):
                for xref in entity.hasDbXref:
                    if isinstance(xref, str) and xref.startswith("CHEBI:"):
                        self.entity_cache[xref] = entity
                        found_count += 1
        
        print(f"✅ Built entity cache with {found_count} mapped ChEBI IDs.")
    
    def _get_entity_by_id(self, chebi_id: str) -> Optional[owl.Thing]:
        """
        Get an entity from the ontology by its ChEBI ID.
        Returns None if the entity is not found.
        """
        # Try direct lookup from cache
        if chebi_id in self.entity_cache:
            return self.entity_cache[chebi_id]
        
        # Try alternative ID formats
        import re
        id_match = re.search(r'CHEBI:(\d+)', chebi_id)
        if id_match:
            id_number = id_match.group(1)
            
            # Try different ID formats
            alt_formats = [
                f"CHEBI:{id_number}",
                f"http://purl.obolibrary.org/obo/CHEBI_{id_number}"
            ]
            
            for alt_id in alt_formats:
                if alt_id in self.entity_cache:
                    return self.entity_cache[alt_id]
            
            # Search by IRI pattern
            search_iri = f"http://purl.obolibrary.org/obo/CHEBI_{id_number}"
            for entity in self.onto.classes():
                if entity.iri == search_iri:
                    self.entity_cache[chebi_id] = entity
                    return entity
        
        print(f"Warning: Could not find entity with ID {chebi_id} in the ontology.")
        return None
    
    def reason(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply ontology-based reasoning to the input data.
        
        Args:
            input_data: Dictionary containing text, entities, relationships, and consistency_results
            
        Returns:
            Dictionary with reasoning results derived from the ontology
        """
        try:
            # Extract components
            text = input_data["text"]
            entities = input_data["entities"]
            relationships = input_data["relationships"]
            consistency_results = input_data["consistency_results"]
            
            # Track all inferred facts
            all_facts = []
            reasoning_steps = []
            
            # Process each entity
            entity_facts = {}
            for entity in entities:
                entity_id = entity["id"]
                entity_name = entity["name"]
                
                # Get facts about this entity from the ontology
                entity_reasoning = self._reason_about_entity(entity_id, entity_name)
                
                if entity_reasoning:
                    entity_facts[entity_id] = entity_reasoning
                    all_facts.extend(entity_reasoning.get("facts", []))
                    reasoning_steps.extend(entity_reasoning.get("steps", []))
            
            # Process relationships
            relationship_facts = self._reason_about_relationships(relationships, consistency_results)
            if relationship_facts:
                all_facts.extend(relationship_facts.get("facts", []))
                reasoning_steps.extend(relationship_facts.get("steps", []))
            
            # Generate overall explanation
            explanation = self._generate_explanation(text, entities, relationships, 
                                                   consistency_results, entity_facts)
            
            return {
                "reasoning_steps": reasoning_steps,
                "all_facts": all_facts,
                "entity_facts": entity_facts,
                "relationship_facts": relationship_facts,
                "explanation": explanation
            }
        except Exception as e:
            print(f"Error during reasoning: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "reasoning_steps": ["Error occurred during reasoning"],
                "all_facts": [],
                "explanation": f"Could not complete reasoning: {str(e)}"
            }
    
    def _reason_about_entity(self, entity_id: str, entity_name: str) -> Dict:
        """
        Extract facts about an entity directly from the ontology.
        All facts are derived purely from the ontology with no hardcoded knowledge.
        
        Args:
            entity_id: ChEBI ID of the entity
            entity_name: Name of the entity
            
        Returns:
            Dictionary with facts and reasoning steps about the entity
        """
        steps = []
        facts = []
        
        steps.append(f"Looking up {entity_name} ({entity_id}) in the ChEBI ontology")
        
        # Get entity from ontology
        entity_obj = self._get_entity_by_id(entity_id)
        if not entity_obj:
            steps.append(f"  - Could not find {entity_name} in the ontology")
            return {"steps": steps, "facts": facts}
        
        steps.append(f"  - Found entity in the ontology: {entity_obj.name}")
        
        # Get parent classes
        steps.append(f"  - Looking for parent classes of {entity_name}")
        if hasattr(entity_obj, "is_a") and entity_obj.is_a:
            parent_classes = []
            for parent in entity_obj.is_a:
                if hasattr(parent, "name") and parent.name:
                    parent_classes.append(parent.name)
                    fact = f"{entity_name} is a {parent.name}"
                    facts.append(fact)
            
            if parent_classes:
                steps.append(f"    - Found parent classes: {', '.join(parent_classes)}")
            else:
                steps.append(f"    - No named parent classes found")
        else:
            steps.append(f"    - No parent classes found")
        
        # Get properties from annotations
        steps.append(f"  - Looking for properties of {entity_name} in annotations")
        properties = self._get_entity_annotations(entity_obj)
        if properties:
            steps.append(f"    - Found properties in annotations:")
            for prop_name, prop_value in properties.items():
                if isinstance(prop_value, list):
                    for val in prop_value:
                        if val and str(val).strip():
                            fact = f"{entity_name} has {prop_name}: {val}"
                            steps.append(f"      - {fact}")
                            facts.append(fact)
                elif prop_value and str(prop_value).strip():
                    fact = f"{entity_name} has {prop_name}: {prop_value}"
                    steps.append(f"      - {fact}")
                    facts.append(fact)
        else:
            steps.append(f"    - No properties found in annotations")
        
        # Get relationships from object properties
        steps.append(f"  - Looking for relationships of {entity_name}")
        relations = self._get_entity_relationships(entity_obj)
        if relations:
            steps.append(f"    - Found relationships:")
            for rel_type, rel_targets in relations.items():
                for target in rel_targets:
                    fact = f"{entity_name} {rel_type} {target}"
                    steps.append(f"      - {fact}")
                    facts.append(fact)
        else:
            steps.append(f"    - No relationships found")
        
        return {
            "steps": steps,
            "facts": facts,
            "parent_classes": parent_classes if 'parent_classes' in locals() else [],
            "properties": properties,
            "relationships": relations if 'relations' in locals() else {}
        }
    
    def _get_entity_annotations(self, entity) -> Dict:
        """
        Extract all annotation properties from an entity in the ontology.
        
        Args:
            entity: Entity object from the ontology
            
        Returns:
            Dictionary mapping property names to values
        """
        properties = {}
        
        # Check all attributes of the entity for annotation properties
        for attr_name in dir(entity):
            # Skip private attributes and methods
            if attr_name.startswith('_') or callable(getattr(entity, attr_name)):
                continue
            
            # Get attribute value
            attr_value = getattr(entity, attr_name)
            
            # Skip empty values and specific attributes
            if attr_value is None or attr_name in ('storid', 'namespace', 'is_a'):
                continue
            
            # Store the property
            properties[attr_name] = attr_value
        
        return properties
    
    def _get_entity_relationships(self, entity) -> Dict[str, List[str]]:
        """
        Extract all object property relationships from an entity.
        
        Args:
            entity: Entity object from the ontology
            
        Returns:
            Dictionary mapping relationship types to lists of target entity names
        """
        relationships = {}
        
        # Get all object properties from the ontology
        object_properties = list(self.onto.object_properties())
        
        # Check each object property
        for prop in object_properties:
            if hasattr(entity, prop.name):
                prop_values = getattr(entity, prop.name)
                if prop_values:
                    # Convert to list if it's not already
                    if not isinstance(prop_values, list):
                        prop_values = [prop_values]
                    
                    # Get names of target entities
                    targets = []
                    for value in prop_values:
                        if hasattr(value, 'name') and value.name:
                            targets.append(value.name)
                    
                    if targets:
                        relationships[prop.name] = targets
        
        return relationships
    
    def _reason_about_relationships(self, relationships, consistency_results) -> Dict:
        """
        Analyze the relationships between entities using the ontology.
        
        Args:
            relationships: List of relationship dictionaries
            consistency_results: Results from consistency checking
            
        Returns:
            Dictionary with facts and reasoning steps about relationships
        """
        steps = []
        facts = []
        
        # Get verified (consistent) relationships
        verified_relationships = []
        consistency_map = {}
        
        for result in consistency_results:
            rel = result["relationship"]
            key = (rel["subject"]["id"], rel["relationship"], rel["object"]["id"])
            consistency_map[key] = result["is_consistent"]
        
        for rel in relationships:
            key = (rel["subject"]["id"], rel["relationship"], rel["object"]["id"])
            if key in consistency_map and consistency_map[key]:
                verified_relationships.append(rel)
        
        # Process each verified relationship
        for rel in verified_relationships:
            subject_id = rel["subject"]["id"]
            subject_name = rel["subject"]["name"]
            relationship_type = rel["relationship"]
            object_id = rel["object"]["id"]
            object_name = rel["object"]["name"]
            
            steps.append(f"Analyzing relationship: {subject_name} {relationship_type} {object_name}")
            
            # Basic fact
            readable_rel = relationship_type.replace('_', ' ')
            fact = f"{subject_name} {readable_rel} {object_name}"
            facts.append(fact)
            
            # Look up relationship in ontology for potential implications
            subject_entity = self._get_entity_by_id(subject_id)
            object_entity = self._get_entity_by_id(object_id)
            
            if subject_entity and object_entity:
                # Use the ontology to find the meaning of this relationship
                relationship_meaning = self._get_relationship_meaning(relationship_type)
                if relationship_meaning:
                    steps.append(f"  - This relationship means: {relationship_meaning}")
                    facts.append(f"A {relationship_type} relationship means: {relationship_meaning}")
                
                # Find potential inferences based on this relationship
                inferences = self._infer_from_relationship(subject_entity, relationship_type, object_entity)
                if inferences:
                    steps.append(f"  - Inferences based on this relationship:")
                    for inference in inferences:
                        steps.append(f"    - {inference}")
                        facts.append(inference)
        
        return {
            "steps": steps,
            "facts": facts
        }
    
    def _get_relationship_meaning(self, relationship_type: str) -> Optional[str]:
        """
        Find the meaning of a relationship type in the ontology.
        
        Args:
            relationship_type: Type of relationship
            
        Returns:
            Description of the relationship if found
        """
        # Find the object property in the ontology
        for prop in self.onto.object_properties():
            if prop.name == relationship_type:
                # Check for description or definition annotations
                for annotation_prop in ["definition", "description", "comment"]:
                    if hasattr(prop, annotation_prop):
                        value = getattr(prop, annotation_prop)
                        if value:
                            return str(value)
        
        return None
    
    def _infer_from_relationship(self, subject, relationship_type, object_entity) -> List[str]:
        """
        Make inferences based on a specific relationship between entities.
        
        Args:
            subject: Subject entity from the ontology
            relationship_type: Type of relationship
            object_entity: Object entity from the ontology
            
        Returns:
            List of inferred facts
        """
        inferences = []
        
        # Get names for readability
        subject_name = subject.name
        object_name = object_entity.name
        
        # Different inference strategies based on relationship type
        if relationship_type == "has_parent_hydride":
            # If A has_parent_hydride B, then A is likely a derivative of B
            inferences.append(f"{subject_name} is a derivative of {object_name}")
            
            # Check if subject has functional groups that object doesn't have
            subject_parts = set()
            if hasattr(subject, "has_part"):
                subject_parts = {p.name for p in subject.has_part if hasattr(p, "name")}
            
            object_parts = set()
            if hasattr(object_entity, "has_part"):
                object_parts = {p.name for p in object_entity.has_part if hasattr(p, "name")}
            
            different_parts = subject_parts - object_parts
            if different_parts:
                inferences.append(f"{subject_name} contains parts not found in {object_name}: {', '.join(different_parts)}")
        
        elif relationship_type == "has_functional_parent":
            # If A has_functional_parent B, then A is structurally derived from B
            inferences.append(f"{subject_name} is structurally derived from {object_name}")
        
        return inferences
    
    def _generate_explanation(self, text, entities, relationships, consistency_results, entity_facts) -> str:
        """
        Generate a comprehensive explanation based on the reasoning.
        
        Args:
            text: Original text
            entities: Extracted entities
            relationships: Extracted relationships
            consistency_results: Results from consistency checking
            entity_facts: Facts about entities
            
        Returns:
            String with comprehensive explanation
        """
        all_consistent = all(result["is_consistent"] for result in consistency_results)
        
        # Introduction
        if all_consistent:
            explanation = f"The statement '{text}' is consistent with the ChEBI ontology.\n\n"
        else:
            explanation = f"The statement '{text}' contains some inconsistencies with the ChEBI ontology.\n\n"
        
        # Entity information
        explanation += "Entities found in the statement:\n"
        for entity in entities:
            explanation += f"- {entity['name']} ({entity['id']})\n"
        explanation += "\n"
        
        # Relationship information
        explanation += "Relationships found in the statement:\n"
        for rel in relationships:
            # Check if it's consistent
            is_consistent = False
            for result in consistency_results:
                r = result["relationship"]
                if (r["subject"]["id"] == rel["subject"]["id"] and 
                    r["relationship"] == rel["relationship"] and 
                    r["object"]["id"] == rel["object"]["id"]):
                    is_consistent = result["is_consistent"]
                    break
            
            # Mark consistent/inconsistent
            mark = "✓" if is_consistent else "✗"
            rel_text = rel["relationship"].replace('_', ' ')
            explanation += f"{mark} {rel['subject']['name']} {rel_text} {rel['object']['name']}\n"
        explanation += "\n"
        
        # Entity facts from the ontology
        explanation += "Facts derived from the ChEBI ontology:\n"
        
        if not entity_facts:
            explanation += "- No facts could be derived from the ontology\n\n"
        else:
            # Add facts for each entity
            for entity_id, facts in entity_facts.items():
                entity_name = next((e["name"] for e in entities if e["id"] == entity_id), entity_id)
                
                # Parent classes/classifications
                if "parent_classes" in facts and facts["parent_classes"]:
                    explanation += f"\nClassification of {entity_name}:\n"
                    for parent in facts["parent_classes"]:
                        explanation += f"- {entity_name} is a {parent}\n"
                
                # Properties
                if "properties" in facts and facts["properties"]:
                    explanation += f"\nProperties of {entity_name}:\n"
                    for prop_name, values in facts["properties"].items():
                        if isinstance(values, list):
                            for value in values:
                                if value and str(value).strip():
                                    explanation += f"- {prop_name}: {value}\n"
                        elif values and str(values).strip():
                            explanation += f"- {prop_name}: {values}\n"
                
                # Relationships
                if "relationships" in facts and facts["relationships"]:
                    explanation += f"\nRelationships of {entity_name} from ontology:\n"
                    for rel_type, targets in facts["relationships"].items():
                        readable_rel = rel_type.replace('_', ' ')
                        for target in targets:
                            explanation += f"- {entity_name} {readable_rel} {target}\n"
        
        return explanation


def reason_with_chebi(input_data, chebi_owl_path):
    """
    Process input data with ChEBI reasoning.
    
    Args:
        input_data: Pipeline output with entities, relationships and consistency results
        chebi_owl_path: Path to ChEBI OWL file
    
    Returns:
        Dictionary with reasoning results
    """
    try:
        # Initialize reasoner with ChEBI ontology
        reasoner = ChEBIReasoner(chebi_owl_path)
        
        # Apply reasoning
        reasoning_results = reasoner.reason(input_data)
        
        # Return enhanced results
        return {
            **input_data,  # Original input
            "reasoning": reasoning_results
        }
    except Exception as e:
        print(f"Error in reasoning: {e}")
        import traceback
        traceback.print_exc()
        return {
            **input_data,  # Original input
            "reasoning": {
                "error": str(e),
                "explanation": "Error occurred during reasoning"
            }
        }
    

#example


#data = 
"""

dummyData = {
  "text": "Methanol has functional parent methane and contains a hydroxyl group that gives it alcohol properties.",
  "entities": [
    {
      "name": "Methanol",
      "id": "CHEBI:17790",
      "span": [0, 8]
    },
    {
      "name": "Methane",
      "id": "CHEBI:16183",
      "span": [31, 38]
    },
    {
      "name": "Hydroxyl group",
      "id": "CHEBI:29191",
      "span": [53, 67]
    },
    {
      "name": "Alcohol",
      "id": "CHEBI:30879",
      "span": [82, 89]
    }
  ],
  "relationships": [
    {
      "subject": {
        "name": "Methanol",
        "id": "CHEBI:17790"
      },
      "relationship": "has_functional_parent",
      "object": {
        "name": "Methane",
        "id": "CHEBI:16183"
      }
    },
    {
      "subject": {
        "name": "Methanol",
        "id": "CHEBI:17790"
      },
      "relationship": "has_part",
      "object": {
        "name": "Hydroxyl group",
        "id": "CHEBI:29191"
      }
    },
    {
      "subject": {
        "name": "Methanol",
        "id": "CHEBI:17790"
      },
      "relationship": "is_a",
      "object": {
        "name": "Alcohol",
        "id": "CHEBI:30879"
      }
    }
  ],
  "consistency_results": [
    {
      "relationship": {
        "subject": {
          "name": "Methanol",
          "id": "CHEBI:17790"
        },
        "relationship": "has_functional_parent",
        "object": {
          "name": "Methane",
          "id": "CHEBI:16183"
        }
      },
      "is_consistent": 'true',
      "explanation": "Methanol correctly has functional parent methane according to the ChEBI ontology."
    },
    {
      "relationship": {
        "subject": {
          "name": "Methanol",
          "id": "CHEBI:17790"
        },
        "relationship": "has_part",
        "object": {
          "name": "Hydroxyl group",
          "id": "CHEBI:29191"
        }
      },
      "is_consistent": 'true',
      "explanation": "Methanol correctly contains hydroxyl group according to the ChEBI ontology."
    },
    {
      "relationship": {
        "subject": {
          "name": "Methanol",
          "id": "CHEBI:17790"
        },
        "relationship": "is_a",
        "object": {
          "name": "Alcohol",
          "id": "CHEBI:30879"
        }
      },
      "is_consistent": 'true',
      "explanation": "Methanol is correctly classified as an alcohol according to the ChEBI ontology."
    }
  ]
}



"""

 


"""

for testing and example useage

"""



"""
#take in the output form the annotator

with open('/home/matt/Proj/Hermeticav2/testing/Initialtestingresults/sentence_1.json') as f:
    _ = f.read()
    data = json.load(_)

results = reason_with_chebi(data,'/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl')
json.dump(results)
"""