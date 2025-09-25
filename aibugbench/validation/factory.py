"""Validator factory scaffolding for Phase 3."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.base import Validator
from aibugbench.validation.impl.prompt1 import Prompt1Validator

_PROMPT_MAP: dict[str, Callable[[Mapping[str, str]], Validator]] = {
    "p1": lambda env: Prompt1Validator(env=env),
}


def make_validator(prompt_id: str, *, env: Mapping[str, str]) -> Validator:
    """Return the validator implementation for the given prompt identifier."""

    try:
        factory = _PROMPT_MAP[prompt_id]
    except KeyError:
        return LegacyValidatorAdapter(prompt_id=prompt_id, env=env)
    return factory(env)


__all__ = ["make_validator"]
