
from flask import Flask, render_template, request, jsonify, session
import os
from werkzeug.utils import secure_filename
from document_parser import extract_text_from_file
from llm_interface import get_llm_response

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Endpoint to handle chat queries
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    # Retrieve document text and model from session
    doc_text = session.get('doc_text')
    model = session.get('model', 'llama')
    if not doc_text:
        return jsonify({'response': 'No document uploaded yet.'}), 400
    if not user_message:
        return jsonify({'response': 'No question provided.'}), 400

    # Call LLM interface to get response
    try:
        response = get_llm_response(user_message, doc_text, model)
    except Exception as e:
        response = f'Error generating response: {str(e)}'

    return jsonify({'response': response})

@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to handle file upload and model selection
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    model = request.form.get('model', 'llama')
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text from the uploaded file
    try:
        doc_text = extract_text_from_file(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to extract text: {str(e)}'}), 500

    # Store document text and model in session
    session['doc_text'] = doc_text
    session['model'] = model

    # Optionally, generate a session id (here, just use Flask session)
    return jsonify({'message': 'File processed successfully.', 'session_id': session.sid if hasattr(session, 'sid') else None})

if __name__ == '__main__':
    app.run(debug=True)