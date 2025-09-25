"""Unit tests for aibugbench.orchestration.runner.BenchmarkRunner internals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from aibugbench.orchestration.runner import BenchmarkRunner, RunStatus


class DummyFS:
    def __init__(self) -> None:
        self.store: dict[Path, Any] = {}

    def atomic_write_json(self, path: str | Path, obj: dict[str, Any]) -> None:
        self.store[Path(path)] = obj

    def load_json(self, path: str | Path) -> Any | None:
        return self.store.get(Path(path))


@dataclass
class DummyValidator:
    prompt: str

    def analyze(self, run_dir: str) -> dict[str, Any]:
        return {"analysis": self.prompt, "dir": run_dir}

    def score(self, analysis: dict[str, Any]) -> float:
        return 0.5


def validator_factory(prompt: str) -> DummyValidator:
    return DummyValidator(prompt)


@pytest.mark.unit
def test_run_once_persists_artifacts_and_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fs = DummyFS()
    # Direct args default_artifact under tmp_path to avoid touching repo
    args = {"artifact": str(tmp_path / "artifacts")}
    runner = BenchmarkRunner(
        validator_factory=validator_factory,
        env={},
        fs=fs,
        args=args,
        default_artifact=str(tmp_path / "artifacts"),
        max_workers=1,
        max_retries=0,
    )

    out = runner.run_once("p1")
    assert out["score"] == 0.5
    # Check persisted files via fs store
    run_dir = Path(args["artifact"]) / "p1"
    assert (run_dir / "analysis.json") in fs.store
    assert (run_dir / "summary.json") in fs.store
    # Check checkpoint recorded as success
    checkpoint = fs.store[run_dir / "checkpoint.json"]
    assert checkpoint["status"] == "SUCCEEDED"
    assert checkpoint["attempts"] == 1


@pytest.mark.unit
def test_run_many_skips_succeeded_checkpoints(tmp_path: Path):
    fs = DummyFS()
    args = {"artifact": str(tmp_path / "arts")}
    runner = BenchmarkRunner(validator_factory=validator_factory, env={}, fs=fs, args=args)

    # Pre-populate a successful checkpoint
    p = Path(args["artifact"]) / "pX"
    fs.atomic_write_json(p / "checkpoint.json", {"status": "SUCCEEDED", "summary": {"score": 1.0}})

    results = runner.run_many(["pX", "pY"])  # pX should be skipped, pY executed
    by_prompt = {r.prompt: r for r in results}
    assert by_prompt["pX"].status is RunStatus.SKIPPED
    assert by_prompt["pY"].status is RunStatus.SUCCEEDED


@pytest.mark.unit
def test_execute_with_retries_handles_retriable(tmp_path: Path):
    class RetriableError(Exception):
        retriable = True

    fs = DummyFS()
    args = {"artifact": str(tmp_path / "arts2")}

    # Validator that fails once then succeeds
    class FlakyValidator(DummyValidator):
        called = 0

        def analyze(self, run_dir: str) -> dict[str, Any]:
            type(self).called += 1
            if self.called == 1:
                raise RetriableError("try again")
            return super().analyze(run_dir)

    def factory(prompt: str) -> DummyValidator:
        return FlakyValidator(prompt)

    runner = BenchmarkRunner(validator_factory=factory, env={}, fs=fs, args=args, max_retries=1)
    results = runner.run_many(["pZ"])  # should succeed after retry
    assert results[0].status is RunStatus.SUCCEEDED


@pytest.mark.unit
def test_execute_with_retries_stops_on_max_attempts(tmp_path: Path):
    class HardFailError(Exception):
        retriable = False

    fs = DummyFS()
    args = {"artifact": str(tmp_path / "arts3")}

    class AlwaysFail(DummyValidator):
        def analyze(self, run_dir: str) -> dict[str, Any]:
            raise HardFailError("nope")

    def factory(prompt: str) -> DummyValidator:
        return AlwaysFail(prompt)

    runner = BenchmarkRunner(validator_factory=factory, env={}, fs=fs, args=args, max_retries=1)
    results = runner.run_many(["p1"])
    assert results[0].status is RunStatus.FAILED
