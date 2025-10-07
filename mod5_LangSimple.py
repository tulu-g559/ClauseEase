from transformers import pipeline
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize

# Lightweight T5 model for paraphrasing / simplification
simplifier = pipeline("text2text-generation", model="t5-small")  

def simplify_text(text, max_length=60):
    sentences = sent_tokenize(text)
    simplified_sentences = []
    
    for sent in sentences:
        if sent.strip():
            simplified = simplifier(
                sent,  # no prefix
                max_length=120,
                num_beams=5,
                early_stopping=True
            )
            simplified_sentences.append(simplified[0]['generated_text'])
    
    return ' '.join(simplified_sentences)


# Example Usage
if __name__ == "__main__":
    complex_clause = """
    Notwithstanding anything to the contrary contained herein, the Lessee shall indemnify and hold harmless the Lessor from any liability arising out of the Lessee's use of the premises, including but not limited to, claims of third parties.
    """
    simplified_clause = simplify_text(complex_clause)

    print("✅ Original Clause:\n", complex_clause)
    print("\n✅ Simplified Clause:\n", simplified_clause)
