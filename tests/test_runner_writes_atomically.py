"""Behavioural tests around BenchmarkRunner's atomic writes."""

from __future__ import annotations

from aibugbench.io import fs as io_fs
from aibugbench.orchestration.runner import BenchmarkRunner


class _Validator:
    def analyze(self, run_dir: str) -> dict[str, str]:
        return {"run_dir": run_dir, "analysis": "ok"}

    def score(self, analysis: dict[str, str]) -> float:
        return 0.9


def test_runner_uses_atomic_writes(tmp_path):
    def factory(prompt: str) -> _Validator:
        return _Validator()

    runner = BenchmarkRunner(
        validator_factory=factory,
        env={},
        fs=io_fs,
        args={"artifact": str(tmp_path)},
    )

    summary = runner.run_once("prompt-1")
    run_dir = tmp_path / "prompt-1"

    analysis_file = run_dir / "analysis.json"
    summary_file = run_dir / "summary.json"

    assert analysis_file.is_file()
    assert summary_file.is_file()

    leftovers = [p for p in run_dir.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []

    assert summary["artifacts"]["analysis"] == str(analysis_file)
    assert summary["artifacts"]["summary"] == str(summary_file)
