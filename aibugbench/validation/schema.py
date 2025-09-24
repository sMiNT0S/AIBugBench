"""Schema constants for validation analysis payload (Phase 3 scaffolding)."""

from __future__ import annotations

from typing import Any

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_ERROR = "error"
SEVERITIES: tuple[str, ...] = (
    SEVERITY_INFO,
    SEVERITY_WARN,
    SEVERITY_ERROR,
)

CHECKS_KEY = "checks"
STATS_KEY = "stats"
ARTIFACTS_KEY = "artifacts"


def is_valid_analysis_v1(analysis: dict[str, Any]) -> tuple[bool, list[str]]:
    """Placeholder schema validator; implemented in Phase 3.C."""

    return False, ["UNIMPLEMENTED"]


__all__ = [
    "ARTIFACTS_KEY",
    "CHECKS_KEY",
    "SEVERITIES",
    "SEVERITY_ERROR",
    "SEVERITY_INFO",
    "SEVERITY_WARN",
    "STATS_KEY",
    "is_valid_analysis_v1",
]
