from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from mod1_docingestion import extract_text
from mod2_preprocess import preprocess_contract_text

# Load Pretrained Legal-BERT Model

model_name = "nlpaueb/legal-bert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=5)


# Define Clause Categories
clause_labels = {
    0: "Confidentiality",
    1: "Termination",
    2: "Indemnity",
    3: "Dispute Resolution",
    4: "Governing Law"
}

# -----------------------------------------------------------
# Function: Detect Clause Type
# -----------------------------------------------------------
def detect_clause_type(text: str) -> str:
    """
    Predict the clause type for a given piece of text using Legal-BERT.
    """
    if not text.strip():
        return "Unknown"

    # Tokenize the input text
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    # Forward pass through the model
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=1).item()

    return clause_labels.get(predicted_class, "Unknown")


# -----------------------------------------------------------
# Example Usage – Integrate with previous modules
# -----------------------------------------------------------
if __name__ == "__main__":
    # Step 1 – Extract raw text from PDF/DOCX using Module 1
    contract_file = r"d:\Internships\Infosys SpringBoard\ClauseEase\employment_agreement.pdf"
    contract_text = extract_text(contract_file)

    if contract_text.startswith("[ERROR]"):
        print(contract_text)
    else:
        # Step 2 – Preprocess text into clauses using Module 2
        processed_clauses = preprocess_contract_text(contract_text)

        # Step 3 – Run clause detection on each clause
        print("✅ Running Legal Clause Detection...\n")
        for i, clause in enumerate(processed_clauses[:5]):  # limit output to first 5 clauses
            clause_text = clause["cleaned_text"]
            detected_type = detect_clause_type(clause_text)
            print(f"Clause {i+1}: {detected_type}\n{clause_text}\n{'-'*80}")