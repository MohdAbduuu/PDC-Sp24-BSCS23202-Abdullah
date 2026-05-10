"""
NAIVE AI Generator (BEFORE FIX)
This is the ORIGINAL implementation without any fault tolerance.

Problems:
  1. No timeout — if the LLM API hangs, the server thread blocks indefinitely.
  2. No circuit breaker — every request retries the failing API.
  3. Synchronous call in an async handler — blocks the entire event loop.

This file is preserved for the before/after demo comparison.
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

FALLBACK_CHALLENGE = {
    "title": "Basic Python List Operation",
    "options": [
        "my_list.append(5)",
        "my_list.add(5)",
        "my_list.push(5)",
        "my_list.insert(5)",
    ],
    "correct_answer_id": 0,
    "explanation": "In Python, append() is the correct method to add an element to the end of a list.",
}


def generate_challenge_naive(difficulty: str, _api_call=None) -> Dict[str, Any]:
    """
    Generate a coding challenge using the LLM API — NAIVE version.

    When the API is down, this function waits for the FULL timeout
    duration before falling back. During that wait, the server thread
    is completely blocked and cannot serve any other requests.

    Args:
        difficulty: "easy", "medium", or "hard"
        _api_call: Injectable API call function (for testing/demo)
    """
    system_prompt = """You are an expert coding challenge creator. 
    Your task is to generate a coding question with multiple choice answers.
    Return the challenge in JSON with keys: title, options, correct_answer_id, explanation."""

    try:
        if _api_call is not None:
            # Use injected API call (for demo/testing)
            response = _api_call(difficulty, system_prompt)
        else:
            # Real API call — NO timeout, NO circuit breaker
            from google import genai
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\n\nGenerate a {difficulty} difficulty coding challenge.",
                config={"response_mime_type": "application/json"},
            )

        challenge_data = json.loads(response.text) if not isinstance(response, dict) else response

        required_fields = ["title", "options", "correct_answer_id", "explanation"]
        for field in required_fields:
            if field not in challenge_data:
                raise ValueError(f"Missing required field: {field}")

        return challenge_data

    except Exception as e:
        print(f"[NAIVE] LLM Error: {e}")
        return FALLBACK_CHALLENGE.copy()
