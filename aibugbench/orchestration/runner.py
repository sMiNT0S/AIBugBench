"""Benchmark orchestration entry point (Phase 2).

The `BenchmarkRunner` orchestrates a single benchmark execution using the
phase-1 infrastructure modules.  It resolves artifact locations, delegates to
validators, and persists results via atomic writes so the CLI wrapper can
remain a thin façade.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from aibugbench.config.artifacts import choose_artifact_path

__all__ = ["BenchmarkRunner"]

_StrPath = str | Path


class _FS(Protocol):
    def atomic_write_json(self, path: _StrPath, obj: dict[str, Any]) -> None: ...


class BenchmarkRunner:
    """Coordinate a single benchmark execution."""

    def __init__(
        self,
        *,
        validator_factory: Callable[[str], Validator],
        env: Mapping[str, str],
        fs: _FS,
        args: Mapping[str, Any] | None = None,
        default_artifact: str | None = None,
    ) -> None:
        self._validator_factory = validator_factory
        self._env = dict(env)
        self._fs = fs
        self._args = dict(args or {})
        self._default_artifact = default_artifact

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self, prompt: str) -> dict[str, Any]:
        """Execute a single prompt run and return a summary mapping."""
        artifact_root = Path(choose_artifact_path(self._args, self._env, self._default_artifact))
        dry_run = bool(self._args.get("dry_run"))

        summary: dict[str, Any] = {
            "status": "ok",
            "prompt": prompt,
            "artifact": str(artifact_root),
            "artifacts": {},
            "score": 0.0,
        }

        if dry_run:
            return summary

        run_dir = artifact_root / prompt
        run_dir.mkdir(parents=True, exist_ok=True)

        validator = self._validator_factory(prompt)
        analysis = validator.analyze(str(run_dir))
        score = float(validator.score(analysis))

        analysis_path = run_dir / "analysis.json"
        summary_path = run_dir / "summary.json"

        self._fs.atomic_write_json(analysis_path, analysis)
        self._fs.atomic_write_json(summary_path, {"prompt": prompt, "score": score})

        summary["score"] = score
        summary["artifacts"] = {
            "analysis": str(analysis_path),
            "summary": str(summary_path),
        }
        return summary


# Deferred import to avoid cycles
from aibugbench.validation.base import Validator  # noqa: E402
