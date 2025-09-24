"""Prompt 1 validator implementation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from aibugbench.validation.analyzers import maintainability, performance, security
from aibugbench.validation.errors import SchemaError
from aibugbench.validation.schema import (
    ARTIFACTS_KEY,
    CHECKS_KEY,
    STATS_KEY,
    is_valid_analysis_v1,
)

Analyzer = Callable[[str], tuple[list[dict[str, Any]], Mapping[str, Any]]]
_ANALYZERS: tuple[Analyzer, ...] = (
    security.run,
    maintainability.run,
    performance.run,
)


class Prompt1Validator:
    """Validator orchestrating Prompt 1 analyzers."""

    def __init__(self, *, env: Mapping[str, str]) -> None:
        self._env = dict(env)

    def analyze(self, run_dir: str) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        stats: dict[str, Any] = {}

        for analyzer in _ANALYZERS:
            analyzer_checks, analyzer_stats = analyzer(run_dir)
            checks.extend(analyzer_checks)
            _merge_stats(stats, analyzer_stats)

        analysis = {
            CHECKS_KEY: checks,
            STATS_KEY: stats,
            ARTIFACTS_KEY: {},
        }

        ok, errors = is_valid_analysis_v1(analysis)
        if not ok:
            detail = "; ".join(errors) if errors else "analysis failed validation"
            raise SchemaError(f"analysis invalid: {detail}")

        return analysis

    def score(self, analysis: dict[str, Any]) -> float:
        checks = analysis.get(CHECKS_KEY, [])
        if not isinstance(checks, list):
            raise SchemaError("analysis missing checks list")

        total = len(checks) or 1
        passed = sum(1 for check in checks if isinstance(check, dict) and bool(check.get("ok")))
        score = passed / total
        if score < 0.0:
            return 0.0
        if score > 1.0:
            return 1.0
        return float(score)


def _merge_stats(target: dict[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in updates.items():
        if (
            key in target
            and isinstance(target[key], (int | float))
            and isinstance(value, (int | float))
        ):
            target[key] = target[key] + value
        else:
            target[key] = value


__all__ = ["Prompt1Validator"]
