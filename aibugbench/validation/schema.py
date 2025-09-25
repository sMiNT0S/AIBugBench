"""Schema constants for validation analysis payload (Phase 3 scaffolding)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

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


def is_valid_analysis_v1(analysis: object) -> tuple[bool, list[str]]:
    """Validate the structure of an analysis payload."""

    errors: list[str] = []

    if not isinstance(analysis, dict):
        return False, ["analysis must be a dict"]

    analysis_dict = cast(dict[str, Any], analysis)

    checks = analysis_dict.get(CHECKS_KEY)
    if not isinstance(checks, list):
        errors.append("checks must be a list")
        checks_iter: list[Any] = []
    else:
        checks_iter = checks

    for index, item in enumerate(checks_iter):
        prefix = f"checks[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be a dict")
            continue
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        ok_value = item.get("ok")
        if not isinstance(ok_value, bool):
            errors.append(f"{prefix}.ok must be a boolean")
        severity = item.get("severity")
        if severity not in SEVERITIES:
            errors.append(f"{prefix}.severity must be one of {SEVERITIES}")
        message = item.get("message")
        if not isinstance(message, str):
            errors.append(f"{prefix}.message must be a string")

    stats = analysis_dict.get(STATS_KEY)
    if not isinstance(stats, dict):
        errors.append("stats must be a dict")
        stats_items: Iterable[tuple[str, Any]] = []
    else:
        stats_items = stats.items()

    for key, value in stats_items:
        if not isinstance(key, str) or not key:
            errors.append("stats keys must be non-empty strings")
        if not isinstance(value, (int | float)) or isinstance(value, bool):
            errors.append(f"stats[{key!r}] must be numeric")

    artifacts = analysis_dict.get(ARTIFACTS_KEY)
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be a dict")
        artifact_items: Iterable[tuple[str, Any]] = []
    else:
        artifact_items = artifacts.items()

    for key, value in artifact_items:
        if not isinstance(key, str) or not key:
            errors.append("artifacts keys must be non-empty strings")
        if not isinstance(value, str):
            errors.append(f"artifacts[{key!r}] must be strings")

    return (not errors), errors


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
