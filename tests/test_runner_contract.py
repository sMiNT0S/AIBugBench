"""Contract tests for BenchmarkRunner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aibugbench.orchestration.runner import BenchmarkRunner


class _RecordingFS:
    """Simple in-memory stand-in capturing atomic write calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[Path, dict[str, Any]]] = []

    def atomic_write_json(self, path: str | Path, obj: dict[str, Any]) -> None:
        self.calls.append((Path(path), dict(obj)))

    def load_json(self, path: str | Path) -> Any | None:  # pragma: no cover
        return None


class _StubValidator:
    def __init__(self, score: float = 0.75) -> None:
        self.score_value = score
        self.last_run_dir: str | None = None

    def analyze(self, run_dir: str) -> dict[str, Any]:
        self.last_run_dir = run_dir
        return {"run_dir": run_dir, "analysis": True}

    def score(self, analysis: dict[str, Any]) -> float:
        assert analysis["run_dir"] == self.last_run_dir
        return self.score_value


def test_runner_returns_minimal_summary(tmp_path):
    fs = _RecordingFS()
    validator = _StubValidator(score=0.42)

    def factory(prompt: str) -> _StubValidator:
        assert prompt == "p1"
        return validator

    runner = BenchmarkRunner(
        validator_factory=factory,
        env={},
        fs=fs,
        args={"artifact": str(tmp_path)},
    )

    summary = runner.run_once("p1")

    run_dir = tmp_path / "p1"
    expected_artifact_root = str(tmp_path.resolve())

    assert summary["status"] == "ok"
    assert summary["prompt"] == "p1"
    assert summary["artifact"] == expected_artifact_root
    assert summary["score"] == 0.42
    assert set(summary["artifacts"].keys()) == {"analysis", "summary"}

    recorded_paths = {p.name for p, _ in fs.calls}
    assert recorded_paths == {"analysis.json", "summary.json", "checkpoint.json"}
    assert validator.last_run_dir == str(run_dir)

    analysis_entry = next(obj for path, obj in fs.calls if path.name == "analysis.json")
    summary_entry = next(obj for path, obj in fs.calls if path.name == "summary.json")
    checkpoint_entry = next(obj for path, obj in fs.calls if path.name == "checkpoint.json")

    assert analysis_entry["run_dir"] == str(run_dir)
    assert summary_entry == {"prompt": "p1", "score": 0.42}
    assert checkpoint_entry["status"] == "SUCCEEDED"
    assert checkpoint_entry["summary"]["prompt"] == "p1"
