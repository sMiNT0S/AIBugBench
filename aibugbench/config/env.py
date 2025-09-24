"""Environment helper utilities.

Robust parsers for boolean / integer / float values plus convenience wrappers
that fall back to sensible defaults when environment variables are unset or
malformed.
"""

from __future__ import annotations

import os
from typing import Final

TRUTHY: Final[set[str]] = {"1", "true", "yes", "on", "y"}
FALSY: Final[set[str]] = {"0", "false", "no", "off", "n"}

__all__ = [
    "FALSY",
    "TRUTHY",
    "get_env",
    "get_env_bool",
    "get_env_float",
    "get_env_int",
]


def get_env(key: str, default: str | None = None) -> str | None:
    """Retrieve *key* from environment, returning *default* if absent."""
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Boolean helpers
# ---------------------------------------------------------------------------


def _parse_bool(value: str) -> bool | None:
    v = value.strip().lower()
    if v in TRUTHY:
        return True
    if v in FALSY:
        return False
    return None


def get_env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key)
    parsed = _parse_bool(val) if val is not None else None
    return parsed if parsed is not None else default


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------


def _parse_int(value: str) -> int | None:
    try:
        return int(value.strip())
    except Exception:
        return None


def get_env_int(key: str, default: int = 0) -> int:
    val = os.environ.get(key)
    parsed = _parse_int(val) if val is not None else None
    return parsed if parsed is not None else default


def _parse_float(value: str) -> float | None:
    try:
        return float(value.strip())
    except Exception:
        return None


def get_env_float(key: str, default: float = 0.0) -> float:
    val = os.environ.get(key)
    parsed = _parse_float(val) if val is not None else None
    return parsed if parsed is not None else default
