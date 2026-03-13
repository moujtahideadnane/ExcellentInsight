"""Circuit breaker implementation for external service calls.

Prevents cascading failures by temporarily blocking calls to failing services.
Inspired by Martin Fowler's Circuit Breaker pattern.
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Optional, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failing, requests blocked immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open and blocks a call."""

    pass


class CircuitBreaker:
    """Circuit breaker for async functions.

    Tracks failure rate and opens circuit when threshold is exceeded.
    After recovery timeout, allows a test request (half-open state).
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker",
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before testing recovery (half-open)
            expected_exception: Exception type to count as failure
            name: Name for logging/monitoring
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Any exception from func (if circuit allows call)
        """
        # Check if circuit is open
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time and time.time() - self._last_failure_time >= self.recovery_timeout:
                logger.info(
                    "circuit_breaker_half_open",
                    name=self.name,
                    failure_count=self._failure_count,
                )
                self._state = CircuitState.HALF_OPEN
            else:
                logger.warning(
                    "circuit_breaker_blocked_call",
                    name=self.name,
                    failure_count=self._failure_count,
                )
                raise CircuitBreakerOpen(f"Circuit breaker '{self.name}' is OPEN after {self._failure_count} failures")

        # Try to execute function
        try:
            result = await func(*args, **kwargs)

            # Success - reset failure count and close circuit
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "circuit_breaker_recovered",
                    name=self.name,
                    previous_failures=self._failure_count,
                )
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            return result

        except self.expected_exception as e:
            # Failure - increment count and potentially open circuit
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                logger.error(
                    "circuit_breaker_opened",
                    name=self.name,
                    failure_count=self._failure_count,
                    error=str(e),
                )
                self._state = CircuitState.OPEN
            else:
                logger.warning(
                    "circuit_breaker_failure",
                    name=self.name,
                    failure_count=self._failure_count,
                    threshold=self.failure_threshold,
                    error=str(e),
                )

            # Re-raise the original exception
            raise


def with_timeout(timeout_seconds: float):
    """Decorator to add timeout to async functions.

    Args:
        timeout_seconds: Maximum execution time in seconds

    Usage:
        @with_timeout(30.0)
        async def my_func():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                func_name = getattr(func, "__name__", "unknown")
                logger.error(
                    "function_timeout",
                    function=func_name,
                    timeout_seconds=timeout_seconds,
                )
                raise TimeoutError(f"Function '{func_name}' exceeded timeout of {timeout_seconds}s") from None

        return wrapper

    return decorator
