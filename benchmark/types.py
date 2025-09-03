"""Shared TypedDict result shapes for benchmark validators and runner.

Centralizing these shapes ensures a single source of truth for prompt-level
and model-level result contracts across the core pipeline (validators,
runner, comparison utilities). Runtime behavior remains unchanged; this is
purely a typing/structure consolidation.
"""

from __future__ import annotations

from typing import TypedDict


class PromptResult(TypedDict, total=False):
    """Result for a single prompt validation.

    total=False so optional fields (like error/traceback) don't require
    union types everywhere; absent keys are naturally treated as optional.
    """

    # Core success path fields
    passed: bool
    score: float
    max_score: int
    feedback: list[str]
    tests_passed: dict[str, bool]
    detailed_scoring: dict[str, dict[str, float]]

    # Error path augmentation (injected by runner on exception)
    error: str
    traceback: str


class ModelResults(TypedDict, total=False):
    """Aggregated results for a single model over all prompts."""

    model_name: str
    timestamp: str
    prompts: dict[str, PromptResult]
    overall_score: float
    total_possible: int
    percentage: float
    # Error path augmentation (injected by runner on exception)
    error: str


__all__ = ["ModelResults", "PromptResult"]
