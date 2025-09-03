"""Tests for CLI security flags (Phase 3)."""

from __future__ import annotations

import builtins
import os
from typing import Any

import run_benchmark


class StubBenchmark:
    """Lightweight stub to avoid running full benchmark during CLI flag tests."""

    def __init__(
        self, submissions_dir: str, results_dir: str, disable_metadata: bool | None = None
    ):
        self.results_dir = results_dir  # minimal usage
        self.submissions_dir = submissions_dir

    def run_single_model(self, model_name: str) -> dict[str, Any]:
        return {"model_name": model_name, "overall_score": 0, "total_possible": 0, "prompts": {}}

    def _generate_comparison(self, models: dict[str, Any]) -> dict[str, Any]:
        return {"ranking": []}

    def _save_results(self, results: dict[str, Any]) -> None:
        return None


def _patch_benchmark(monkeypatch):
    monkeypatch.setattr(run_benchmark, "AICodeBenchmark", StubBenchmark)


def test_security_banner_default(monkeypatch, capsys, tmp_path):
    """Default run prints security status with sandbox enabled (no UNSAFE env var)."""
    _patch_benchmark(monkeypatch)
    args = [
        "--model",
        "dummy",
        "--submissions-dir",
        str(tmp_path / "submissions"),
        "--results-dir",
        str(tmp_path / "results"),
        "--quiet",
    ]
    exit_code = run_benchmark.main(args)
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Sandboxing:" in captured
    assert "ENABLED" in captured  # default should be enabled
    assert os.environ.get("AIBUGBENCH_UNSAFE") not in {"true", "1"}


def test_unsafe_requires_confirmation_decline(monkeypatch, capsys, tmp_path):
    """--unsafe without confirmation aborts execution and does not set env."""
    _patch_benchmark(monkeypatch)
    monkeypatch.setattr(builtins, "input", lambda _="": "no")
    args = [
        "--model",
        "dummy",
        "--submissions-dir",
        str(tmp_path / "submissions"),
        "--results-dir",
        str(tmp_path / "results"),
        "--unsafe",
        "--quiet",
    ]
    # Ensure clean env
    os.environ.pop("AIBUGBENCH_UNSAFE", None)
    exit_code = run_benchmark.main(args)
    _ = capsys.readouterr()
    assert exit_code == 1
    assert os.environ.get("AIBUGBENCH_UNSAFE") is None


def test_unsafe_confirmation_accept(monkeypatch, capsys, tmp_path):
    """--unsafe with confirmation sets env and continues."""
    _patch_benchmark(monkeypatch)
    monkeypatch.setattr(builtins, "input", lambda _="": "yes")
    args = [
        "--model",
        "dummy",
        "--submissions-dir",
        str(tmp_path / "submissions"),
        "--results-dir",
        str(tmp_path / "results"),
        "--unsafe",
        "--quiet",
    ]
    os.environ.pop("AIBUGBENCH_UNSAFE", None)
    exit_code = run_benchmark.main(args)
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Sandboxing:" in captured
    assert os.environ.get("AIBUGBENCH_UNSAFE") == "true"


def test_allow_network_sets_env(monkeypatch, capsys, tmp_path):
    """--allow-network sets AIBUGBENCH_ALLOW_NETWORK env variable."""
    _patch_benchmark(monkeypatch)
    args = [
        "--model",
        "dummy",
        "--submissions-dir",
        str(tmp_path / "submissions"),
        "--results-dir",
        str(tmp_path / "results"),
        "--allow-network",
        "--quiet",
    ]
    os.environ.pop("AIBUGBENCH_ALLOW_NETWORK", None)
    exit_code = run_benchmark.main(args)
    _ = capsys.readouterr()
    assert exit_code == 0
    assert os.environ.get("AIBUGBENCH_ALLOW_NETWORK") == "true"


def test_trusted_model_skips_confirmation(monkeypatch, capsys, tmp_path):
    """--unsafe with --trusted-model skips prompt and proceeds."""
    _patch_benchmark(monkeypatch)
    # If input were called, it would raise (no patch), so absence of patch ensures skip.
    args = [
        "--model",
        "dummy",
        "--submissions-dir",
        str(tmp_path / "submissions"),
        "--results-dir",
        str(tmp_path / "results"),
        "--unsafe",
        "--trusted-model",
        "--quiet",
    ]
    os.environ.pop("AIBUGBENCH_UNSAFE", None)
    exit_code = run_benchmark.main(args)
    _ = capsys.readouterr()
    assert exit_code == 0
    assert os.environ.get("AIBUGBENCH_UNSAFE") == "true"


def teardown_module(module):
    """Cleanup env vars set during tests to avoid bleed into other tests."""
    for var in ["AIBUGBENCH_UNSAFE", "AIBUGBENCH_ALLOW_NETWORK"]:
        os.environ.pop(var, None)
