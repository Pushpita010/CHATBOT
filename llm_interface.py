# Placeholder for LLM response function
def get_llm_response(user_message, doc_text, model):
	"""
	Simulate an LLM response. Replace this with actual LLM integration (e.g., via Ollama, LlamaIndex, or Langchain).
	"""
	# For now, just echo the question and mention the model
	return f"[Model: {model}] You asked: '{user_message}'. (Document length: {len(doc_text)} characters)"
