"""Workflow failure taxonomy.

Failures are classified so the platform can decide *how* to recover:
transient failures are retried with backoff, permanent failures abort the
run and leave a clear, auditable error state. Classification can be injected
by the provider or the agent layer.
"""


class WorkflowError(Exception):
    """Base class for every platform failure."""


class TransientFailure(WorkflowError):
    """A recoverable failure: timeout, rate limit, backend hiccup, ..."""


class PermanentFailure(WorkflowError):
    """A non-recoverable failure: invalid prompt, bad request, validation, ..."""
