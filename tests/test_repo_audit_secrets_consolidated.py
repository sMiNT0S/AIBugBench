"""Consolidated tests for validation.repo_audit_enhanced.secret_scan.

Covers:
1. Detection of a real-looking secret token.
2. Skipping of placeholders / lines explicitly marked with `nosec`.
3. Early termination / hit cap behavior (20 findings) for noisy files.

Rationale: Formerly split across two small modules producing extra collection
overhead. Merged to reduce test startup time while preserving assertion
specificity and coverage.
"""

from pathlib import Path

import pytest

from validation.repo_audit_enhanced import secret_scan


@pytest.mark.unit
def test_secret_scan_detects_token(temp_dir: Path):
    real = temp_dir / "code.py"
    real.write_text("API_KEY = 'ABCD1234EFGH5678IJKLmnop'\n", encoding="utf-8")

    hits = secret_scan([real])
    assert hits, "Expected at least one secret hit"
    assert str(real) in hits[0]


@pytest.mark.unit
def test_secret_scan_skips_placeholder_and_nosec(temp_dir: Path):
    placeholder = temp_dir / "fake.py"
    placeholder.write_text(
        "# nosec example placeholder token: API_KEY='YOUR_API_KEY_REPLACE_THIS_1234567890'\n",
        encoding="utf-8",
    )

    hits = secret_scan([placeholder])
    assert hits == []


@pytest.mark.unit
def test_secret_scan_hit_cap(temp_dir: Path):
    spam = temp_dir / "many_secrets.txt"
    # Generate >30 fake secrets matching patterns (token= / api_key=)
    lines = [f"api_key = 'ABCDEFGHIJKLMNOPQRST{i:02d}'\n" for i in range(35)]
    spam.write_text("".join(lines), encoding="utf-8")

    hits = secret_scan([spam])
    assert len(hits) == 20  # capped
    assert all(str(spam) in h for h in hits)
