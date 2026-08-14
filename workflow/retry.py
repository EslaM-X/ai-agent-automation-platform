"""Retry policy for transient failures.

Deterministic and injectable so the test suite exercises retries without
sleeping: the backoff sequence and the sleep primitive are plain callables.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from core.errors import TransientFailure, WorkflowError


class RetryExhausted(WorkflowError):
    """Raised when a transient failure outlives `max_attempts`.

    Carries the underlying cause and how many attempts were actually used so
    callers can record precise retry accounting.
    """

    def __init__(self, cause: WorkflowError, attempts: int):
        self.cause = cause
        self.attempts = attempts
        super().__init__(f"{cause} (after {attempts} attempts)")


@dataclass
class RetryPolicy:
    """Run a callable up to `max_attempts`, retrying transient failures.

    Returns `(result, attempts_used)` on success. Permanent failures raise
    the original exception immediately; exhausted transient failures raise
    `RetryExhausted` carrying the attempts count.
    """

    max_attempts: int = 3
    base_delay: float = 0.25

    def backoff(self, attempt: int) -> float:
        """Exponential backoff for a zero-indexed attempt."""
        return self.base_delay * (2**attempt)

    def run(
        self,
        fn: Callable[[], object],
        sleep: Callable[[float], None] = time.sleep,
        retryable: Callable[[WorkflowError], bool] | None = None,
    ) -> tuple[object, int]:
        if retryable is None:

            def retryable(exc: WorkflowError) -> bool:
                return isinstance(exc, TransientFailure)

        attempts = 0
        last: WorkflowError | None = None
        while attempts < self.max_attempts:
            attempts += 1
            try:
                return fn(), attempts
            except WorkflowError as exc:
                last = exc
                if not retryable(exc):
                    raise
                if attempts >= self.max_attempts:
                    raise RetryExhausted(exc, attempts) from exc
                sleep(self.backoff(attempts - 1))
        raise RetryExhausted(last, attempts)  # pragma: no cover - unreachable by construction
