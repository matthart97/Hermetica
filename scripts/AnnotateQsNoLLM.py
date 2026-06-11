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
OUTPUT_FILE = f"{OUTPUT_DIR}/MMLU_highschool_Chem_SimpleAnnotation_College.json"

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

def Process_Text(text):
    """Annotate and reason about text using ChEBI ontologies"""
    # start with annotations
    annotator = AnnotationCheck(f'{BASE_PATH}/notebooks/prototyping/QAReasoning/chebi.obo',
                               f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    annotations = annotator.process_text(text)
    Reasoned = reason_with_chebi(annotations, f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    
    # convert the stuff back into NL for LLM input 
    finder = ChEBINameRetriever(f'{BASE_PATH}/data/ontologies/Chemistry/chebi.owl')
    IDs = extract_chebi_ids(Reasoned)
    mapping = finder.get_chebi_names(IDs)
    PreNL = replace_chebi_ids(Reasoned, mapping)
    NL = format_json_as_prompt(PreNL)
    
    # Force garbage collection after heavy processing
    gc.collect()
    
    return NL


def save_result(results, key, data):
    # Add new data to results
    results[key] = data
    
    # Save the entire results file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4, cls=NumpyEncoder)
    
    print(f"Updated results file after processing {key}")
    return results

# Function to convert any pandas/numpy types to Python native types
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

# Main processing function with individual saving
def main():
    # Load data
    df = pd.read_parquet(f'{BASE_PATH}/data/Raw/MMLU/mmlu/college_chemistry/test-00000-of-00001.parquet')
    # sampling for prototyping

    

    results = {}
   
    # Process each question individually
    for i in tqdm(range(len(df))):
        try:
            # Convert pandas series elements to Python native types
            question = str(df['question'][i])
            choices = convert_to_serializable(df['choices'][i])
            ans = str(df['answer'][i]) if not pd.isna(df['answer'][i]) else None
            
            # STEP 1: Process and annotate the question
            print(f"Annotating question {i}...")
            question_annotation = Process_Text(question)
            question_annotation = convert_to_serializable(question_annotation)
            
            
            
            # Create result data
            data = {
                'question': {
                    'text': question,
                    'choices': choices,
                    'answer': ans
                },
                'question_annotation': question_annotation
            }
            
            # Save immediately after each question
            results = save_result(results, f'{i}', data)
            
            # Free up memory
            del question_annotation, response_annotation, initial_msg, feedback_msg, data
            gc.collect()
            
        except Exception as e:
            print(f"Error processing question {i}: {str(e)}")
            # Continue with next question despite errors
        

print(f"All processing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
