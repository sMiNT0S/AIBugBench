"""CLI characterization snapshot against Phase-0 stub."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

FIXTURE = Path(__file__).parent / "fixtures" / "golden_summary.json"


def test_cli_smoke(tmp_path):
    cp = subprocess.run(
        [sys.executable, "-m", "aibugbench.run_benchmark", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stderr
    summary_line = next((line for line in cp.stdout.splitlines() if line.startswith("SUMMARY:")), None)
    assert summary_line is not None, "No line starting with 'SUMMARY:' found in CLI output"
    got = json.loads(summary_line.split("SUMMARY:", 1)[1])
    golden = json.loads(FIXTURE.read_text())
    assert set(got.keys()) == set(golden.keys())
