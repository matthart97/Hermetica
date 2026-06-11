import sys
import os 
import json 
import gc  # For garbage collection
import time
import numpy as np
from tqdm import tqdm  # For progress tracking
sys.path.append('/home/matt/Proj/Hermeticav2/src')
from pipeline.ChEBIPipeline import ChEBIPipeline as AnnotationCheck
from reasoning.OntoValidation.ChEBIReasoner import ChEBIReasoner, reason_with_chebi
from reasoning.LLMFeedback.Pipe2NL import extract_chebi_ids, ChEBINameRetriever, replace_chebi_ids, format_json_as_prompt
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
import pandas as pd

# Paths
BASE_PATH = '/home/matt/Proj/Hermeticav2'
OUTPUT_DIR = f"{BASE_PATH}/results"
OUTPUT_FILE = f"{OUTPUT_DIR}/MMLU_highschool_Chem_SimpleAnnotation_Highschool_LLMResponse.json"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Custom JSON encoder to handle numpy arrays and other non-serializable types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)

def Process_Text(text, llm_name, question_number):
    """Annotate and reason about text using ChEBI ontologies"""
    annotator = AnnotationCheck(f'{BASE_PATH}/notebooks/prototyping/QAReasoning/chebi.obo',
                               f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    annotations = annotator.process_text(text)
    Reasoned = reason_with_chebi(annotations, f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    
    finder = ChEBINameRetriever(f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    IDs = extract_chebi_ids(Reasoned)
    mapping = finder.get_chebi_names(IDs)
    PreNL = replace_chebi_ids(Reasoned, mapping)
    NL = format_json_as_prompt(PreNL)
    
    gc.collect()
    
    return {
        'annotated_text': NL,
        'llm_source': llm_name,
        'question_number': question_number
    }

def save_result(results, key, data):
    results[key] = data
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4, cls=NumpyEncoder)
    print(f"Updated results file after processing {key}")
    return results

def convert_to_serializable(obj):
    if isinstance(obj, (np.ndarray, pd.Series)):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj

def main():
    INPUT_JSON_FILE = "/home/matt/Proj/Hermeticav2/results/QAnnotationOnly/MMLU_highschool_Chem_Full1.json"  # Replace with actual JSON file path
    with open(INPUT_JSON_FILE, 'r') as f:
        data = json.load(f)
    
    results = {}
    
    for i, (llm_name, entry) in tqdm(enumerate(data.items()), total=len(data)):
        try:
            question_data = entry['question']
            question_text = str(question_data['text'])
            choices = convert_to_serializable(question_data['choices'])
            annotation = convert_to_serializable(entry.get('OntologyInfo', {}))
            raw_model_response = str(entry.get('raw_model_response', ''))
            onto_model_response = str(entry.get('onto_model_response', ''))
            
            print(f"Annotating response for question {i}...")
            response_annotation = Process_Text(raw_model_response, llm_name, i)
            response_annotation = convert_to_serializable(response_annotation)
            
            result_data = {
                'question': {
                    'text': question_text,
                    'choices': choices,
                },
                'OntologyInfo': annotation,
                'onto_model_response': onto_model_response,
                'raw_model_response': raw_model_response,
                'response_annotation': response_annotation
            }
            
            results = save_result(results, f'{llm_name}_{i}', result_data)
            
            del response_annotation, result_data
            gc.collect()
            
        except Exception as e:
            print(f"Error processing question {i} for model {llm_name}: {str(e)}")
    
    print(f"All processing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
