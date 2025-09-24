"""Security analyzer implementation for Prompt 1."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
import re
from typing import Any

from aibugbench.validation.errors import raise_retriable

MAX_FILE_BYTES = 65536  # 64 KiB cap per file read
MAX_FILES_SCANNED = 200
LINE_LEN_WARN = 120
COMPLEXITY_NODES = (ast.If, ast.For, ast.While, ast.BoolOp)

_ALLOWED_EXTENSIONS = {".py", ".txt", ".md"}
_SNIFF_BYTES = 4096
_PRINTABLE_BYTES = {9, 10, 13} | set(range(32, 127))
_AWS_ACCESS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

# Prevent unused-name lint complaints in modules where constants are parity-only.
_UNUSED = (LINE_LEN_WARN, COMPLEXITY_NODES)


def run(run_dir: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Scan text files for high-signal security findings."""

    root = Path(run_dir)
    checks: list[dict[str, Any]] = []
    files_scanned = 0
    matches_found = 0

    for path in _iter_candidate_files(root):
        if files_scanned >= MAX_FILES_SCANNED:
            break

        data = _read_limited_bytes(path, MAX_FILE_BYTES)
        if not _looks_textual(data):
            continue

        text = data.decode("utf-8", errors="ignore")

        files_scanned += 1
        matches = list(_AWS_ACCESS_KEY.finditer(text))
        match_count = len(matches)
        if match_count:
            matches_found += match_count
            rel_path = _format_relative(path, root)
            message = f"AWS access key pattern detected in {rel_path}"
            checks.append(
                {
                    "id": "sec.aws_key_found",
                    "ok": False,
                    "severity": "error",
                    "message": message,
                }
            )

    stats = {"files_scanned": files_scanned, "matches_found": matches_found}
    return checks, stats


def _iter_candidate_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _ALLOWED_EXTENSIONS:
            continue
        yield path


def _read_limited_bytes(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(limit)
    except OSError as exc:
        raise_retriable(f"transient read failure for {path}", cause=exc)


def _looks_textual(chunk: bytes) -> bool:
    if not chunk:
        return True
    sample = chunk[:_SNIFF_BYTES]
    printable = sum(1 for byte in sample if byte in _PRINTABLE_BYTES)
    return (printable / len(sample)) >= 0.95


def _format_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


__all__ = ["run"]
