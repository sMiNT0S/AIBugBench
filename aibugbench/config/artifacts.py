"""Artifact directory resolution utilities.

`choose_artifact_path()` applies precedence *args* ➜ *env* ➜ *default* while
ignoring empty / whitespace-only inputs.  Returned paths are absolute and the
containing directory is ensured to exist via :func:`ensure_dir`.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aibugbench.io.paths import project_root

__all__ = [
    "choose_artifact_path",
    "ensure_dir",
]

_StrPath = str | Path


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def ensure_dir(p: _StrPath) -> Path:
    """Return *p* as an absolute directory, creating parents if needed."""
    path = Path(p).expanduser()
    if not path.is_absolute():
        path = project_root() / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def choose_artifact_path(
    args: Mapping[str, Any],
    env: Mapping[str, str],
    default: str | None = None,
) -> str:
    """Return preferred artifact directory (absolute path).

    Parameters
    ----------
    args:
        Parsed CLI arguments (e.g. from vars(argparse.Namespace)). Only the
        ``artifact`` key is consulted.
    env:
    Environment mapping (``os.environ`` or a stand-in) from which the
        ``ARTIFACT`` variable may be read.
    default:
        Optional fallback directory string (may be relative to project root).
    """
    path_str = _clean(args.get("artifact")) or _clean(env.get("ARTIFACT")) or _clean(default)

    if path_str is None:
        # Final fallback under the project root.
        path_str = str(project_root() / "artifacts")

    return str(ensure_dir(path_str))
