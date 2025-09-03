from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

try:
    # Prefer stdlib on newer Pythons
    from typing import ParamSpec  # Python ≥3.10
except ImportError:  # pragma: no cover
    from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")  # instance type for methods (self), if needed


def preserve_sig(fn: Callable[P, R]) -> Callable[P, R]:
    """No-op decorator that preserves the wrapped function's signature for type checkers."""

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)

    return wrapper


def typed_factory(factory: Callable[..., Callable[P, R]]) -> Callable[..., Callable[P, R]]:
    """Identity helper to keep readable types on decorator factories."""
    return factory
