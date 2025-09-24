"""Minimal env parsing helpers (Phase 0).

These stubs avoid duplicating logic until Phase 1.
"""

from __future__ import annotations

import os

__all__ = [
    "get_env",
    "get_env_bool",
]


def get_env(key: str, default: str | None = None) -> str | None:
    """Fetch raw env var with optional default."""
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Parse truthy env var helpers useful for later phases."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}
