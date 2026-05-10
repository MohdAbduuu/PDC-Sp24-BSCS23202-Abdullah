"""
=======================================================================
  DEMO: Fault Tolerance - Circuit Breaker Pattern
  Student: Mohammad Abdullah (BSCS23202)
  Course:  Parallel and Distributed Computing (PDC)
=======================================================================

This script demonstrates Problem 3 (Fault Tolerance) BEFORE and AFTER
the fix. It mocks the external LLM API to simulate downtime and shows:

  BEFORE: Every request waits for the full timeout -> server blocks.
  AFTER:  Circuit breaker trips after 3 failures -> instant fallback.

Usage:
    cd backend
    python demo_fault_tolerance.py

No API keys or running server required -- everything is self-contained.
"""

import sys
import os
import io
import time
import concurrent.futures

# Fix Windows console encoding for Unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure imports work from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# -- Configuration --
SIMULATED_API_DELAY = 3  # seconds (reduced from real 60s for demo)
NUM_BEFORE_REQUESTS = 5
NUM_AFTER_REQUESTS = 8

FALLBACK_CHALLENGE = {
    "title": "Basic Python List Operation (FALLBACK)",
    "options": [
        "my_list.append(5)",
        "my_list.add(5)",
        "my_list.push(5)",
        "my_list.insert(5)",
    ],
    "correct_answer_id": 0,
    "explanation": "In Python, append() is the correct method.",
}


# ==================================================================
#  SIMULATED FAILING LLM API
# ==================================================================

def failing_llm_api(difficulty: str = "easy"):
    """
    Simulates an LLM API that is DOWN.
    Blocks for SIMULATED_API_DELAY seconds, then raises an error.
    In production, this timeout would be 60+ seconds.
    """
    time.sleep(SIMULATED_API_DELAY)
    raise ConnectionError(
        f"HTTPSConnectionPool(host='api.llm-provider.com'): "
        f"Read timed out. (read timeout={SIMULATED_API_DELAY})"
    )


# ==================================================================
#  SCENARIO 1: BEFORE FIX (Naive - No Circuit Breaker)
# ==================================================================

def naive_generate_challenge(difficulty: str) -> dict:
    """
    Mimics the ORIGINAL ai_generator.py behavior:
    - Calls the API directly.
    - Waits for the full timeout.
    - Falls back only AFTER waiting.
    - Every. Single. Request. Waits.
    """
    try:
        return failing_llm_api(difficulty)
    except Exception as e:
        return FALLBACK_CHALLENGE.copy()


def run_before_demo():
    """Demonstrates the system WITHOUT circuit breaker."""
    print()
    print("=" * 70)
    print("  [X] BEFORE FIX: Naive Implementation (No Circuit Breaker)")
    print("=" * 70)
    print(f"  Simulated API timeout: {SIMULATED_API_DELAY}s per request")
    print(f"  Sending {NUM_BEFORE_REQUESTS} sequential requests...\n")

    total_start = time.time()

    for i in range(1, NUM_BEFORE_REQUESTS + 1):
        start = time.time()
        print(f"  Request {i}/{NUM_BEFORE_REQUESTS}: [WAITING] Calling LLM API...", end="", flush=True)
        result = naive_generate_challenge("easy")
        elapsed = time.time() - start
        print(f"  [FAIL] Waited {elapsed:.1f}s -> fell back to static response")

    total = time.time() - total_start
    print(f"\n  +----------------------------------------------------+")
    print(f"  |  Total time: {total:.1f}s for {NUM_BEFORE_REQUESTS} requests                    |")
    print(f"  |  Server was BLOCKED the entire time!                |")
    print(f"  |  In production (60s timeout): ~{NUM_BEFORE_REQUESTS * 60}s total!        |")
    print(f"  |  ALL other users are stuck waiting too!             |")
    print(f"  +----------------------------------------------------+")

    return total


# ==================================================================
#  SCENARIO 2: AFTER FIX (Circuit Breaker Pattern)
# ==================================================================

def run_after_demo():
    """Demonstrates the system WITH circuit breaker."""
    # Import the REAL circuit breaker from our codebase
    from src.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
        name="llm_api_demo",
    )

    print()
    print("=" * 70)
    print("  [OK] AFTER FIX: Circuit Breaker Pattern")
    print("=" * 70)
    print(f"  Failure threshold: {cb.failure_threshold} consecutive failures")
    print(f"  Recovery timeout:  {cb.recovery_timeout}s")
    print(f"  Sending {NUM_AFTER_REQUESTS} sequential requests...\n")

    total_start = time.time()

    for i in range(1, NUM_AFTER_REQUESTS + 1):
        start = time.time()
        state_before = cb.state.value

        print(f"  Request {i}/{NUM_AFTER_REQUESTS}: [{state_before:9s}] ", end="", flush=True)

        # Use the circuit breaker to wrap the failing API call
        result = cb.call(
            failing_llm_api,
            "easy",
            fallback=lambda: FALLBACK_CHALLENGE.copy(),
        )

        elapsed = time.time() - start
        state_after = cb.state.value

        if elapsed < 0.5:
            print(f">> INSTANT fallback in {elapsed:.4f}s")
        else:
            print(f"[FAIL] Failed after {elapsed:.1f}s "
                  f"(failures: {cb.failure_count}/{cb.failure_threshold})")
            if state_after == "OPEN":
                print(f"           >>> CIRCUIT TRIPPED! All future requests get instant fallback!")

    total = time.time() - total_start
    slow_requests = min(cb.failure_threshold, NUM_AFTER_REQUESTS)
    fast_requests = max(0, NUM_AFTER_REQUESTS - slow_requests)

    print(f"\n  +----------------------------------------------------+")
    print(f"  |  Total time: {total:.1f}s for {NUM_AFTER_REQUESTS} requests                    |")
    print(f"  |  Only {slow_requests} slow calls (before circuit tripped)         |")
    print(f"  |  {fast_requests} requests served INSTANTLY via fallback         |")
    print(f"  |  Saved ~{fast_requests * SIMULATED_API_DELAY}s compared to naive approach!           |")
    print(f"  +----------------------------------------------------+")

    return total


# ==================================================================
#  SCENARIO 3: CONCURRENT REQUESTS (Bonus - shows server impact)
# ==================================================================

def run_concurrent_demo():
    """Shows how the circuit breaker helps under concurrent load."""
    from src.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30, name="concurrent_demo")

    print()
    print("=" * 70)
    print("  [BONUS] Concurrent Requests Comparison")
    print("=" * 70)

    # -- BEFORE: 5 concurrent naive requests --
    print(f"\n  --- Naive: 5 concurrent requests (no circuit breaker) ---")
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(naive_generate_challenge, "easy") for _ in range(5)]
        concurrent.futures.wait(futures)
    naive_time = time.time() - start
    print(f"  [TIME] All 5 completed in {naive_time:.1f}s (each waited {SIMULATED_API_DELAY}s)")

    # -- Pre-trip the circuit breaker --
    print(f"\n  --- Circuit Breaker: pre-tripping with 3 failures ---")
    for _ in range(3):
        cb.call(failing_llm_api, "easy", fallback=lambda: FALLBACK_CHALLENGE.copy())
    print(f"  [OPEN] Circuit is now: {cb.state.value}")

    # -- AFTER: 5 concurrent requests with open circuit --
    print(f"\n  --- Circuit Breaker: 5 concurrent requests (circuit OPEN) ---")
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [
            pool.submit(
                cb.call,
                failing_llm_api, "easy",
                fallback=lambda: FALLBACK_CHALLENGE.copy(),
            )
            for _ in range(5)
        ]
        concurrent.futures.wait(futures)
    cb_time = time.time() - start
    print(f"  [FAST] All 5 completed in {cb_time:.4f}s (instant fallback!)")
    print(f"  [SPEEDUP] {naive_time / max(cb_time, 0.001):.0f}x faster")


# ==================================================================
#  MAIN
# ==================================================================

if __name__ == "__main__":
    print()
    print("+====================================================================+")
    print("|   StudySync -- Fault Tolerance Demo                                |")
    print("|   Student: Mohammad Abdullah (BSCS23202)                           |")
    print("|   Problem: Synchronous LLM call blocks entire server              |")
    print("|   Fix:     Circuit Breaker Pattern with Fallback Response          |")
    print("+====================================================================+")

    before_time = run_before_demo()
    after_time = run_after_demo()
    run_concurrent_demo()

    # -- Summary --
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  BEFORE (naive):           {before_time:.1f}s for {NUM_BEFORE_REQUESTS} requests")
    print(f"  AFTER  (circuit breaker): {after_time:.1f}s for {NUM_AFTER_REQUESTS} requests")
    print(f"  Improvement:              {before_time / max(after_time, 0.001):.1f}x faster overall")
    print()
    print("  The Circuit Breaker pattern prevents cascading failures by")
    print("  detecting when a service is down and short-circuiting calls")
    print("  to return a fallback response instantly.")
    print()
    print("  [OK] Server stays responsive for ALL users")
    print("  [OK] No wasted time retrying a known-dead API")
    print("  [OK] Automatic recovery when the API comes back (HALF_OPEN probe)")
    print()
