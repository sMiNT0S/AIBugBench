"""Maintainability analyzer implementation for Prompt 1."""

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


def run(run_dir: str) -> tuple[list[dict[str, Any]], dict[str, float | int]]:
    """Compute basic maintainability indicators for Python files."""

    root = Path(run_dir)
    checks: list[dict[str, Any]] = []

    py_file_count = 0
    total_line_length = 0
    total_line_count = 0
    complexity_score = 0

    for path in _iter_python_files(root):
        if py_file_count >= MAX_FILES_SCANNED:
            break

        text = _read_text(path)

        py_file_count += 1
        lines = text.splitlines()
        total_line_count += len(lines)
        total_line_length += sum(len(line) for line in lines)
        complexity_score += _count_complexity(text)

    avg_line_length = float(total_line_length) / total_line_count if total_line_count else 0.0
    ok = avg_line_length <= LINE_LEN_WARN or py_file_count == 0
    if py_file_count == 0:
        message = "No Python files scanned"
    elif ok:
        message = f"Average Python line length {avg_line_length:.1f} chars within {LINE_LEN_WARN}"
    else:
        message = f"Average Python line length {avg_line_length:.1f} chars exceeds {LINE_LEN_WARN}"

    checks.append(
        {
            "id": "maint.too_long_lines",
            "ok": ok,
            "severity": "warn",
            "message": message,
        }
    )

    stats: dict[str, float | int] = {
        "py_file_count": py_file_count,
        "avg_line_length": float(avg_line_length),
        "complexity_score": int(complexity_score),
    }

    return checks, stats


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.is_file():
            yield path


def _read_text(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(MAX_FILE_BYTES)
    except OSError as exc:
        raise_retriable(f"transient read failure for {path}", cause=exc)


def _count_complexity(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    return sum(1 for node in ast.walk(tree) if isinstance(node, COMPLEXITY_NODES))


__all__ = ["run"]
