"""Factory dispatch tests for validator selection."""

from __future__ import annotations

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.factory import make_validator
from aibugbench.validation.impl.prompt1 import Prompt1Validator


def test_factory_returns_prompt1_for_known_prompt() -> None:
    env = {"REGION": "us-east-1"}
    validator = make_validator("p1", env=env)

    assert isinstance(validator, Prompt1Validator)
    assert env == {"REGION": "us-east-1"}


def test_factory_falls_back_to_legacy_for_unknown_prompt() -> None:
    env = {"LEGACY": "1"}
    validator = make_validator("legacy", env=env)

    assert isinstance(validator, LegacyValidatorAdapter)
    assert validator._prompt_id == "legacy"
    assert validator._env == {"LEGACY": "1"}
    assert env == {"LEGACY": "1"}


def test_factory_does_not_leak_env_between_calls() -> None:
    env_a = {"A": "1"}
    env_b = {"B": "2"}

    validator_a = make_validator("p1", env=env_a)
    validator_b = make_validator("p1", env=env_b)

    assert isinstance(validator_a, Prompt1Validator)
    assert isinstance(validator_b, Prompt1Validator)
    assert validator_a is not validator_b
    assert env_a == {"A": "1"}
    assert env_b == {"B": "2"}
