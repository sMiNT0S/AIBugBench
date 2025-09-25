"""Error taxonomy definitions for validator implementations."""

from __future__ import annotations

from typing import NoReturn


class ValidationError(Exception):
    """Non-retriable validation failure (schema/invariant breach)."""


class SchemaError(ValidationError):
    """Raised when validator output violates the analysis schema."""


class RetriableError(Exception):
    """Transient failure eligible for runner retries."""


def raise_retriable(message: str, *, cause: Exception | None = None) -> NoReturn:
    """Raise :class:`RetriableError` with an optional chained *cause*."""

    if cause is None:
        raise RetriableError(message)
    raise RetriableError(message) from cause


__all__ = ["RetriableError", "SchemaError", "ValidationError", "raise_retriable"]
