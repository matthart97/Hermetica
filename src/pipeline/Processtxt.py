"""
Takes in natural language, and outputs reasoning and annotations in json and natural language

"""
import sys
import os 
import json 
sys.path.append('../../src')
from pipeline.ChEBIPipeline import ChEBIPipeline as AnnotationCheck
from reasoning.OntoValidation.ChEBIReasoner import ChEBIReasoner as Reasoner
from reasoning.LLMFeedback.Pipe2NL import extract_chebi_ids, ChEBINameRetriever, replace_chebi_ids, format_json_as_prompt


def core(text,output_path):
    # start with annotations
    annotations = AnnotationCheck(text)
    Reasoned = Reasoner(annotations)
    # save the machine readable annotations with CHEBI IDs
    
    # convert the stuff back into NL for LLM input 
    finder = ChEBINameRetriever('/home/matt/Proj/Hermeticav2/data/ontologies/Chemistry/chebi.owl')
    IDs = extract_chebi_ids(Reasoned)
    mapping = finder(IDs)
    PreNL = replace_chebi_ids(Reasoned,mapping)
    NL = format_json_as_prompt(PreNL)

    return NL



# tesing 

