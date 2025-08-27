"""Tests secret_scan hit cap to ensure early termination at 20 findings."""
from pathlib import Path

import pytest

from validation.repo_audit_enhanced import secret_scan


@pytest.mark.unit
def test_secret_scan_hit_cap(temp_dir: Path):
    spam = temp_dir / "many_secrets.txt"
    # Generate >30 fake secrets matching patterns (token= / api_key=)
    lines = []
    for i in range(35):
        lines.append(f"api_key = 'ABCDEFGHIJKLMNOPQRST{i:02d}'\n")
    spam.write_text("".join(lines), encoding="utf-8")

    hits = secret_scan([spam])
    assert len(hits) == 20  # capped
    # Ensure each hit references file and truncated content
    assert all(str(spam) in h for h in hits)
