"""Validator factory scaffolding for Phase 3."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import os

from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter
from aibugbench.validation.base import Validator
from aibugbench.validation.impl.prompt1 import Prompt1Validator
from aibugbench.validation.impl.prompt2 import Prompt2Validator

_PROMPT_MAP: dict[str, Callable[[Mapping[str, str]], Validator]] = {
    "p1": lambda env: Prompt1Validator(env=env),
}


def make_validator(prompt_id: str, *, env: Mapping[str, str]) -> Validator:
    """Return the validator implementation for the given prompt identifier."""

    if prompt_id == "p2":
        flag = os.environ.get("USE_LEGACY_PROMPT2", "")
        if flag.lower() in {"1", "true", "yes"}:
            return LegacyValidatorAdapter(prompt_id=prompt_id, env=env)
        return Prompt2Validator()

    factory = _PROMPT_MAP.get(prompt_id)
    if factory is None:
        return LegacyValidatorAdapter(prompt_id=prompt_id, env=env)
    return factory(env)


__all__ = ["make_validator"]
