"""
LLM Interface - Connect to local Ollama instance with Gemini API fallback
Falls back to Gemini API if Ollama takes more than 10 seconds
Gemini API has a 15-second timeout
Uses google-genai SDK for cleaner Gemini integration
"""

import requests
import time
import os
from typing import Tuple
import google.genai as genai


def _try_ollama(prompt: str, model: str, timeout: int = 50) -> Tuple[bool, str]:
    """
    Try to get response from local Ollama instance with explicit timing.

    Args:
        prompt: Full prompt to send
        model: Model to use
        timeout: Timeout in seconds

    Returns:
        Tuple of (success: bool, response: str)
    """
    ollama_url = "http://localhost:11434/api/generate"

    try:
        print(f"[LLM] Trying Ollama (timeout: {timeout}s)...")
        start_time = time.time()

        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=timeout
        )

        elapsed = time.time() - start_time
        print(f"[LLM] Ollama responded in {elapsed:.1f}s")

        if response.status_code != 200:
            return False, f"Ollama returned status {response.status_code}"

        data = response.json()
        result = data.get("response", "").strip()

        if not result:
            return False, "No response from Ollama model"

        print(f"[LLM] ✓ Ollama responded ({len(result)} chars)")
        return True, result

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[LLM] ✗ Ollama timeout ({elapsed:.1f}s >= {timeout}s timeout)")
        return False, "ollama_timeout"
    except requests.exceptions.ConnectionError as e:
        print(f"[LLM] ✗ Ollama connection error: {str(e)}")
        return False, "ollama_connection_error"
    except Exception as e:
        print(f"[LLM] ✗ Ollama error: {str(e)}")
        return False, str(e)


def _try_gemini(prompt: str, timeout: int = 60) -> Tuple[bool, str]:
    """
    Fallback to Google Gemini API using google-genai SDK.
    Dynamically finds and uses available models.

    Args:
        prompt: Full prompt to send
        timeout: Timeout in seconds (default: 15)

    Returns:
        Tuple of (success: bool, response: str)
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return False, "Gemini API key not configured (set GEMINI_API_KEY env variable)"

    # Create client with API key
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return False, f"Failed to create Gemini client: {str(e)}"

    print(f"[LLM] Switching to Gemini API (fallback, timeout: {timeout}s)...")

    # Try to get list of available models
    models_to_try = []
    try:
        print(f"[LLM] Fetching available Gemini models...")
        available_models = client.models.list()

        # Filter for generateContent-capable models
        for model in available_models:
            model_name = model.name
            # Extract just the model ID (e.g., "gemini-1.5-flash" from "models/gemini-1.5-flash")
            if model_name.startswith("models/"):
                model_id = model_name.split("/")[1]
            else:
                model_id = model_name

            # Check if it supports generateContent
            if hasattr(model, 'supported_generation_methods'):
                if 'generateContent' in model.supported_generation_methods:
                    models_to_try.append((model_id, client))
                    print(f"[LLM] Found available model: {model_id}")

        # If we found models, use them; otherwise use hardcoded fallback list
        if not models_to_try:
            print(f"[LLM] No available models found via API, using fallback list...")
            models_to_try = [
                ("gemini-2.5-flash", client),
                ("gemini-2.0-flash", client),
                ("gemini-2.5-pro", client),
                ("gemini-2.0-flash-lite", client),
            ]
    except Exception as e:
        print(
            f"[LLM] Could not fetch model list ({str(e)[:80]}), using fallback...")
        models_to_try = [
            ("gemini-2.5-flash", client),
            ("gemini-2.0-flash", client),
            ("gemini-2.5-pro", client),
            ("gemini-2.0-flash-lite", client),
        ]

    # Try each model
    gemini_start = time.time()
    for model_name, client in models_to_try:
        try:
            # Check if we've exceeded total timeout
            elapsed = time.time() - gemini_start
            if elapsed >= timeout:
                print(
                    f"[LLM] ✗ Gemini timeout ({elapsed:.1f}s >= {timeout}s timeout)")
                return False, "gemini_timeout"

            print(f"[LLM] Trying {model_name}...")

            # Generate response using the client with timeout
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            # Check if response was generated successfully
            if response and hasattr(response, 'text') and response.text:
                result = response.text.strip()
                if result:
                    elapsed = time.time() - gemini_start
                    print(
                        f"[LLM] ✓ Gemini ({model_name}) responded in {elapsed:.1f}s ({len(result)} chars)"
                    )
                    return True, result
            else:
                print(
                    f"[LLM] {model_name}: No text in response, trying next...")
                continue

        except Exception as e:
            # Log the error but continue to next model
            error_msg = str(e)
            if len(error_msg) > 150:
                error_msg = error_msg[:150] + "..."
            print(f"[LLM] {model_name}: {error_msg}")
            continue

    model_names = [m[0] for m in models_to_try]
    return False, f"All Gemini models failed. Tried: {', '.join(model_names)}"


def get_llm_response(user_message: str, doc_context: str, model: str = 'llama2') -> str:
    """
    Get response from LLM - tries Ollama first, falls back to Gemini if Ollama takes >10s

    Args:
        user_message: User's question
        doc_context: Relevant context from document
        model: Model to use (llama2, gemma, etc) - only for Ollama

    Returns:
        LLM response or error message
    """

    # Construct prompt with context
    prompt = f"""Based on the following document context, answer the user's question.

DOCUMENT CONTEXT:
{doc_context}

USER QUESTION:
{user_message}

ANSWER:"""

    # Try Ollama with 10 second timeout
    print("[LLM] Step 1: Attempting local Ollama...")
    success, result = _try_ollama(prompt, model, timeout=10)

    if success:
        print("[LLM] ✓ Using Ollama response")
        return result

    # If Ollama failed due to timeout or connection, try Gemini
    print(
        f"[LLM] Step 2: Ollama failed ({result}), checking if fallback is needed...")
    if result == "ollama_timeout" or result == "ollama_connection_error":
        print(
            f"[LLM] Step 3: Triggering Gemini fallback (Ollama issue: {result})...")
        success, gemini_result = _try_gemini(prompt)

        if success:
            return gemini_result
        else:
            # Gemini fallback also failed
            fallback_error = f"Both Ollama and Gemini failed: {gemini_result}"
            print(f"[LLM] ✗ {fallback_error}")
            return fallback_error

    # Ollama returned other error - don't fallback
    print(f"[LLM] ✗ Ollama error (not falling back): {result}")
    return f"Ollama error: {result}"
