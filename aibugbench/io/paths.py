"""Shared path utilities.

* `project_root()` - ascend from *start* (defaults to `cwd`) looking for a
  marker (``.git`` directory **or** ``pyproject.toml`` file).
* `artifacts_dir()` - default location for artifacts (``<root>/artifacts``).
* `results_dir()`   - default location for results   (``<root>/results``).

These helpers are deliberately simple and have no side-effects beyond basic
filesystem inspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

__all__ = [
    "artifacts_dir",
    "project_root",
    "results_dir",
]

_MARKERS: Final[set[str]] = {".git", "pyproject.toml"}


def _is_fs_root(path: Path) -> bool:
    return path.parent == path


def project_root(start: Path | None = None) -> Path:
    """Return the repository root path.

    Walk up from *start* (default: ``Path.cwd()``) until a marker is found.
    Raises :class:`FileNotFoundError` if no marker is located.
    """
    cur = (start or Path.cwd()).resolve()
    while True:
        for marker in _MARKERS:
            if (cur / marker).exists():
                return cur
        if _is_fs_root(cur):
            raise FileNotFoundError(
                "Unable to locate project root (looked for .git or pyproject.toml)"
            )
        cur = cur.parent


def artifacts_dir() -> Path:
    """Return `<project_root>/artifacts`, creating directory if missing."""
    p = project_root() / "artifacts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def results_dir() -> Path:
    """Return `<project_root>/results`, creating directory if missing."""
    p = project_root() / "results"
    p.mkdir(parents=True, exist_ok=True)
    return p
