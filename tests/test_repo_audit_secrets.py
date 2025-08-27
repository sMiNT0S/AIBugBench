"""Repo audit secret_scan: detects real secrets, ignores placeholders/no-sec comments."""
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
