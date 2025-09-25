"""Contract smoke-test for legacy validator adapter."""

from __future__ import annotations

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.base import Validator


def test_validator_contract_smoke():
    v: Validator = LegacyValidatorAdapter()
    analysis = v.analyze(".")
    assert isinstance(analysis, dict)
    assert 0.0 <= v.score(analysis) <= 1.0
