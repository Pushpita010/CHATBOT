
# Real LLM integration using OpenAI API
import openai
import os

# Set your OpenAI API key as an environment variable for security
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_llm_response(user_message, doc_text, model, chat_history=None):
	"""
	Get a response from OpenAI's GPT model, using the document text and chat history.
	"""
	if not openai.api_key:
		return "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable."

	# Build the prompt and chat history
	system_prompt = "You are a helpful assistant that answers questions about uploaded documents."
	doc_context = f"The user uploaded a document. Here is the content:\n\n{doc_text[:4000]}\n\n(Only the first 4000 characters are shown to the model for context.)"
	messages = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": doc_context}
	]
	if chat_history:
		for entry in chat_history:
			messages.append({"role": "user", "content": entry["user"]})
			messages.append({"role": "assistant", "content": entry["bot"]})
	messages.append({"role": "user", "content": user_message})

	try:
		response = openai.ChatCompletion.create(
			model="gpt-3.5-turbo",  # or "gpt-4" if you have access
			messages=messages,
			max_tokens=512,
			temperature=0.2
		)
		return response.choices[0].message['content'].strip()
	except Exception as e:
		return f"Error contacting OpenAI API: {str(e)}"
