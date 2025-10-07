import streamlit as st
from mod1_docingestion import extract_text
from mod2_preprocess import preprocess_contract_text
from mod3_legalClause import detect_clause_type
from mod4_legalTermRec import recognize_legal_terms, legal_terms
from mod5_LangSimple import simplify_text


st.set_page_config(page_title="ClauseEase AI", layout="wide")


USERNAME = "arnab"
PASSWORD = "1234"

def login_page():
    """Login UI"""
    st.title("ClauseEase Login")
    st.markdown("Please enter your credentials to continue.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["logged_in"] = True
            st.success("Login successful! Redirecting...")
            st.rerun()  # reload app after login
        else:
            st.error("Invalid username or password.")

def logout_button():
    """Logout button at the sidebar"""
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

# ------------------------ MAIN CLAUSEEASE APP ------------------------
def main_app():
    """Main ClauseEase workflow"""
    st.title("ClauseEase: Legal Clause Analyzer & Simplifier")
    st.markdown("Automatically analyzes a preloaded contract, detects clause types, recognizes legal terms, and simplifies language.")

    logout_button()

    # Preloaded Document Path
    contract_file_path = r"d:\Internships\Infosys SpringBoard\ClauseEase\employment_agreement.pdf"

    # Step 1: Document Ingestion
    with st.spinner("Extracting text from document..."):
        contract_text = extract_text(contract_file_path)
    if contract_text.startswith("[ERROR]"):
        st.error(contract_text)
        return
    st.success("Text extraction complete!")

    with st.expander("Extracted Text"):
        st.write(contract_text)

    # Step 2: Preprocessing
    with st.spinner("Preprocessing text into clauses..."):
        processed_clauses = preprocess_contract_text(contract_text)
    st.success("Preprocessing complete!")

    with st.expander("Preprocessed Clauses"):
        for i, clause in enumerate(processed_clauses[:5]):
            st.write(f"Clause {i+1}: {clause['cleaned_text']}")

    # Step 3: Legal Clause Detection
    with st.spinner("Detecting clause types..."):
        clause_types = [detect_clause_type(clause["cleaned_text"]) for clause in processed_clauses]
    st.success("Clause detection complete!")

    with st.expander("Legal Clause Detection"):
        for i, (clause, ctype) in enumerate(zip(processed_clauses, clause_types)):
            st.write(f"Clause {i+1}: **{ctype}**")
            st.write(clause["cleaned_text"])
            st.markdown("---")

    # Step 4: Legal Term Recognition
    with st.spinner("Recognizing legal terms..."):
        clause_terms = [recognize_legal_terms(clause["cleaned_text"], legal_terms) for clause in processed_clauses]
    st.success("Legal term recognition complete!")

    with st.expander("Legal Terms Found"):
        for i, terms in enumerate(clause_terms):
            st.write(f"Clause {i+1}:")
            if terms:
                for term, definition in terms.items():
                    st.write(f"• **{term}**: {definition}")
            else:
                st.write("No legal terms recognized.")
            st.markdown("---")

    # Step 5: Language Simplification
    with st.spinner("Simplifying clauses..."):
        simplified_clauses = [simplify_text(clause["cleaned_text"]) for clause in processed_clauses]
    st.success("Language simplification complete!")

    with st.expander("Simplified Clauses"):
        for i, simplified in enumerate(simplified_clauses):
            st.write(f"Clause {i+1}:")
            st.write(simplified)
            st.markdown("---")


# ------------------------ APP FLOW CONTROL ------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()
