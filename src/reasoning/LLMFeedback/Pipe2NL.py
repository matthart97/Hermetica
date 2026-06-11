"""

takes in all the informnation from the reasoner/annotator and makes it ready for the LLM 

"""


import owlready2 as owl
import re
from typing import Dict, List, Optional
import os
import json

def extract_chebi_ids(json_data):
    """
    Extracts all CHEBI IDs (CHEBI_{number} or CHEBI:{number}) from the entire JSON string
    and returns a list of unique CHEBI IDs.
    """
    chebi_pattern = re.compile(r'CHEBI[:_]\d+')
    
    # Convert JSON data to a full string representation
    json_string = json.dumps(json_data, default=str)
    
    # Find all unique CHEBI IDs
    matches = list(set(chebi_pattern.findall(json_string)))
    
    return matches

#

# Run function
"""
chebi_ids = extract_chebi_ids(results)
print(chebi_ids)
"""
"""

finding all the chebi ONtology names


"""


class ChEBINameRetriever:
    def __init__(self, ontology_path: str = None):
        """
        Initialize the ChEBI name retriever with the path to the ChEBI ontology file.
        
        Args:
            ontology_path: Path to the ChEBI OWL file. If None, will try to use a default location
                          or download the ontology.
        """
        self.entity_cache = {}
        self.label_cache = {}
        
        if ontology_path is None:
            # Try common locations or download
            default_paths = [
                "chebi.owl",
                "chebi_lite.owl", 
                os.path.expanduser("~/chebi.owl"),
                os.path.expanduser("~/ontologies/chebi.owl")
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    ontology_path = path
                    break
            
            if ontology_path is None:
                print("ChEBI ontology not found. Downloading...")
                self._download_ontology()
                ontology_path = "chebi.owl"
        
        print(f"Loading ChEBI ontology from {ontology_path}...")
        self.onto = owl.get_ontology(f"file://{ontology_path}").load()
        print("Ontology loaded.")
        
        # Pre-cache some common properties for faster access
        self._precache_labels()
    
    def _download_ontology(self):
        """Download the ChEBI ontology file if it doesn't exist."""
        import requests
        
        # Use the ChEBI Lite version which is smaller but contains the names
        url = "https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi_lite.owl"
        print(f"Downloading ChEBI ontology from {url}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open("chebi.owl", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Download complete.")
    
    def _precache_labels(self):
        """Pre-cache entity labels for faster lookups."""
        print("Pre-caching entity labels...")
        label_property = self.onto.search_one(iri="*label")
        
        count = 0
        for entity in self.onto.classes():
            if hasattr(entity, "label") and entity.label:
                self.label_cache[entity.iri] = entity.label[0]
                count += 1
        
        print(f"Cached {count} entity labels.")
    
    def _get_entity_by_id(self, chebi_id: str) -> Optional[owl.Thing]:
        """
        Get an entity from the ontology by its ChEBI ID.
        Returns None if the entity is not found.
        
        Args:
            chebi_id: ChEBI ID in various formats (CHEBI:12345, CHEBI_12345, etc.)
            
        Returns:
            The entity object or None if not found
        """
        # Try direct lookup from cache
        if chebi_id in self.entity_cache:
            return self.entity_cache[chebi_id]
        
        # Extract the numeric part of the ID
        id_match = re.search(r'(\d+)', chebi_id)
        if not id_match:
            print(f"Warning: Invalid ChEBI ID format: {chebi_id}")
            return None
            
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
        entity = self.onto.search_one(iri=search_iri)
        
        if entity is not None:
            self.entity_cache[chebi_id] = entity
            return entity
        
        # If not found by IRI, try a more exhaustive search
        chebi_prefix = f"CHEBI_{id_number}"
        for cls in self.onto.classes():
            if cls.name == chebi_prefix or (hasattr(cls, "id") and any(chebi_id in id_val for id_val in cls.id)):
                self.entity_cache[chebi_id] = cls
                return cls
        
        print(f"Warning: Could not find entity with ID {chebi_id} in the ontology.")
        return None
    
    def get_chebi_name(self, chebi_id: str) -> Optional[str]:
        """
        Get the name/label of a ChEBI entity.
        
        Args:
            chebi_id: ChEBI ID in various formats (CHEBI:12345, CHEBI_12345, etc.)
            
        Returns:
            The entity name or None if not found
        """
        entity = self._get_entity_by_id(chebi_id)
        
        if entity is None:
            return None
        
        # Try to get the name from various properties
        if hasattr(entity, "label") and entity.label:
            return str(entity.label[0])
        
        # Check if we have it in the label cache
        if entity.iri in self.label_cache:
            return self.label_cache[entity.iri]
        
        # Try other properties that might contain the name
        for prop_name in ["title", "name", "chebi_name", "ChEBI_name"]:
            if hasattr(entity, prop_name):
                prop_value = getattr(entity, prop_name)
                if prop_value and len(prop_value) > 0:
                    return str(prop_value[0])
        
        # Last resort: use the entity name from IRI
        if hasattr(entity, "name"):
            name = entity.name
            if name.startswith("CHEBI_"):
                name = name[6:]  # Remove the CHEBI_ prefix
            return name
        
        return None
    
    def get_chebi_names(self, chebi_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Get names for multiple ChEBI IDs.
        
        Args:
            chebi_ids: List of ChEBI IDs in various formats
            
        Returns:
            Dictionary mapping each input ChEBI ID to its name (or None if not found)
        """
        results = {}
        
        for chebi_id in chebi_ids:
            name = self.get_chebi_name(chebi_id)
            results[chebi_id] = name
        
        return results


# Example usage
if __name__ == "__main__":
    # Test with a list of ChEBI IDs
    test_ids = chebi_ids
    
    # Initialize the retriever (will download the ontology if needed)
    retriever = ChEBINameRetriever('/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl')
    
    # Get names for all IDs
    mapping = retriever.get_chebi_names(test_ids)
    
    # Print results
    for chebi_id, name in mapping.items():
        if name:
            print(f"{chebi_id}: {name}")
        else:
            print(f"{chebi_id}: Not found")



""" concerting the json to the real names"""



def replace_chebi_ids(obj, mapping):
    """Recursively replace all CHEBI IDs in a JSON object."""
    
    if isinstance(obj, dict):  # If obj is a dictionary, process its keys and values
        return {k: replace_chebi_ids(v, mapping) for k, v in obj.items()}
    
    elif isinstance(obj, list):  # If obj is a list, process each element
        return [replace_chebi_ids(item, mapping) for item in obj]
    
    elif isinstance(obj, str):  # If obj is a string, replace CHEBI IDs
        for chebi_id, term in mapping.items():
            chebi_id_colon = chebi_id.replace("_", ":")  # Normalize ID format
            obj = obj.replace(chebi_id, term).replace(chebi_id_colon, term)
        return obj
    
    else:
        return obj  # Return as-is for non-string values

# Example usage:
# cleaned_json = replace_chebi_ids(results, mapping)


#PreNL=  replace_chebi_ids(results, mapping)

"""
finally, convert the whole thing to a prompt

"""





def format_json_as_prompt(json_data):
    """Convert JSON data into a natural language prompt format."""
    prompt = []
    
    prompt.append(f"The original sentence analyzed is: \"{json_data['text']}\"\n")
    
    # Extract entities
    entities = [f"{e['name']} ({e['id']})" for e in json_data.get("entities", [])]
    if entities:
        prompt.append(f"The entities identified in this sentence are: {', '.join(entities)}.\n")
    
    # Extract relationships
    relationships = [f"{r['subject']['name']} {r['relationship']} {r['object']['name']}" for r in json_data.get("relationships", [])]
    if relationships:
        prompt.append(f"The relationships extracted are: {', '.join(relationships)}.\n")
    
    # Extract consistency results
    consistency = [f"{r['relationship']['subject']['name']} {r['relationship']['relationship']} {r['relationship']['object']['name']} - Consistency: {r['is_consistent']}, Explanation: {r['explanation']}" for r in json_data.get("consistency_results", [])]
    if consistency:
        prompt.append(f"Consistency checks and explanations: {' '.join(consistency)}\n")
    
    # Extract reasoning steps
    reasoning_steps = json_data.get("reasoning", {}).get("reasoning_steps", [])
    if reasoning_steps:
        prompt.append(f"The reasoning process followed these steps: {' '.join(reasoning_steps)}\n")
    
    return "\n".join(prompt)

# Example usage:
# formatted_prompt = format_json_as_prompt(your_json_data)
# print(formatted_prompt)


if __name__ == '__main__':
    finder = ChEBINameRetriever('/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl')
    with open('REASONING_OUTPUT_FILE') as f:
        _ = f.read()
        data = json.load(_)
    IDs =  extract_chebi_ids(data)
    mapping = finder(IDs)
    PreNL = replace_chebi_ids(data,mapping)
    NL = format_json_as_prompt(PreNL)
    # save the natural language output 
    



