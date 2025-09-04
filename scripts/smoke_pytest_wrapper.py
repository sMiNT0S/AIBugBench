# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Wrapper script to run smoke pytest with redirected artifact/results output.

This avoids modifying the working tree during pre-commit by honoring the
same environment variable cascade implemented in the benchmark code.

Environment precedence for results/artifacts redirection:
1. AIB_RESULTS_DIR
2. AIB_ARTIFACT_DIR / AIBUGBENCH_ARTIFACT_DIR (results subdir appended)
3. Defaults to .git/precommit_artifacts/results

The wrapper ensures directories exist before invoking pytest.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _resolve_results_dir() -> Path:
    env_results = os.getenv("AIB_RESULTS_DIR")
    env_art_root = os.getenv("AIB_ARTIFACT_DIR") or os.getenv("AIBUGBENCH_ARTIFACT_DIR")
    if env_results and env_results.strip():
        return Path(env_results.strip())
    if env_art_root and env_art_root.strip():
        return Path(env_art_root.strip()) / "results"
    return Path(".git/precommit_artifacts/results")


def main() -> int:
    results_dir = _resolve_results_dir()
    # Set the cascade variables explicitly so benchmark code sees them.
    os.environ.setdefault("AIB_RESULTS_DIR", str(results_dir))
    os.environ.setdefault("AIB_ARTIFACT_DIR", str(results_dir.parent))
    os.environ.setdefault("AIBUGBENCH_ARTIFACT_DIR", str(results_dir.parent))
    # Disable auto plugin discovery (speeds up + avoids coverage plugin import issues)
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    results_dir.mkdir(parents=True, exist_ok=True)

    # Run a minimal subset of tests (aligns with previous -k expression)
    # Explicit minimal args (omit coverage enforced in pytest.ini by skipping those plugins)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        "scripts/pytest_smoke.ini",
        "-q",
        "-k",
        "cli or runner",
    ]
    # Fixed argument list (no shell, controlled command)
    proc = subprocess.run(cmd)  # noqa: S603  # fixed command list, no shell
    return proc.returncode


if __name__ == "__main__":  # pragma: no cover - small utility
    raise SystemExit(main())
