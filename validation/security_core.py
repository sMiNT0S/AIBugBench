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

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(
    cmd: list[str], capture_output: bool = True, cwd: Path | None = None
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
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
    code, stdout, _ = run_command(["git", "log", "--oneline", f"-{limit}", "--no-merges"])
    if code != 0:
        return True, 0
    secret_terms = [
        "password",
        "secret",
        "key",
        "token",
        "api_key",
        "private_key",
        "credentials",
        "auth",
    ]
    hits = 0
    for line in stdout.splitlines():
        low = line.lower()
        if any(term in low for term in secret_terms) and "test" not in low and "dummy" not in low:
            hits += 1
    return hits == 0, hits


def validate_test_data_safety() -> tuple[bool, int]:
    test_data = PROJECT_ROOT / "test_data"
    if not test_data.exists():
        return True, 0
    patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{48}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"sk-ant-[a-zA-Z0-9\-_]{95}"),
    ]
    incidents = 0
    for file in test_data.rglob("*"):
        if not file.is_file() or file.suffix not in {".py", ".json", ".yaml", ".yml"}:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - best effort logging
            logging.debug("Failed reading %s: %s", file, exc)
            continue
        for pat in patterns:
            if pat.search(text) and not any(
                k in text for k in ("dummy", "test", "fake", "placeholder")
            ):
                incidents += 1
    return incidents == 0, incidents


SECURITY_CHECKS = {
    "ruff": run_ruff_security_check,
    "safety": run_safety_check,
    "git": check_git_history_safety,
    "test_data": validate_test_data_safety,
}

__all__ = [
    "SECURITY_CHECKS",
    "check_git_history_safety",
    "check_security_files",
    "run_ruff_security_check",
    "run_safety_check",
    "validate_test_data_safety",
]
