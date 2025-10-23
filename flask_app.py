import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, session
from werkzeug.utils import secure_filename

# Import existing modules
from mod1_docingestion import extract_text
from mod2_preprocess import preprocess_contract_text
from mod3_legalClause import detect_clause_type
from mod4_legalTermRec import recognize_legal_terms, legal_terms
from mod5_LangSimple import simplify_text
import json
import io

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'dev-secret-for-demo'  # Required for session management

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple in-memory user store for demo purposes
USERS = {
    'arnab@test.com': {'password': '1234', 'name': 'Arnab'}
}

# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # check in-memory USERS store first
        user = USERS.get(email)
        if user and user.get('password') == password:
            session['user_email'] = email
            session['user_name'] = user.get('name', '')
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        # fallback: check legacy hardcoded credential (kept for backward-compat)
        if email == 'arnab@test.com' and password == '1234':
            session['user_email'] = email
            session['user_name'] = 'Arnab'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If GET, just render the login page (which contains signup form)
    if request.method == 'GET':
        return render_template('login.html')

    # POST: create user, set session, and redirect to dashboard
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password or not name:
        flash('Please provide name, email and password', 'error')
        return redirect(url_for('index'))

    if email in USERS:
        flash('An account with this email already exists. Please log in.', 'error')
        return redirect(url_for('index'))

    # create user
    USERS[email] = {'password': password, 'name': name}
    # set session so user is logged in immediately
    session['user_email'] = email
    session['user_name'] = name
    flash('Registration successful — welcome!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    uploaded_file_info = None
    results = None
    logo_filename = None
    candidate = os.path.join(app.config['UPLOAD_FOLDER'], 'logo.png')
    if os.path.exists(candidate):
        logo_filename = 'logo.png'
    if request.method == 'POST':
        # handle uploaded document
        # if a logo file was uploaded via a field named 'logo', save it as logo.png
        if 'logo' in request.files and request.files['logo'].filename != '':
            logo_file = request.files['logo']
            if logo_file and allowed_file(logo_file.filename):
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'logo.png')
                logo_file.save(logo_path)
                logo_filename = 'logo.png'

        if 'document' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['document']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            uploaded_file_info = {'name': filename, 'path': save_path}

            # Run pipeline: extract -> preprocess -> detect -> terms -> simplify
            contract_text = extract_text(save_path)
            if contract_text.startswith('[ERROR]'):
                flash(contract_text)
                return redirect(request.url)

            processed_clauses = preprocess_contract_text(contract_text)
            clause_types = [detect_clause_type(c['cleaned_text']) for c in processed_clauses]
            clause_terms = [recognize_legal_terms(c['cleaned_text'], legal_terms) for c in processed_clauses]
            simplified = [simplify_text(c['cleaned_text']) for c in processed_clauses]

            results = []
            for i, c in enumerate(processed_clauses):
                results.append({
                    'index': i+1,
                    'raw': c['raw_text'],
                    'cleaned': c['cleaned_text'],
                    'type': clause_types[i],
                    'terms': clause_terms[i],
                    'simple': simplified[i]
                })
            # persist results to a JSON file next to the uploaded file so we can
            # generate PDFs later or serve them for download
            try:
                json_path = save_path + '.results.json'
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(results, jf, ensure_ascii=False, indent=2)
            except Exception as e:
                app.logger.warning(f"Could not save results JSON: {e}")
    return render_template('dashboard.html', uploaded=uploaded_file_info, results=results, logo_filename=logo_filename)


@app.route('/download_results')
def download_results():
    filename = request.args.get('filename')
    if not filename:
        flash('No filename provided for download')
        return redirect(url_for('dashboard'))

    # expect a results json saved as <uploaded_filename>.results.json
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + '.results.json')
    if not os.path.exists(json_path):
        flash('No results available to download for this file.')
        return redirect(url_for('dashboard'))

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        flash('PDF generation requires the reportlab package. Install with: pip install reportlab')
        return redirect(url_for('dashboard'))

    # load results
    with open(json_path, 'r', encoding='utf-8') as jf:
        results = json.load(jf)

    # generate PDF in-memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 72
    y = height - margin

    # header
    c.setFont('Helvetica-Bold', 16)
    c.drawString(margin, y, f'Analysis Results — {filename}')
    y -= 24
    c.setFont('Helvetica', 10)

    def write_wrapped(text, indent=0, max_width=80):
        nonlocal y
        import textwrap
        lines = textwrap.wrap(text, max_width)
        for ln in lines:
            if y < margin + 40:
                c.showPage()
                y = height - margin
                c.setFont('Helvetica', 10)
            c.drawString(margin + indent, y, ln)
            y -= 12

    for r in results:
        if y < margin + 80:
            c.showPage()
            y = height - margin
            c.setFont('Helvetica', 10)

        c.setFont('Helvetica-Bold', 12)
        c.drawString(margin, y, f"Clause {r.get('index')} — {r.get('type')}")
        y -= 14
        c.setFont('Helvetica', 10)
        write_wrapped(r.get('cleaned', ''), indent=8, max_width=90)
        y -= 6
        # terms
        terms = r.get('terms') or {}
        if terms:
            c.setFont('Helvetica-Bold', 10)
            c.drawString(margin + 8, y, 'Terms:')
            y -= 12
            c.setFont('Helvetica', 9)
            for t, info in terms.items():
                definition = info.get('definition') if isinstance(info, dict) else info
                method = info.get('method') if isinstance(info, dict) else ''
                write_wrapped(f"- {t}: {definition} ({method})", indent=16, max_width=86)
                y -= 4
        else:
            c.drawString(margin + 8, y, 'Terms: None')
            y -= 14

        # simplified
        c.setFont('Helvetica-Bold', 10)
        c.drawString(margin + 8, y, 'Simplified:')
        y -= 12
        c.setFont('Helvetica', 10)
        write_wrapped(r.get('simple', ''), indent=16, max_width=86)
        y -= 12

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{filename}_analysis.pdf", mimetype='application/pdf')


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(port=3000, debug=True)