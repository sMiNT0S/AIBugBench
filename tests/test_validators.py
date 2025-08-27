"""Legacy validator test suite removed.

All validator coverage is now in dedicated focused tests:
    - test_validators_parametric.py
    - test_validators_prompt4_golden.py

This stub intentionally left in place to preserve historical path; it is skipped.
"""

import pytest


@pytest.mark.skip(reason="Legacy validator tests superseded; see parametric + golden files")
def test_validators_legacy_placeholder():
        assert True
