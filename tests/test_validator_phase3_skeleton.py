"""Smoke tests covering Prompt 1 analyzer scaffolding now implemented."""

from __future__ import annotations

from aibugbench.validation.analyzers import maintainability, performance, security


def test_security_run_empty_directory(tmp_path) -> None:
    checks, stats = security.run(str(tmp_path))
    assert checks == []
    assert stats == {"files_scanned": 0, "matches_found": 0}


def test_maintainability_run_empty_directory(tmp_path) -> None:
    checks, stats = maintainability.run(str(tmp_path))
    assert len(checks) == 1
    assert checks[0]["id"] == "maint.too_long_lines"
    assert checks[0]["ok"] is True
    assert stats == {
        "py_file_count": 0,
        "avg_line_length": 0.0,
        "complexity_score": 0,
    }


def test_performance_run_empty_directory(tmp_path) -> None:
    checks, stats = performance.run(str(tmp_path))
    assert len(checks) == 1
    assert checks[0]["id"] == "perf.large_file_detected"
    assert checks[0]["ok"] is True
    assert stats == {
        "total_files_scanned": 0,
        "total_bytes": 0,
        "largest_file_bytes": 0,
    }
