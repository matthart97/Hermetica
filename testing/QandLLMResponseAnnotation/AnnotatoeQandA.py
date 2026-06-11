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
OUTPUT_DIR = f"{BASE_PATH}/results/DualAnnotation"
OUTPUT_FILE = f"{OUTPUT_DIR}/MMLU_highschool_Chem_dual_anno.json"

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

# Define your customized prompts
# Template for initial response (without annotation)
initial_template = """
You are given a multiple choice question and a set of possible answers. Make sure you respond ONLY with the correct answer.

The question is: {question}

The possible answers are {choices}. Choose only one

Final Answer:
"""

# Template for feedback with both question and response annotations
feedback_template = """
You are a chemistry expert tasked with answering a multiple-choice chemistry question.

Both the question and your initial response have been analyzed using a chemical ontology database, providing verified scientific information about the chemical concepts involved.

### QUESTION: 
{question}

### QUESTION ONTOLOGY INFORMATION:
The following verified chemistry facts were identified in the question:
{question_annotation}

### YOUR INITIAL RESPONSE:
{initial_response}

### RESPONSE ONTOLOGY INFORMATION:
The following verified chemistry facts were identified in your response:
{response_annotation}

### POSSIBLE ANSWERS:
{choices}

Using the ontology information for both the question and your response:
1. Check if there are any misunderstandings or misconceptions in your initial reasoning
2. Consider any new information provided in the ontology that you may not have considered initially
3. Determine if your initial answer needs correction based on the verified chemistry knowledge

Provide your final answer with clear reasoning that incorporates the ontology information. Your answer must be one of the provided choices.
"""

initial_prompt = ChatPromptTemplate.from_template(initial_template)
feedback_prompt = ChatPromptTemplate.from_template(feedback_template)

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
    df = firstdf.sample(n=30, random_state=42)
    df = df.reset_index()
    llm_list = ['llama2', 'llama3.1', 'llama3.2', 'phi4', 'deepseek-r1:14b']
    
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
                
                # STEP 1: Process and annotate the question
                print(f"Annotating question {i}...")
                question_annotation = Process_Text(question)
                question_annotation = convert_to_serializable(question_annotation)
                
                # STEP 2: Get initial response from the model
                initial_msg = initial_prompt.invoke({'question': question, 'choices': choices})
                initial_response = llm.invoke(initial_msg.messages[0].content)
                
                # STEP 3: Annotate the LLM's response
                print(f"Annotating response {i}...")
                response_annotation = Process_Text(initial_response)
                response_annotation = convert_to_serializable(response_annotation)
                
                # STEP 4: Feed both annotations back to the model
                feedback_msg = feedback_prompt.invoke({
                    'question': question,
                    'question_annotation': question_annotation,
                    'initial_response': initial_response,
                    'response_annotation': response_annotation,
                    'choices': choices
                })
                
                final_response = llm.invoke(feedback_msg.messages[0].content)
                
                # Create result data
                data = {
                    'question': {
                        'text': question,
                        'choices': choices,
                        'answer': ans
                    },
                    'question_annotation': question_annotation,
                    'initial_response': initial_response,
                    'response_annotation': response_annotation,
                    'final_response': final_response
                }
                
                # Save immediately after each question
                results = save_result(results, f'{model}_{i}', data)
                
                # Free up memory
                del question_annotation, response_annotation, initial_msg, feedback_msg, data
                gc.collect()
                
            except Exception as e:
                print(f"Error processing question {i} for model {model}: {str(e)}")
                # Continue with next question despite errors
            
            # Brief pause to let system recover
            time.sleep(0.5)
    
    print(f"All processing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()





