"""Error taxonomy regression tests for Prompt1 + runner integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from aibugbench.io import fs as io_fs
from aibugbench.orchestration.runner import BenchmarkRunner, RunStatus
from aibugbench.validation.errors import SchemaError
from aibugbench.validation.impl import prompt1 as prompt1_mod
from aibugbench.validation.impl.prompt1 import Prompt1Validator
from tests.test_validator_p1_contract import _build_fixture


class _FSAdapter:
    def atomic_write_json(self, path: str | Path, obj: dict[str, Any]) -> None:
        io_fs.atomic_write_json(path, obj)

    def load_json(self, path: str | Path) -> Any:
        return io_fs.load_json(path)


class _RecordingLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def event(self, name: str, **fields: Any) -> None:
        self.events.append((name, dict(fields)))


class _StubClock:
    def __init__(self) -> None:
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


def test_prompt1_invalid_analysis_raises_schema_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def broken_analyzer(run_dir: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return (
            [
                {
                    "id": "broken.check",
                    "ok": True,
                    "severity": "warn",
                    "message": None,
                }
            ],
            {"py_file_count": 1},
        )

    monkeypatch.setattr(prompt1_mod, "_ANALYZERS", (broken_analyzer,))
    validator = Prompt1Validator(env={})

    with pytest.raises(SchemaError):
        validator.analyze(str(tmp_path))


def test_runner_retries_on_transient_io(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original_open = Path.open
    failures = {"count": 0}

    def flaky_open(self: Path, *args: Any, **kwargs: Any):
        mode = str(args[0]) if args else str(kwargs.get("mode", "r"))
        if (
            failures["count"] == 0
            and "r" in mode
            and "b" not in mode
            and self.suffix == ".py"
            and self.name == "module.py"
        ):
            failures["count"] += 1
            raise OSError("simulated transient read")
        return original_open(self, *args, **kwargs)

    logger = _RecordingLogger()
    clock = _StubClock()
    fs_adapter = _FSAdapter()

    runner = BenchmarkRunner(
        validator_factory=lambda prompt: Prompt1Validator(env={}),
        env={},
        fs=fs_adapter,
        args={"artifact": str(tmp_path / "artifacts")},
        clock=clock,
        logger=logger,
        max_retries=1,
        retry_seed=0,
    )

    run_dir = runner._artifact_root_path() / "prompt1"
    run_dir.mkdir(parents=True, exist_ok=True)
    _build_fixture(run_dir)

    monkeypatch.setattr(Path, "open", flaky_open, raising=False)

    results = runner.run_many(["prompt1"])

    assert failures["count"] == 1
    assert any(name == "run.retry" for name, _ in logger.events)
    assert results[0].status is RunStatus.SUCCEEDED
    assert isinstance(results[0].summary, dict)

    # No RetriableError should leak out after retry succeeds.
    for name, fields in logger.events:
        if name == "run.failure":
            pytest.fail(f"unexpected failure event: {fields}")
