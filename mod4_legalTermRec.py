import re
import difflib
from mod3_legalClause import detect_clause_type
from mod1_docingestion import extract_text
from mod2_preprocess import preprocess_contract_text


# Custom Legal Term Dictionary

legal_terms = {
    "indemnity": "Security or protection against a loss or other financial burden.",
    "arbitration": "A method of resolving disputes outside the courts.",
    "force majeure": "Unforeseeable circumstances that prevent someone from fulfilling a contract.",
    "breach": "A violation of a law, duty, or other form of obligation.",
    "jurisdiction": "The official power to make legal decisions and judgments.",
    "confidentiality": "Obligation to keep certain information secret.",
    "termination": "Ending of the contract or agreement before its natural expiry."
}

# Synonyms / alternative phrases to improve recall
term_synonyms = {
    "indemnity": ["indemnify", "hold harmless", "liability", "indemnification"],
    "arbitration": ["arbitrat", "tribunal", "panel"],
    "force majeure": ["force majeure", "act of god", "unforeseeable"],
    "breach": ["breach", "violation", "commit a breach"],
    "jurisdiction": ["jurisdiction", "venue", "competent court"],
    "confidentiality": ["confidential", "non-disclosure", "non disclosure", "secret", "disclos"],
    "termination": ["terminate", "termination", "expiry", "end of employment", "dismissal"]
}

# Regex patterns for more semantic matches (verbs, surrounding words)
term_patterns = {
    "confidentiality": [r'not to disclose', r'not disclose', r'keep .* secret', r'non[- ]disclos'],
    "termination": [r'terminat', r'end of employ', r'dismissal', r'resigne?'],
    "indemnity": [r'hold harmless', r'indemnif', r'liabilit'],
    "arbitration": [r'arbitrat', r'dispute resolution', r'mediation'],
    "force majeure": [r'force majeure', r'act of god', r'unforeseeable circum'],
    "breach": [r'breach of', r'violation of'],
    "jurisdiction": [r'jurisdiction', r'governed by the laws of', r'venue for']
}


# Function: Recognize Legal Terms in Text

def recognize_legal_terms(text: str, term_dict: dict) -> dict:
    """
    Identify legal terms in text using a custom dictionary, synonyms, regex patterns,
    and fuzzy matching. Returns a dict of found terms -> {definition, method}.
    """
    found_terms = {}
    if not text:
        return found_terms

    # remove extra punctuation for matching but keep newlines to preserve clause structure
    clean_text = re.sub(r"[^\n\w\s]", ' ', text.lower())

    # 1) Exact match on canonical term
    for term, definition in term_dict.items():
        if re.search(r"\b" + re.escape(term.lower()) + r"\b", clean_text):
            found_terms[term] = {"definition": definition, "method": "exact"}

    # 2) Synonym matching
    for term, synonyms in term_synonyms.items():
        if term in found_terms:
            continue
        for syn in synonyms:
            if re.search(r"\b" + re.escape(syn.lower()) + r"\b", clean_text):
                found_terms[term] = {"definition": term_dict.get(term, ""), "method": f"synonym:{syn}"}
                break

    # 3) Regex semantic patterns
    for term, patterns in term_patterns.items():
        if term in found_terms:
            continue
        for pat in patterns:
            if re.search(pat, clean_text):
                found_terms[term] = {"definition": term_dict.get(term, ""), "method": f"pattern:{pat}"}
                break

    # 4) Fuzzy word matching as a last resort
    if not found_terms:
        words = re.findall(r"\w+", clean_text)
        # compare words to canonical terms
        for term in term_dict.keys():
            matches = difflib.get_close_matches(term, words, n=1, cutoff=0.85)
            if matches:
                found_terms[term] = {"definition": term_dict.get(term, ""), "method": f"fuzzy:{matches[0]}"}

    # 5) If still empty, try to infer from clause classification
    if not found_terms:
        try:
            inferred = detect_clause_type(text)
            # Map clause label to canonical term if applicable
            label_to_term = {
                "Confidentiality": "confidentiality",
                "Termination": "termination",
                "Indemnity": "indemnity",
                "Dispute Resolution": "arbitration",
                "Governing Law": "jurisdiction"
            }
            mapped = label_to_term.get(inferred)
            if mapped:
                found_terms[mapped] = {"definition": term_dict.get(mapped, ""), "method": f"inferred_from_clause:{inferred}"}
        except Exception:
            # If detect_clause_type not available or errors, ignore
            pass

    return found_terms



# Example Usage – Integrate with previous modules

if __name__ == "__main__":
    # Step 1 – Extract raw text from PDF/DOCX using Module 1
    contract_file = r"d:\Internships\Infosys SpringBoard\ClauseEase\employment_agreement.pdf"
    contract_text = extract_text(contract_file)

    if contract_text.startswith("[ERROR]"):
        print(contract_text)
    else:
        # Step 2 – Preprocess text into clauses using Module 2
        processed_clauses = preprocess_contract_text(contract_text)

        print("✅ Running Legal Term Recognition...\n")
        for i, clause in enumerate(processed_clauses[:5]):  # limit to first 5 clauses
            clause_text = clause.get("cleaned_text") or clause.get("raw_text") or ""

            # Step 3 – Detect legal terms in each clause
            recognized_terms = recognize_legal_terms(clause_text, legal_terms)

            # Also get the clause classification (may help when no explicit terms found)
            try:
                clause_label = detect_clause_type(clause_text)
            except Exception:
                clause_label = "Unknown"

            print(f"Clause {i+1} (predicted type: {clause_label}):")
            print(clause_text)

            # If no explicit terms found, show that we inferred one from clause type
            if recognized_terms:
                print("\n🔹 Recognized Legal Terms:")
                for term, info in recognized_terms.items():
                    definition = info.get("definition") if isinstance(info, dict) else info
                    method = info.get("method") if isinstance(info, dict) else ""
                    print(f"   • {term}: {definition} (method: {method})")
            else:
                # Try to map the clause label to a canonical legal term
                label_to_term = {
                    "Confidentiality": "confidentiality",
                    "Termination": "termination",
                    "Indemnity": "indemnity",
                    "Dispute Resolution": "arbitration",
                    "Governing Law": "jurisdiction"
                }
                mapped = label_to_term.get(clause_label)
                if mapped:
                    print(f"\n🔹 No explicit legal dictionary matches — inferring term from clause type:")
                    print(f"   • {mapped}: {legal_terms.get(mapped, '')} (method: inferred_from_clause:{clause_label})")
                else:
                    print("\n🔹 No legal terms recognized.")
            print("-"*80)
