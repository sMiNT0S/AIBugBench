"""Utility helpers (extracted from legacy code).

Currently provides:
* unicode_safety
* gitmeta
"""

from __future__ import annotations

from .gitmeta import resolve_git_commit
from .unicode_safety import is_unicode_safe, safe_print

__all__ = [
    "is_unicode_safe",
    "resolve_git_commit",
    "safe_print",
]
