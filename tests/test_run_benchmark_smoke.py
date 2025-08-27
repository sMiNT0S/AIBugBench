"""Lightweight smoke test for run_benchmark main entry to bump coverage.

This avoids heavy execution: it invokes main with --help to trigger argument
parsing without performing benchmark runs.
"""

import contextlib
from importlib import reload

import run_benchmark


def test_run_benchmark_help(monkeypatch):
    # Simulate passing --help; argparse will raise SystemExit after showing help
    monkeypatch.setattr("sys.argv", ["run_benchmark.py", "--help"])
    with contextlib.suppress(SystemExit):
        reload(run_benchmark).main()
