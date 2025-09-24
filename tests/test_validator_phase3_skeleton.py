"""Phase 3.B scaffolding tests (xfail placeholders)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from aibugbench.validation.analyzers import maintainability, performance, security
from aibugbench.validation.impl.prompt1 import Prompt1Validator


@pytest.mark.parametrize(
    "analyzer",
    [security.run, maintainability.run, performance.run],
)
@pytest.mark.xfail(strict=True, reason="Phase 3 analyzers not yet implemented")
def test_analyzers_placeholder(analyzer: Callable[[str], object], tmp_path) -> None:
    analyzer(str(tmp_path))


@pytest.mark.xfail(strict=True, reason="Prompt1 validator not yet implemented")
def test_prompt1_validator_placeholder(tmp_path) -> None:
    validator = Prompt1Validator(env={})
    validator.analyze(str(tmp_path))


@pytest.mark.xfail(strict=True, reason="Prompt1 score not yet implemented")
def test_prompt1_validator_score_placeholder() -> None:
    validator = Prompt1Validator(env={})
    validator.score({})
