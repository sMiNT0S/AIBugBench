# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Factory routing tests for Prompt 2 validator selection."""

from __future__ import annotations

import os
from unittest import mock

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.factory import make_validator
from aibugbench.validation.impl.prompt2 import Prompt2Validator


def test_factory_returns_prompt2_validator_by_default():
    """Factory routes prompt 2 requests to the new validator without flags."""
    env = {}
    validator = make_validator("p2", env=env)
    assert isinstance(validator, Prompt2Validator)


def test_factory_prompt2_legacy_fallback_via_env():
    """USE_LEGACY_PROMPT2 env toggle should switch back to adapter."""
    env = {}
    with mock.patch.dict(os.environ, {"USE_LEGACY_PROMPT2": "true"}):
        validator = make_validator("p2", env=env)
    assert isinstance(validator, LegacyValidatorAdapter)


def test_factory_nonexistent_prompt_still_uses_legacy():
    """Other unknown prompts continue to route through the legacy adapter."""
    env = {}
    validator = make_validator("p99", env=env)
    assert isinstance(validator, LegacyValidatorAdapter)
