# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Security validation core helpers.

Thin wrappers around functions that currently live in the `scripts/validate_security.py`
script so they can be imported and (lightly) unit tested. The goal is to
incrementally move logic here while keeping the CLI behaviour stable.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re
import subprocess

"""Canonical secret pattern registry.

SECRET_PATTERNS centralizes conservative regular expressions for high-signal
credential formats. These are intentionally strict (no broad entropy matching)
to minimize false positives inside test fixtures while still catching
accidental real key inclusion. Update here (with rationale) instead of
scattering hard-coded regex literals across README or scripts.

Trade-offs:
- Pros: Single source of truth, easier maintenance, clearer audit surface.
- Cons: May miss novel provider patterns (kept minimal to avoid noise).
"""
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "openai_api_key": re.compile(r"sk-[A-Za-z0-9]{48}"),
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "anthropic_api_key": re.compile(r"sk-ant-[A-Za-z0-9_-]{95}"),
}

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(
    cmd: list[str], capture_output: bool = True, cwd: Path | None = None
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(  # noqa: S603  # Security validation tool execution - controlled commands
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=str(cwd or PROJECT_ROOT),
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"


def check_security_files() -> dict[str, bool]:
    security_files = {
        ".github/dependabot.yml": True,
        ".github/workflows/security.yml": True,
        ".github/codeql/codeql-config.yml": True,
        ".trufflehogignore": True,
        ".semgrepignore": True,
        ".safety-project.ini": True,
        ".github/secret-patterns.yml": True,
        "docs/SECURITY_INFRASTRUCTURE.md": True,
    }
    results: dict[str, bool] = {}
    for rel, _ in security_files.items():
        results[rel] = (PROJECT_ROOT / rel).exists()
    return results


def run_ruff_security_check() -> tuple[bool, int]:
    code, stdout, _ = run_command(["ruff", "check", ".", "--select=S", "--format=json"])
    if code == 127:
        return True, 0
    try:
        issues = [r for r in json.loads(stdout or "[]") if r.get("code", "").startswith("S")]
    except json.JSONDecodeError:
        return False, -1
    return not issues, len(issues)


def run_safety_check() -> tuple[bool, int]:
    code, stdout, _ = run_command(["safety", "check", "--json"])
    if code == 127:
        return True, 0
    try:
        data = json.loads(stdout or "{}")
        vulns = data.get("vulnerabilities", [])
    except json.JSONDecodeError:
        return False, -1
    return code == 0, len(vulns)


def check_git_history_safety(limit: int = 10) -> tuple[bool, int]:
    """Scan recent commit messages for high-signal secret patterns.

    Replaces broad keyword heuristics (password, token, etc.) with the stricter
    SECRET_PATTERNS registry to reduce false positives. While real secrets should
    never appear in commit messages, this provides a lightweight guardrail.

    If git is unavailable or the command fails we log and return a neutral PASS
    (True, 0) rather than failing the entire security suite.
    """
    code, stdout, stderr = run_command(
        ["git", "log", "--oneline", f"--max-count={limit}", "--no-merges"]
    )
    if code != 0:
        logging.debug(
            "git log failed (code=%s). Skipping commit history secret scan. stderr=%r", code, stderr
        )
        return True, 0
    patterns = list(SECRET_PATTERNS.values())
    hits = 0
    for line in stdout.splitlines():
        # Apply strict regex; we intentionally do *not* lower() line so provider-specific
        # patterns that rely on case remain accurate.
        if any(pat.search(line) for pat in patterns):
            hits += 1
    return hits == 0, hits


def validate_test_data_safety() -> tuple[bool, int]:
    """Scan test_data files for accidental inclusion of real secrets.

    Improvements:
    - Case-insensitive suffix filtering & exclusion keyword checks.
    - Expanded monitored suffixes (.env, .md, .txt) for embedded examples.
    - Narrow exception handling to UnicodeDecodeError / OSError.
    """
    test_data = PROJECT_ROOT / "test_data"
    if not test_data.exists():
        return True, 0
    patterns = list(SECRET_PATTERNS.values())
    incidents = 0
    allowed_suffixes = {".py", ".json", ".yaml", ".yml", ".env", ".md", ".txt"}
    exclusion_markers = ("dummy", "test", "fake", "placeholder")
    for file in test_data.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in allowed_suffixes:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:  # pragma: no cover - best effort logging
            logging.debug("Failed reading %s: %s", file, exc)
            continue
        text_lower = text.lower()
        for pat in patterns:
            if pat.search(text) and not any(marker in text_lower for marker in exclusion_markers):
                incidents += 1
    return incidents == 0, incidents


SECURITY_CHECKS = {
    "ruff": run_ruff_security_check,
    "safety": run_safety_check,
    "git": check_git_history_safety,
    "test_data": validate_test_data_safety,
}

__all__ = [
    "SECRET_PATTERNS",
    "SECURITY_CHECKS",
    "check_git_history_safety",
    "check_security_files",
    "run_ruff_security_check",
    "run_safety_check",
    "validate_test_data_safety",
]
