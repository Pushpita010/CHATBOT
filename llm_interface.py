
# Real LLM integration using OpenAI API

# Ollama integration for local LLMs (Llama, Gemma, etc.)
import requests

def get_llm_response(user_message, doc_text, model, chat_history=None):
	"""
	Get a response from a local LLM (Llama, Gemma, etc.) using Ollama's API.
	"""
	# Use only the first 4000 characters for context (Ollama context limit)
	context = doc_text[:4000]
	prompt = f"Document:\n{context}\n\nUser question: {user_message}\n\nAnswer:"
	try:
		response = requests.post(
			"http://localhost:11434/api/generate",
			json={
				"model": model,  # e.g., "llama2" or "gemma"
				"prompt": prompt,
				"stream": False
			},
			timeout=300  # Increased to 5 minutes for slower models
		)
		response.raise_for_status()
		data = response.json()
		return data.get("response", "No response from LLM.")
	except requests.exceptions.Timeout:
		return "Response took too long. Try a shorter question or check if Ollama is running and model is loaded."
	except requests.exceptions.ConnectionError:
		return "Cannot connect to Ollama. Make sure Ollama is running: ollama serve"
	except Exception as e:
		return f"Error: {str(e)}"
