"""Adapter that makes legacy validation code conform to the new `Validator` Protocol.

During Phase 0 this simply returns dummy values when the true legacy helpers
are not present. Later phases will import the real logic once the refactor is
finished.
"""

from __future__ import annotations

from typing import Any

from aibugbench.validation.base import Validator

# Attempt to locate legacy helpers; tolerate absence so that Phase 0 tests run.
try:
    from validation.validators import analyze_run, score_result  # type: ignore
except ImportError:  # pragma: no cover - legacy helpers not importable in some envs

    def analyze_run(run_dir: str) -> dict[str, Any]:
        return {}

    def score_result(analysis: dict[str, Any]) -> float:
        return 0.0


class LegacyValidatorAdapter(Validator):
    def analyze(self, run_dir: str) -> dict[str, Any]:  # type: ignore[override]
        return analyze_run(run_dir)

    def score(self, analysis: dict[str, Any]) -> float:  # type: ignore[override]
        return float(score_result(analysis))


__all__ = ["LegacyValidatorAdapter"]
