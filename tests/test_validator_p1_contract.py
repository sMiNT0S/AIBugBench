"""Contract tests for Prompt1Validator implementation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from aibugbench.validation.impl.prompt1 import Prompt1Validator
from aibugbench.validation.schema import is_valid_analysis_v1

_LONG_SEGMENT = "A" * 160


def _build_fixture(tmp_path: Path) -> Path:
    module = tmp_path / "module.py"
    long_lines = [f'LONG_CONST_{index} = "{_LONG_SEGMENT}"' for index in range(10)]
    function_lines = [
        "def branch(x):",
        "    if x > 0:",
        "        return True",
        "    return False",
    ]
    module.write_text("\n".join(long_lines + function_lines) + "\n", encoding="utf-8", newline="\n")

    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "README.md").write_text(
        "Documentation placeholder\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets" / "leaky.txt").write_text(
        "Credentials AKIA1234567890ABCDE1\n",
        encoding="utf-8",
        newline="\n",
    )

    return tmp_path


@pytest.fixture()
def run_dir(tmp_path: Path) -> Path:
    return _build_fixture(tmp_path)


def test_analyze_returns_schema_valid_payload(run_dir: Path) -> None:
    validator = Prompt1Validator(env={})
    analysis = validator.analyze(str(run_dir))
    ok, errors = is_valid_analysis_v1(analysis)

    assert ok, errors

    score = validator.score(analysis)
    assert 0.0 <= score <= 1.0


def test_score_is_monotonic_over_check_improvements(run_dir: Path) -> None:
    validator = Prompt1Validator(env={})
    analysis = validator.analyze(str(run_dir))
    first_score = validator.score(analysis)

    mutated = deepcopy(analysis)
    for check in mutated["checks"]:
        if not check.get("ok", False):
            check["ok"] = True
            break
    else:
        pytest.skip("fixture did not produce a failing check")

    improved_score = validator.score(mutated)
    assert improved_score >= first_score
