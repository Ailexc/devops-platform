"""
Circuit Breaker — protects downstream AWS API calls from cascading failures.

Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (probing).
Implements the standard circuit breaker pattern with a sliding window.
"""

import time
from enum import Enum
from dataclasses import dataclass


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_attempts: int = 3


class CircuitBreaker:
    """Per-resource-type circuit breaker."""

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.half_open_attempts = 0

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")

        if self.state == CircuitState.HALF_OPEN and self.half_open_attempts >= self.config.half_open_max_attempts:
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' HALF_OPEN max attempts reached")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_attempts += 1
            if self.half_open_attempts >= self.config.half_open_max_attempts:
                self.state = CircuitState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

    def reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    pass
