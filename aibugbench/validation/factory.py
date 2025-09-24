"""Validator factory scaffolding for Phase 3."""

from __future__ import annotations

from collections.abc import Mapping

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.base import Validator


def make_validator(prompt_id: str, *, env: Mapping[str, str]) -> Validator:
    """Return the validator implementation for the given prompt.

    Phase 3.B placeholder: always route to the legacy adapter.
    """

    _ = (prompt_id, env)  # Silence unused parameters during scaffolding.
    return LegacyValidatorAdapter()


__all__ = ["make_validator"]
