"""Golden snapshot tests for Prompt1Validator deterministic outputs."""

from __future__ import annotations

from pathlib import Path

from aibugbench.validation.impl.prompt1 import Prompt1Validator
from tests.test_validator_p1_contract import _build_fixture

_EXPECTED_CHECKS = [
    ("maint.too_long_lines", False, "warn"),
    ("perf.large_file_detected", True, "warn"),
    ("sec.aws_key_found", False, "error"),
]

_EXPECTED_STATS = {
    "avg_line_length": 130.857,
    "complexity_score": 1,
    "files_scanned": 3,
    "largest_file_bytes": 1860,
    "matches_found": 1,
    "py_file_count": 1,
    "total_bytes": 1921,
    "total_files_scanned": 3,
}

_EXPECTED_SCORE = 0.333


def test_prompt1_validator_snapshot(tmp_path: Path) -> None:
    run_dir = _build_fixture(tmp_path)
    validator = Prompt1Validator(env={})

    analysis = validator.analyze(str(run_dir))
    score = validator.score(analysis)

    sorted_checks = sorted(
        (check["id"], bool(check["ok"]), check["severity"]) for check in analysis["checks"]
    )

    stats_snapshot = {
        key: (round(value, 3) if isinstance(value, float) else value)
        for key, value in analysis["stats"].items()
    }

    assert sorted_checks == _EXPECTED_CHECKS
    assert stats_snapshot == _EXPECTED_STATS
    assert round(score, 3) == _EXPECTED_SCORE
