"""Prompt 1 validator scaffolding for Phase 3."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class Prompt1Validator:
    """Placeholder validator; full implementation lands in Phase 3.C."""

    def __init__(self, *, env: Mapping[str, str]) -> None:
        self._env = dict(env)

    def analyze(self, run_dir: str) -> dict[str, Any]:
        """Produce the analysis payload for Prompt 1."""

        raise NotImplementedError("Phase 3.C will implement analyze()")

    def score(self, analysis: dict[str, Any]) -> float:
        """Compute the Prompt 1 score from the analysis payload."""

        raise NotImplementedError("Phase 3.C will implement score()")


__all__ = ["Prompt1Validator"]
