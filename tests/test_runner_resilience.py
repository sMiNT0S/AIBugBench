"""Phase 2.5 resilience tests for BenchmarkRunner."""

from __future__ import annotations

from pathlib import Path

from aibugbench.io import fs as io_fs
from aibugbench.orchestration.runner import (
    BenchmarkRunner,
    RetriableError,
    RunResult,
    RunStatus,
)


class _SimpleValidator:
    def __init__(self, score: float = 0.5) -> None:
        self._score = score

    def analyze(self, run_dir: str) -> dict[str, str]:
        return {"run_dir": run_dir}

    def score(self, analysis: dict[str, str]) -> float:
        return self._score


def test_run_many_skips_completed_prompt(tmp_path):
    artifact_root = Path(tmp_path)
    run_dir = artifact_root / "p1"
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_payload = {
        "status": "ok",
        "prompt": "p1",
        "artifact": str(artifact_root),
        "artifacts": {"summary": str(run_dir / "summary.json")},
        "score": 0.99,
    }
    io_fs.atomic_write_json(run_dir / "summary.json", {"prompt": "p1", "score": 0.99})
    io_fs.atomic_write_json(
        run_dir / "checkpoint.json",
        {
            "prompt": "p1",
            "status": "SUCCEEDED",
            "summary": summary_payload,
            "attempts": 1,
            "error": None,
        },
    )

    def factory(prompt: str):
        if prompt == "p1":
            raise AssertionError("prompt p1 should be skipped")
        return _SimpleValidator(score=0.25)

    runner = BenchmarkRunner(
        validator_factory=factory,
        env={},
        fs=io_fs,
        args={"artifact": str(artifact_root)},
        max_workers=2,
    )

    results = runner.run_many(["p1", "p2"])

    first, second = results
    assert first.status is RunStatus.SKIPPED
    assert first.summary == summary_payload
    assert second.status is RunStatus.SUCCEEDED
    assert second.summary is not None
    assert second.summary["score"] == 0.25


class _FakeClock:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.calls.append(seconds)


class _FlakyValidator:
    def __init__(self) -> None:
        self.invocations = 0

    def analyze(self, run_dir: str) -> dict[str, str]:
        self.invocations += 1
        if self.invocations < 3:
            raise RetriableError("transient failure")
        return {"run_dir": run_dir}

    def score(self, analysis: dict[str, str]) -> float:
        return 0.8


def test_run_many_retries_with_backoff(tmp_path):
    clock = _FakeClock()
    validator = _FlakyValidator()

    def factory(prompt: str):
        assert prompt == "p1"
        return validator

    runner = BenchmarkRunner(
        validator_factory=factory,
        env={},
        fs=io_fs,
        args={"artifact": str(tmp_path)},
        clock=clock,
        max_workers=1,
        max_retries=3,
        backoff_base=0.1,
        backoff_factor=2.0,
        jitter=0.0,
    )

    results = runner.run_many(["p1"])
    (result,) = results

    assert result.status is RunStatus.SUCCEEDED
    assert result.summary is not None
    assert result.summary["score"] == 0.8

    # Two sleeps for the first two failures, deterministic because jitter=0
    assert clock.calls == [0.1, 0.2]

    checkpoint = io_fs.load_json(Path(tmp_path) / "p1" / "checkpoint.json")
    assert checkpoint["status"] == "SUCCEEDED"
    assert checkpoint["attempts"] == 3


def test_run_many_failed_checkpoint_budget(tmp_path):
    artifact_root = Path(tmp_path)
    run_dir = artifact_root / "p1"
    run_dir.mkdir(parents=True, exist_ok=True)

    io_fs.atomic_write_json(
        run_dir / "checkpoint.json",
        {
            "prompt": "p1",
            "status": "FAILED",
            "summary": None,
            "attempts": 3,
            "error": "boom",
        },
    )

    def factory(prompt: str):
        if prompt == "p1":
            raise AssertionError("p1 should not re-run after exhausting retries")
        return _SimpleValidator(score=0.3)

    runner = BenchmarkRunner(
        validator_factory=factory,
        env={},
        fs=io_fs,
        args={"artifact": str(artifact_root)},
        max_workers=2,
        max_retries=2,
    )

    results = runner.run_many(["p1", "p2"])
    first, second = results

    assert first.status is RunStatus.FAILED
    assert first.error == "boom"
    assert second.status is RunStatus.SUCCEEDED
    assert isinstance(second, RunResult)
