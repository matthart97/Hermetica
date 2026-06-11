from owlready2 import *
import requests
import json

class WikidataFormulizer:
    def __init__(self, working_ontology_uri="http://example.org/wikidata.owl"):
        """
        Initialize a working ontology for Wikidata-based knowledge.
        """
        self.working_onto = get_ontology(working_ontology_uri)

        # Define OWL Classes and Properties
        with self.working_onto:
            class WikidataEntity(Thing): pass  # General class for Wikidata concepts
            class hasWikidataID(DataProperty, FunctionalProperty):
                domain = [WikidataEntity]
                range = [str]
            class hasDescription(DataProperty, FunctionalProperty):
                domain = [WikidataEntity]
                range = [str]
    
    def query_wikidata_relationships(self, wikidata_id):
        """
        Query Wikidata to find relationships for a given entity.
        """
        query = f"""
        SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {{
          wd:{wikidata_id} ?property ?value .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        url = "https://query.wikidata.org/sparql"
        headers = {"Accept": "application/sparql-results+json"}
        response = requests.get(url, params={"query": query}, headers=headers)

        if response.status_code == 200:
            results = response.json()["results"]["bindings"]
            relationships = []
            for result in results:
                property_id = result["property"]["value"].split("/")[-1]  # Extract property ID
                value_id = result["value"]["value"].split("/")[-1]  # Extract object entity ID
                property_label = result.get("propertyLabel", {}).get("value", property_id)
                value_label = result.get("valueLabel", {}).get("value", value_id)

                relationships.append({
                    "subject": wikidata_id,
                    "predicate": property_id,
                    "predicate_label": property_label,
                    "object": value_id,
                    "object_label": value_label
                })
            return relationships
        else:
            print(f"⚠️ Wikidata query failed for {wikidata_id}")
            return []

    def process_annotation(self, annotation):
        """
        Convert annotated Wikidata entities into OWL representation and extract relationships.
        """
        with self.working_onto:
            for entity in annotation["annotations"]:
                entity_name = entity["label"].replace(" ", "_")
                wikidata_id = entity["wikidata_id"]
                description = entity["description"]

                # Check if entity already exists
                existing_entity = self.working_onto.search_one(hasWikidataID=wikidata_id)
                if existing_entity:
                    print(f"✅ Entity already exists: {entity_name}")
                    continue

                # Create OWL entity
                new_entity = self.working_onto.WikidataEntity(entity_name)
                new_entity.hasWikidataID = wikidata_id
                new_entity.hasDescription = description

                print(f"➕ Added entity: {entity_name} (Wikidata ID: {wikidata_id})")

                # Query Wikidata for relationships
                relationships = self.query_wikidata_relationships(wikidata_id)

                # Store relationships in OWL
                for relation in relationships:
                    obj_entity = self.working_onto.search_one(hasWikidataID=relation["object"])
                    if not obj_entity:
                        obj_entity = self.working_onto.WikidataEntity(relation["object_label"].replace(" ", "_"))
                        obj_entity.hasWikidataID = relation["object"]
                    
                    # Create a new OWL object property dynamically
                    relation_name = relation["predicate_label"].replace(" ", "_")
                    if not hasattr(self.working_onto, relation_name):
                        with self.working_onto:
                            exec(f"class {relation_name}(ObjectProperty): pass")

                    # Assign relationship
                    exec(f"new_entity.{relation_name}.append(obj_entity)")
                    print(f"🔗 Added relationship: {entity_name} {relation_name} {obj_entity.name}")

    def save_working_ontology(self, filename="wikidata_annotations.owl"):
        """
        Overwrites the working ontology file with new data.
        """
        self.working_onto.save(file=filename, format="rdfxml")
        print(f"💾 Wikidata ontology saved as {filename}")

    def process_json_annotations(self, json_annotations):
        """
        Processes multiple Wikidata annotations and updates the OWL file.
        """
        for annotation in json_annotations:
            self.process_annotation(annotation)

        # Save final working ontology
        self.save_working_ontology()
