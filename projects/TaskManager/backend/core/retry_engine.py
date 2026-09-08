"""
Retry Engine — three-layer retry strategy.

Layer 1: Automatic retry with exponential backoff + jitter (transient failures)
Layer 2: Circuit breaker protection (sustained failures)
Layer 3: DLQ + notification (unrecoverable failures)

This module provides a decorator/function that orchestrates all three layers.
"""

import time
import random
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def exponential_backoff(attempt: int, base: float = 3.0, jitter: bool = True) -> float:
    delay = base ** attempt
    if jitter:
        delay += random.uniform(0, 1)
    return delay


class RetryEngine:
    """Three-layer retry orchestrator.

    Usage:
        engine = RetryEngine(max_retries=3)
        result = engine.execute(my_func, arg1, arg2)
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 3.0,
        jitter: bool = True,
        circuit_breaker=None,  # optional CircuitBreaker instance
        on_final_failure=None,  # callable(exception) — Layer 3 hook
    ):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.jitter = jitter
        self.circuit_breaker = circuit_breaker
        self.on_final_failure = on_final_failure

    def execute(self, func, *args, **kwargs):
        last_exc = None

        for attempt in range(1, self.max_retries + 2):  # +1 for initial try
            try:
                if self.circuit_breaker:
                    return self.circuit_breaker.call(func, *args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                logger.warning(f"Attempt {attempt}/{self.max_retries + 1} failed: {e}")
                if attempt <= self.max_retries:
                    delay = exponential_backoff(attempt, self.backoff_base, self.jitter)
                    logger.info(f"Backing off {delay:.1f}s before retry...")
                    time.sleep(delay)

        # Layer 3: final failure
        logger.error(f"All {self.max_retries + 1} attempts failed: {last_exc}")
        if self.on_final_failure:
            self.on_final_failure(last_exc)
        raise last_exc


def retryable(
    max_retries: int = 3,
    backoff_base: float = 3.0,
    jitter: bool = True,
    circuit_breaker=None,
):
    """Decorator version of RetryEngine."""
    engine = RetryEngine(
        max_retries=max_retries,
        backoff_base=backoff_base,
        jitter=jitter,
        circuit_breaker=circuit_breaker,
    )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return engine.execute(func, *args, **kwargs)
        return wrapper

    return decorator
