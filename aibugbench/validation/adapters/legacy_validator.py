"""Adapter that makes legacy validation code conform to the new `Validator` Protocol.

During Phase 0 this simply returns dummy values when the true legacy helpers
are not present. Later phases will import the real logic once the refactor is
finished.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from aibugbench.validation.base import Validator

# Attempt to locate legacy helpers; tolerate absence so that Phase 0 tests run.
try:  # Attempt import of untyped legacy helpers
    from validation.validators import (
        analyze_run as _analyze_run,
        score_result as _score_result,
    )
except ImportError:  # pragma: no cover - legacy helpers not importable in some envs

    def _analyze_run(run_dir: str) -> dict[str, Any]:
        """Stub analyze_run returning empty analysis for Phase 0."""
        return {}

    def _score_result(analysis: dict[str, Any]) -> float:
        """Stub score_result returning neutral score for Phase 0."""
        return 0.0


# Provide typed callables for adapter; cast in case legacy functions are untyped.
analyze_run: Callable[[str], dict[str, Any]] = cast(
    Callable[[str], dict[str, Any]],
    _analyze_run,
)
score_result: Callable[[dict[str, Any]], float] = cast(
    Callable[[dict[str, Any]], float],
    _score_result,
)


class LegacyValidatorAdapter(Validator):
    def analyze(self, run_dir: str) -> dict[str, Any]:
        return analyze_run(run_dir)

    def score(self, analysis: dict[str, Any]) -> float:
        return float(score_result(analysis))


__all__ = ["LegacyValidatorAdapter"]
