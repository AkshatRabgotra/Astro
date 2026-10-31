"""Circuit breaker implementation for external LLM API resilience."""

from enum import Enum
import time
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"        # Healthy, requests pass through
    OPEN = "open"            # Failing, fast fail without calling provider
    HALF_OPEN = "half_open"  # Testing if provider has recovered


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()

    def allow_request(self) -> bool:
        """Check if request is permitted under current circuit state."""
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (now - self.last_failure_time >= self.recovery_timeout_seconds):
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow a trial request through
            return True

        return False

    def record_success(self):
        """Record successful call: reset failures and close circuit."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()

    def record_failure(self):
        """Record failed call: increment failures and open circuit if threshold exceeded."""
        now = time.time()
        self.failure_count += 1
        self.last_failure_time = now

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = now
