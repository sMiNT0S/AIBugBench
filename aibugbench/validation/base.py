"""Validation contract definitions (Protocol stubs)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

__all__ = ["Validator"]


@runtime_checkable
class Validator(Protocol):
    def analyze(self, run_dir: str) -> dict[str, Any]: ...
    def score(self, analysis: dict[str, Any]) -> float: ...
