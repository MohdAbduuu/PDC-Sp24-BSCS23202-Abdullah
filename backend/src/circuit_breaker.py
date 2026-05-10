"""
Circuit Breaker Pattern Implementation
Prevents cascading failures when an external service (e.g., LLM API) is down.

States:
  CLOSED    → Normal operation. Requests pass through.
  OPEN      → Service is known to be down. Requests are short-circuited immediately.
  HALF_OPEN → Recovery probe. One test request is allowed through.

Transitions:
  CLOSED → OPEN:      After `failure_threshold` consecutive failures.
  OPEN → HALF_OPEN:   After `recovery_timeout` seconds have elapsed.
  HALF_OPEN → CLOSED: If the probe request succeeds.
  HALF_OPEN → OPEN:   If the probe request fails.

Student: Mohammad Abdullah (BSCS23202)
"""

import time
import threading
from enum import Enum
from typing import Callable, Optional, Any


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""
    pass


class CircuitBreaker:
    """
    Thread-safe Circuit Breaker for wrapping unreliable external service calls.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    # ── Properties ──────────────────────────────────────────────

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN and self._last_failure_time:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
            return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    # ── Core Method ─────────────────────────────────────────────

    def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ) -> Any:
        """
        Execute `func` through the circuit breaker.

        If the circuit is OPEN and a `fallback` is provided, the fallback
        is returned immediately without attempting the real call.
        """
        current_state = self.state  # property handles OPEN→HALF_OPEN

        # ── OPEN: fail-fast ──
        if current_state == CircuitState.OPEN:
            if fallback is not None:
                return fallback()
            raise CircuitBreakerOpenError(
                f"Circuit '{self.name}' is OPEN — call rejected"
            )

        # ── CLOSED or HALF_OPEN: attempt the call ──
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            if fallback is not None:
                return fallback()
            raise

    # ── Internal State Transitions ──────────────────────────────

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    # ── Utility ─────────────────────────────────────────────────

    def reset(self):
        """Reset the circuit breaker to its initial CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self.state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )
