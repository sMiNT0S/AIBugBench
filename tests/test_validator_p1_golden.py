"""Golden snapshot tests for Prompt1Validator deterministic outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aibugbench.validation.impl.prompt1 import Prompt1Validator
from tests.test_validator_p1_contract import _build_fixture


def _stable_stats(stats: dict[str, Any]) -> dict[str, int]:
    """Return an OS-agnostic subset of stats for snapshotting."""

    # Convert sizes to KB to dodge CRLF/LF drift
    def _kb(n: int) -> int:
        return (int(n) + 512) // 1024  # round to nearest KB

    out = {
        "py_file_count": int(stats.get("py_file_count", 0)),
        "files_scanned": int(stats.get("files_scanned", 0)),
        "total_files_scanned": int(stats.get("total_files_scanned", 0)),
        "complexity_score": int(stats.get("complexity_score", 0)),
    }
    # Keep sizes, but normalize to KB
    if "largest_file_bytes" in stats:
        out["largest_file_kb"] = _kb(int(stats["largest_file_bytes"]))
    if "total_bytes" in stats:
        out["total_kb"] = _kb(int(stats["total_bytes"]))
    return out


_EXPECTED_CHECKS = [
    ("maint.too_long_lines", False, "warn"),
    ("perf.large_file_detected", True, "warn"),
    ("sec.aws_key_found", False, "error"),
]

_EXPECTED_STATS_BYTES = {
    # Raw bytes here are *only* inputs to normalization.
    "py_file_count": 1,
    "files_scanned": 3,
    "total_files_scanned": 3,
    "complexity_score": 1,
    "largest_file_bytes": 1860,
    "total_bytes": 1921,
}

_EXPECTED_SCORE = 0.333


def test_prompt1_validator_snapshot(tmp_path: Path) -> None:
    # Fixture writer should use newline="\n" to force LF in the created files.
    run_dir = _build_fixture(tmp_path)
    v = Prompt1Validator(env={})
    analysis = v.analyze(str(run_dir))

    checks = analysis["checks"]
    stats = analysis["stats"]

    got_checks = sorted((c["id"], bool(c["ok"]), c["severity"]) for c in checks)
    assert got_checks == sorted(_EXPECTED_CHECKS)

    # Compare stable projection, not raw stats
    got_stats = _stable_stats(stats)
    expected_stats = _stable_stats(_EXPECTED_STATS_BYTES)
    assert got_stats == expected_stats

    # Score snapshot: round to 3 decimals
    assert round(v.score(analysis), 3) == _EXPECTED_SCORE
