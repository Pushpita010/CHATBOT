"""
Document Chatbot - Flask Backend
Simplified, robust implementation without heavy dependencies
"""

from flask import Flask, render_template, request, jsonify
from io import BytesIO
import uuid

from document_parser import extract_text_from_file
from document_retriever import DocumentRetriever
from llm_interface import get_llm_response

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Store documents in memory
document_store = {}

print("\n" + "="*60)
print("DOCUMENT CHATBOT - STARTING")
print("="*60)


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle document upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        model = request.form.get('model', 'llama2')

        print(f"\n📄 Uploading: {file.filename}")
        print(f"   Model: {model}")

        # Extract text from file
        try:
            file_data = BytesIO(file.read())
            doc_text = extract_text_from_file(file_data, file.filename)
            print(f"   ✓ Extracted {len(doc_text)} characters")
        except Exception as e:
            error_msg = f"Failed to extract text: {str(e)}"
            print(f"   ✗ {error_msg}")
            return jsonify({'error': error_msg}), 500

        # Process document with retriever
        try:
            print(f"   Processing document...")
            retriever = DocumentRetriever(doc_text)
            print(f"   ✓ Document indexed ({len(retriever.chunks)} chunks)")
        except Exception as e:
            error_msg = f"Failed to process document: {str(e)}"
            print(f"   ✗ {error_msg}")
            return jsonify({'error': error_msg}), 500

        # Create session
        session_id = str(uuid.uuid4())
        document_store[session_id] = {
            'retriever': retriever,
            'model': model,
            'doc_text': doc_text,
            'filename': file.filename
        }

        print(f"   ✓ Session created: {session_id[:8]}...")
        return jsonify({
            'message': f'Document "{file.filename}" processed successfully',
            'session_id': session_id
        })

    except Exception as e:
        print(f"   ✗ Unexpected error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat queries"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not user_message:
            return jsonify({'response': 'Please enter a question.'}), 400

        if not session_id or session_id not in document_store:
            return jsonify({'response': 'No document uploaded. Please upload a document first.'}), 400

        session = document_store[session_id]
        retriever = session['retriever']
        model = session['model']

        print(f"\n💬 Query: {user_message[:60]}...")
        print(f"   Model: {model}")

        # Retrieve relevant context
        try:
            print(f"   Searching document...")
            context = retriever.retrieve(user_message, top_k=3)
            print(f"   ✓ Found relevant context ({len(context)} chars)")
        except Exception as e:
            error_msg = f"Error retrieving context: {str(e)}"
            print(f"   ✗ {error_msg}")
            return jsonify({'response': f'Error: {error_msg}'}), 500

        # Get LLM response
        try:
            print(f"   Calling Ollama ({model})...")
            response = get_llm_response(user_message, context, model)
            print(f"   ✓ Response received ({len(response)} chars)")
            return jsonify({'response': response})
        except Exception as e:
            error_msg = str(e)
            print(f"   ✗ {error_msg}")
            return jsonify({'response': f'Error: {error_msg}'}), 500

    except Exception as e:
        print(f"✗ Chat error: {str(e)}")
        return jsonify({'response': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    print("\n✓ Server starting on http://localhost:5000")
    print("✓ Make sure Ollama is running: ollama serve\n")
    app.run(debug=True, use_reloader=False, port=5000)
