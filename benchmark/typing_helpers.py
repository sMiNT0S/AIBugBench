# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Type annotation helpers for the benchmarking framework.

Python 3.13+ provides modern typing features natively.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")  # instance type for methods (self), if needed


def preserve_sig(
    fn: Callable[P, R],
) -> Callable[P, R]:
    """No-op decorator that preserves the wrapped function's signature for type checkers."""

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)

    return wrapper


def typed_factory(
    factory: Callable[..., Callable[P, R]],
) -> Callable[..., Callable[P, R]]:
    """Identity helper to keep readable types on decorator factories."""
    return factory
