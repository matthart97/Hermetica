import sys
import os 
import json 
import gc  # For garbage collection
import time
import numpy as np
from tqdm import tqdm  # For progress tracking
sys.path.append('../../src')
from pipeline.ChEBIPipeline import ChEBIPipeline as AnnotationCheck
from reasoning.OntoValidation.ChEBIReasoner import ChEBIReasoner, reason_with_chebi
from reasoning.LLMFeedback.Pipe2NL import extract_chebi_ids, ChEBINameRetriever, replace_chebi_ids, format_json_as_prompt
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
import pandas as pd

# Paths
BASE_PATH = '/home/matt/Proj/Hermeticav2'
OUTPUT_DIR = f"{BASE_PATH}/results/QAnnotationOnly"
OUTPUT_FILE = f"{OUTPUT_DIR}/MMLU_highschool_Chem.json"

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

# Define your customized prompts
Ontotemplate = """You are a neuro-symbolic system being tested on your knowledge of chemistry. You are tasked with answering a multiple choice chemistry question.
The Question has been annotated in natural language.
Use the annotation and reasoning information to aid your response to the question. Ignore errors in the annotation and reasoning information. It's your job to fill in the Final Answer.
The annotation and reasoning information is surrounded by tags, beginning with <Ontology_Information> and ending with <Ontology_Information>
You are given a set of possible answers to choose from.


The question is: {question}
The annotation and reasoning information is:<Ontology_Information>{ChEBI_Info}<Ontology_Information>

The possible answers are: {choices}

Think about through your response using the ontology information, then respond with Final Answer:"""

SimpleTemplate = """
You are given a multiple choice question and a set of possible answers. Make sure you respond ONLY with the correct answer.

The question is {question}

The possible responses are {choices}

Final Answer:

"""

custom_prompt = ChatPromptTemplate.from_template(Ontotemplate)
custom_dummy = ChatPromptTemplate.from_template(SimpleTemplate)

# Function to load existing results if available
def load_existing_results():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading existing results file. Starting fresh.")
    return {}

# Function to save results after each individual question
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
    firstdf = pd.read_parquet(f'{BASE_PATH}/data/Raw/MMLU/mmlu/high_school_chemistry/test-00000-of-00001.parquet')
    # sampling for prototyping
    df = firstdf.sample(n=30,random_state=42)
    df = df.reset_index()


    llm_list = ['llama2', 'llama3.1', 'llama3.2','phi4', 'deepseek-r1:14b'] #'phi', 'phi3', 'phi3.5', 'phi4', 'deepseek-r1:14b']
    
    # Load or initialize results
    results = load_existing_results()
    
    # Process each model and question
    for model in llm_list:
        print(f"Processing model: {model}")
        llm = Ollama(model=model)
        
        # Check which questions have already been processed for this model
        processed_indices = set()
        for key in results.keys():
            if key.startswith(f"{model}_"):
                try:
                    idx = int(key.split('_')[1])
                    processed_indices.add(idx)
                except (ValueError, IndexError):
                    pass
        
        # Process each question individually
        for i in tqdm(range(len(df))):
            if i in processed_indices:
                print(f"Skipping already processed question {i} for model {model}")
                continue
                
            try:
                # Convert pandas series elements to Python native types
                question = str(df['question'][i])
                choices = convert_to_serializable(df['choices'][i])
                ans = str(df['answer'][i]) if not pd.isna(df['answer'][i]) else None
                
                # Process text and get responses
                info = Process_Text(question)
                
                # Make sure info is JSON serializable
                info = convert_to_serializable(info)
                
                dummyPrompt = custom_dummy.invoke({'question': question, 'choices': choices})
                Rawresponse = llm.invoke(dummyPrompt.messages[0].content)
                
                prompt = custom_prompt.invoke({'question': question, 'ChEBI_Info': info, 'choices': choices})
                LLM_response = llm.invoke(prompt.messages[0].content)
                
                # Create result data
                data = {
                    'question': {
                        'text': question,
                        'choices': choices,
                        'answer': ans
                    },
                    'OntologyInfo': info,
                    'onto_model_response': LLM_response,
                    'raw_model_response': Rawresponse
                }
                
                # Save immediately after each question
                results = save_result(results, f'{model}_{i}', data)
                
                # Free up memory
                del info, prompt, dummyPrompt, data
                gc.collect()
                
            except Exception as e:
                print(f"Error processing question {i} for model {model}: {str(e)}")
                # Continue with next question despite errors
            
            # Brief pause to let system recover
            time.sleep(0.5)
    
    print(f"All processing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()