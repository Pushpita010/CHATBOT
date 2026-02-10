
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from document_parser import extract_text_from_file
from document_indexer import DocumentIndex
from llm_interface import get_llm_response

import uuid
import traceback
import sys

doc_store = {}

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

print("[App] Flask application starting...", file=sys.stderr)

# Endpoint to handle chat queries


@app.route('/chat', methods=['POST'])
def chat():
    print("[Chat] Request received", file=sys.stderr)
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id')
    chat_history = data.get('chat_history', None)

    if not session_id or session_id not in doc_store:
        return jsonify({'response': 'No document uploaded yet.'}), 400

    index = doc_store[session_id]['index']
    model = doc_store[session_id]['model']

    if not user_message:
        return jsonify({'response': 'No question provided.'}), 400

    # Call LLM interface to get response
    try:
        print(
            f"[Chat] Starting semantic search for: {user_message[:50]}...", file=sys.stderr)
        # Use semantic search to get relevant context
        relevant_context = index.query(user_message, top_k=3)
        print(
            f"[Chat] Semantic search completed. Context length: {len(relevant_context)}", file=sys.stderr)

        print(f"[Chat] Calling LLM with model: {model}", file=sys.stderr)
        response = get_llm_response(
            user_message, relevant_context, model, chat_history)
        print(
            f"[Chat] LLM response received. Length: {len(response)}", file=sys.stderr)
    except Exception as e:
        error_msg = f'Error: {str(e)}'
        print(f"[Chat] Exception occurred: {error_msg}", file=sys.stderr)
        print(f"[Chat] Traceback: {traceback.format_exc()}", file=sys.stderr)
        response = error_msg

    return jsonify({'response': response})


@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to handle file upload and model selection
@app.route('/upload', methods=['POST'])
def upload():
    print("[Upload] File upload request received", file=sys.stderr)
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    model = request.form.get('model', 'llama')
    print(
        f"[Upload] Processing file: {file.filename}, model: {model}", file=sys.stderr)

    # Process file in memory without saving to disk
    try:
        print("[Upload] Extracting text from file...", file=sys.stderr)
        file_data = BytesIO(file.read())
        doc_text = extract_text_from_file(file_data, file.filename)
        print(
            f"[Upload] Text extraction complete. Length: {len(doc_text)}", file=sys.stderr)
    except Exception as e:
        error_msg = f'Failed to extract text: {str(e)}'
        print(f"[Upload] {error_msg}", file=sys.stderr)
        print(f"[Upload] Traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({'error': error_msg}), 500

    # Create document index for semantic search
    try:
        print("[Upload] Initializing DocumentIndex...", file=sys.stderr)
        index = DocumentIndex()
        print(
            "[Upload] DocumentIndex created. Creating index from document...", file=sys.stderr)
        index.create_index(doc_text)
        print("[Upload] Document index created successfully", file=sys.stderr)
    except Exception as e:
        error_msg = f'Failed to index document: {str(e)}'
        print(f"[Upload] {error_msg}", file=sys.stderr)
        print(f"[Upload] Traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({'error': error_msg}), 500

    # Store document index and metadata
    session_id = str(uuid.uuid4())
    doc_store[session_id] = {'index': index,
                             'model': model, 'doc_text': doc_text}
    print(f"[Upload] Session created: {session_id}", file=sys.stderr)

    return jsonify({'message': 'File processed successfully.', 'session_id': session_id})


if __name__ == '__main__':
    app.run(debug=True)
