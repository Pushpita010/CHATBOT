"""
LLM Interface - Connect to local Ollama instance
"""

import requests
import time


def get_llm_response(user_message: str, doc_context: str, model: str = 'llama2') -> str:
    """
    Get response from local Ollama LLM
    
    Args:
        user_message: User's question
        doc_context: Relevant context from document
        model: Model to use (llama2, gemma, etc)
    
    Returns:
        LLM response or error message
    """
    
    ollama_url = "http://localhost:11434/api/generate"
    
    # Construct prompt with context
    prompt = f"""Based on the following document context, answer the user's question.

DOCUMENT CONTEXT:
{doc_context}

USER QUESTION:
{user_message}

ANSWER:"""
    
    try:
        print(f"[LLM] Sending request to Ollama...")
        print(f"[LLM] Model: {model}")
        print(f"[LLM] Waiting for response (this may take 30-60 seconds)...")
        
        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            error_msg = f"Ollama returned status {response.status_code}"
            print(f"[LLM] ✗ {error_msg}")
            return f"Error: {error_msg}"
        
        data = response.json()
        result = data.get("response", "").strip()
        
        if not result:
            print(f"[LLM] ✗ No response from model")
            return "The model did not generate a response. Try a different question."
        
        print(f"[LLM] ✓ Response received ({len(result)} characters)")
        return result
    
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Ollama. Make sure it's running with: ollama serve"
        print(f"[LLM] ✗ {error_msg}")
        return error_msg
    
    except requests.exceptions.Timeout:
        error_msg = "Request timed out. The model is taking too long. Try a shorter question."
        print(f"[LLM] ✗ {error_msg}")
        return error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[LLM] ✗ {error_msg}")
        return error_msg
