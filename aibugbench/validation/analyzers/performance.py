"""Performance analyzer implementation for Prompt 1."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from aibugbench.validation.errors import raise_retriable

MAX_FILE_BYTES = 65536  # 64 KiB cap per file read
MAX_FILES_SCANNED = 200
LINE_LEN_WARN = 120
COMPLEXITY_NODES = (ast.If, ast.For, ast.While, ast.BoolOp)

_LARGE_FILE_THRESHOLD = 1_000_000  # bytes (~1 MB)


def run(run_dir: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Collect lightweight performance-oriented stats."""

    root = Path(run_dir)
    checks: list[dict[str, Any]] = []

    total_files_scanned = 0
    total_bytes = 0
    largest_file_bytes = 0

    for path in _iter_files(root):
        if total_files_scanned >= MAX_FILES_SCANNED:
            break

        try:
            size = path.stat().st_size
        except OSError as exc:
            raise_retriable(f"transient stat failure for {path}", cause=exc)

        total_files_scanned += 1
        total_bytes += int(size)
        if size > largest_file_bytes:
            largest_file_bytes = int(size)

    ok = largest_file_bytes <= _LARGE_FILE_THRESHOLD or total_files_scanned == 0
    if total_files_scanned == 0:
        message = "No files scanned"
    elif ok:
        message = f"Largest file size {largest_file_bytes} B within {_LARGE_FILE_THRESHOLD}"
    else:
        message = f"Largest file size {largest_file_bytes} B exceeds {_LARGE_FILE_THRESHOLD}"

    checks.append(
        {
            "id": "perf.large_file_detected",
            "ok": ok,
            "severity": "warn",
            "message": message,
        }
    )

    stats = {
        "total_files_scanned": total_files_scanned,
        "total_bytes": total_bytes,
        "largest_file_bytes": largest_file_bytes,
    }

    return checks, stats


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


__all__ = ["run"]
