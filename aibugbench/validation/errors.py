"""Error taxonomy placeholders for Phase 3 validators."""

from __future__ import annotations


class ValidationError(Exception):
    """Non-retriable validation failure (schema/invariant breach)."""


class SchemaError(ValidationError):
    """Raised when validator output violates the analysis schema."""


class RetriableError(Exception):
    """Transient failure eligible for runner retries."""


__all__ = ["RetriableError", "SchemaError", "ValidationError"]
