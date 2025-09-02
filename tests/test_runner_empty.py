"""Runner edge-case: empty submissions directory handled gracefully."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.integration
def test_runner_empty_submissions_dir(temp_dir: Path):
    empty_dir = temp_dir / "submissions"
    empty_dir.mkdir()
    result = subprocess.run(  # noqa: S603  # CLI empty submissions test - safe command
        [
            sys.executable,
            "run_benchmark.py",
            "--submissions-dir",
            str(empty_dir),
            "--results-dir",
            str(temp_dir / "results"),
            "--quiet",
        ],
        text=True,
        capture_output=True,
    )
    # Should not crash hard; exit 0 or 1 acceptable
    assert result.returncode in (0, 1)
    # Expect message indicating no models (heuristic)
    combined = (result.stdout + result.stderr).lower()
    assert "no" in combined and "model" in combined
