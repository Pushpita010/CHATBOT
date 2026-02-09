
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from document_parser import extract_text_from_file
from llm_interface import get_llm_response

import uuid
doc_store = {}

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production


# Endpoint to handle chat queries
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id')
    chat_history = data.get('chat_history', None)
    if not session_id or session_id not in doc_store:
        return jsonify({'response': 'No document uploaded yet.'}), 400
    doc_text = doc_store[session_id]['doc_text']
    model = doc_store[session_id]['model']
    if not user_message:
        return jsonify({'response': 'No question provided.'}), 400

    # Call LLM interface to get response
    try:
        response = get_llm_response(
            user_message, doc_text, model, chat_history)
    except Exception as e:
        response = f'Error: {str(e)}'

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

    # Process file in memory without saving to disk
    try:
        file_data = BytesIO(file.read())
        doc_text = extract_text_from_file(file_data, file.filename)
    except Exception as e:
        return jsonify({'error': f'Failed to extract text: {str(e)}'}), 500

    # Store document text and model in a server-side store with a session id
    session_id = str(uuid.uuid4())
    doc_store[session_id] = {'doc_text': doc_text, 'model': model}

    return jsonify({'message': 'File processed successfully.', 'session_id': session_id})


if __name__ == '__main__':
    app.run(debug=True)
