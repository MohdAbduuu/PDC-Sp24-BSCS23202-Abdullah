"""
AI Generator with Circuit Breaker (AFTER FIX)
Wraps the external LLM API call with:
  1. A configurable TIMEOUT so the thread never blocks for 60+ seconds.
  2. A CIRCUIT BREAKER that trips after repeated failures, returning
     an instant fallback instead of hammering a dead API.

Student: Mohammad Abdullah (BSCS23202)
"""

import os
import json
import concurrent.futures
from typing import Dict, Any
from dotenv import load_dotenv

from .circuit_breaker import CircuitBreaker

load_dotenv()

# ── Module-level Circuit Breaker instance ──────────────────────
# Shared across all requests so failure state is remembered.
llm_circuit_breaker = CircuitBreaker(
    failure_threshold=3,   # trip after 3 consecutive failures
    recovery_timeout=30.0, # try again after 30 seconds
    name="llm_api",
)

# ── Configuration ──────────────────────────────────────────────
LLM_TIMEOUT_SECONDS = 10  # max wait per API call (was unlimited before)

FALLBACK_CHALLENGE = {
    "title": "Basic Python List Operation",
    "options": [
        "my_list.append(5)",
        "my_list.add(5)",
        "my_list.push(5)",
        "my_list.insert(5)",
    ],
    "correct_answer_id": 0,
    "explanation": (
        "In Python, append() is the correct method to add an element "
        "to the end of a list."
    ),
}


def _raw_llm_call(difficulty: str) -> Dict[str, Any]:
    """
    The actual LLM API call — isolated so it can be wrapped by the
    circuit breaker and executed inside a thread-pool with a timeout.
    """
    from google import genai

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    system_prompt = """You are an expert coding challenge creator. 
    Your task is to generate a coding question with multiple choice answers.
    The question should be appropriate for the specified difficulty level.

    For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
    For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
    For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

    Return the challenge in the following JSON structure:
    {
        "title": "The question title",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer_id": 0,
        "explanation": "Detailed explanation of why the correct answer is right"
    }

    Make sure the options are plausible but with only one clearly correct answer.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\nGenerate a {difficulty} difficulty coding challenge.",
        config={"response_mime_type": "application/json"},
    )

    challenge_data = json.loads(response.text)

    required_fields = ["title", "options", "correct_answer_id", "explanation"]
    for field in required_fields:
        if field not in challenge_data:
            raise ValueError(f"Missing required field: {field}")

    return challenge_data


def _llm_call_with_timeout(difficulty: str, timeout: float = LLM_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Run the LLM call in a thread pool with a hard timeout.
    This prevents the server from blocking indefinitely.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_raw_llm_call, difficulty)
        return future.result(timeout=timeout)


def _get_fallback() -> Dict[str, Any]:
    """Return a static fallback challenge when the LLM is unavailable."""
    return FALLBACK_CHALLENGE.copy()


def generate_challenge_with_ai(
    difficulty: str,
    _api_call=None,
) -> Dict[str, Any]:
    """
    Generate a coding challenge using the LLM API — PROTECTED version.

    The circuit breaker tracks consecutive failures. Once the threshold
    is reached, it immediately returns the fallback without even
    attempting the API call, saving time and server resources.

    Args:
        difficulty: "easy", "medium", or "hard"
        _api_call: Injectable API call for testing (overrides real LLM)
    """
    def _do_call():
        if _api_call is not None:
            return _api_call(difficulty)
        return _llm_call_with_timeout(difficulty)

    return llm_circuit_breaker.call(
        _do_call,
        fallback=_get_fallback,
    )