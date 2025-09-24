"""Cross-platform filesystem helpers.

This replaces the Phase-0 façade with real implementations that **do not** rely
on legacy modules.  All public function names are preserved so existing imports
continue to work.

Key features
------------
• UTF-8 text I/O with newline normalisation ("\n").
• Parent directory auto-creation on writes.
• Atomic write helpers for text and JSON using `tempfile` + `os.replace`.
• Optional loaders for JSON / TOML / YAML (gracefully degrade if libs missing).
• Minimal, standard-library-only dependencies (YAML optional).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

__all__ = [
    "atomic_write_json",
    "atomic_write_text",
    "load_json",
    "load_toml",
    "load_yaml",
    "read_text",
    "write_text",
]

_StrPath = str | Path

###############################################################################
# Core helpers
###############################################################################


def _to_path(p: _StrPath) -> Path:
    """Return *p* as a `pathlib.Path`, expanding user symbols."""
    return p if isinstance(p, Path) else Path(p).expanduser()


def read_text(path: _StrPath) -> str:
    """Read a UTF-8 text file and normalise line endings to "\n"."""
    p = _to_path(path)
    data = p.read_text(encoding="utf-8", errors="replace")
    # Normalise both CRLF and lone CR to LF so downstream diffing is simpler
    return data.replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: _StrPath, data: str) -> None:
    """Write UTF-8 *data* to *path*, creating parent directories if needed."""
    p = _to_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # `newline="\n"` forces LF endings even on Windows.
    p.write_text(data, encoding="utf-8", newline="\n")


###############################################################################
# Atomic writes
###############################################################################


def _atomic_write(target: Path, data: str, mode: str = "w", encoding: str = "utf-8") -> None:
    """Write *data* to *target* via a temp file then `os.replace` (atomic)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    # Use same dir so os.replace() is atomic on the same filesystem.
    with tempfile.NamedTemporaryFile(
        mode=mode,
        encoding=encoding if "b" not in mode else None,
        delete=False,
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    ) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())  # ensure bytes hit disk before replace
        temp_path = Path(tmp.name)
    os.replace(temp_path, target)


def atomic_write_text(path: _StrPath, data: str) -> None:
    """Atomically write UTF-8 *data* to *path*."""
    _atomic_write(_to_path(path), data, mode="w", encoding="utf-8")


def atomic_write_json(path: _StrPath, obj: Any) -> None:
    """Atomically dump *obj* as pretty JSON (indent=2, sort_keys=True)."""
    json_text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)
    atomic_write_text(path, json_text)


###############################################################################
# Loaders (optional third-party deps allowed but not required)
###############################################################################


def load_json(path: _StrPath) -> Any | None:
    """Return parsed JSON or *None* if file is absent/invalid."""
    p = _to_path(path)
    if not p.exists():
        return None
    try:
        with p.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# TOML support (Python ≥3.11 provides tomllib)
try:  # pragma: no cover - optional
    import tomllib as _tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - tomllib backport not installed
    _tomllib = None


def load_toml(path: _StrPath) -> Any | None:
    if _tomllib is None:
        return None
    p = _to_path(path)
    if not p.exists():
        return None
    try:
        return _tomllib.loads(read_text(p))
    except Exception:
        return None


# YAML support (PyYAML optional)
try:  # pragma: no cover
    import yaml as _yaml
except ModuleNotFoundError:  # pragma: no cover
    _yaml = None


def load_yaml(path: _StrPath) -> Any | None:
    if _yaml is None:
        return None
    p = _to_path(path)
    if not p.exists():
        return None
    try:
        return _yaml.safe_load(read_text(p))
    except Exception:
        return None
