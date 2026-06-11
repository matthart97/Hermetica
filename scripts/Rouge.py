"""
For calculating the rouge similarity between two strings 

returns rouge1, rouge2, rougeL

"""

from rouge_score import rouge_scorer

def calculate_rouge_metrics(reference, candidate):
    """
    Calculate ROUGE-1, ROUGE-2, and ROUGE-L using the rouge-score package.
    
    Args:
        reference: Reference text
        candidate: Candidate text to compare against reference
        
    Returns:
        Dictionary containing ROUGE-1, ROUGE-2, and ROUGE-L F1 scores
    """
    # Initialize scorer with the metrics we want
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    
    # Calculate scores
    scores = scorer.score(reference, candidate)
    
    # Extract F1 scores
    return {
        'rouge1': scores['rouge1'].fmeasure,
        'rouge2': scores['rouge2'].fmeasure,
        'rougeL': scores['rougeL'].fmeasure
    }

# Example usage
reference = "The quick brown fox jumps over the lazy dog."
candidate = "The fast brown fox leaps over the lazy dog."
results = calculate_rouge_metrics(reference, candidate)
print(results)