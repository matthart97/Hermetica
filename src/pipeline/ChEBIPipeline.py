import json
from typing import List, Dict, Any
import os
import sys
sys.path.append('../../src')


class ChEBIPipeline:

    """
    Pipeline for extracting ChEBI entities and relationships from text 
    and checking their consistency against the ChEBI ontology.
    """
    
    def __init__(self, obo_path: str, owl_path: str):
        from ontology.Annotation.ChEBIRelationsAnn import ChEBI_NER 
        from ontology.Relations import ChEBIRelationshipExtractor 
        from reasoning.OntoValidation.ChEBIVal import ChEBIOntologyChecker
        """
        Initialize the pipeline components.
        
        Args:
            obo_path: Path to the ChEBI OBO file for entity recognition
            owl_path: Path to the ChEBI OWL file for consistency checking
        """
        print("Initializing ChEBI pipeline components...")
        self.ner = ChEBI_NER(obo_path)
        self.relationship_extractor = ChEBIRelationshipExtractor()
        self.ontology_checker = ChEBIOntologyChecker(owl_path)
        print("Pipeline initialization complete.")
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process a text through the entire pipeline.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary with extraction and validation results
        """
        # Step 1: Extract entities
        entities = self.ner.find_entities(text)
        
        # Step 2: Extract relationships
        relationships = self.relationship_extractor.extract_relationships(text, entities)
        
        # Step 3: Check consistency of relationships
        consistency_results = []
        for rel in relationships:
            result = self.ontology_checker.check_relationship(rel)
            consistency_results.append({
                "relationship": rel,
                "is_consistent": result["is_consistent"],
                "explanation": result["explanation"]
            })
        
        # Build the final result
        return {
            "text": text,
            "entities": entities,
            "relationships": relationships,
            "consistency_results": consistency_results
        }
    
    def process_to_json(self, text: str, ) -> None:
        """
        Process text and write results to a JSON file.
        
        Args:
            text: Text to process
            output_path: Path to output JSON file
        """
        result = self.process_text(text)
        
        # Ensure output directory exists
        #os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        """
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Results written to {output_path}")
        """
        # Also return a summary
        return {
            "text": result["text"],
            "entity_count": len(result["entities"]),
            "relationship_count": len(result["relationships"]),
            "consistent_count": sum(1 for r in result["consistency_results"] if r["is_consistent"])
        }


# Example usage
if __name__ == "__main__":
    # Paths to ChEBI files
    obo_path = "/home/matt/Proj/Hermeticav2/notebooks/prototyping/QAReasoning/chebi.obo"
    owl_path = "/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl"
    
    # Initialize pipeline
    pipeline = ChEBIPipeline(obo_path, owl_path)
    
    # Process test sentences
    test_sentences = [
        "Water contains hydrogen and oxygen.",
        "Lactic acid is tautomer of pyruvic acid.",
        "Acetic acid is conjugate acid of acetate.",
        "Methanol has functional parent methane.",
        "Alkylbenzene has parent hydride benzene.",
        "D-glucose is enantiomer of L-glucose.",
        "Caffeine has role psychoactive drug."
    ]
    
    # Process each sentence
    for i, sentence in enumerate(test_sentences):
        output_file = f"/home/matt/Proj/Hermeticav2/testing/Initialtestingresults/sentence_{i+1}.json"
        summary = pipeline.process_to_json(sentence, output_file)
        
        print(f"\nProcessed: \"{sentence}\"")
        print(f"Found {summary['entity_count']} entities and {summary['relationship_count']} relationships")
        print(f"Consistency: {summary['consistent_count']}/{summary['relationship_count']} relationships are consistent")
