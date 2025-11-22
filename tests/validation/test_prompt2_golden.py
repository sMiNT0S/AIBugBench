# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Golden test ensuring Prompt2Validator matches legacy behaviour."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from aibugbench.validation.impl.prompt2 import Prompt2Validator

REFERENCE_DIR = Path("submissions/reference_implementations/example_model")
REFERENCE_YAML = REFERENCE_DIR / "prompt_2_config_fixed.yaml"
REFERENCE_JSON = REFERENCE_DIR / "prompt_2_config.json"
LEGACY_FIXTURE = Path("tests/fixtures/prompt2/legacy_analysis.json")
# Fixture captured from the legacy monolithic validator; see tests/fixtures/prompt2/README.md


@pytest.mark.skipif(
    not (REFERENCE_YAML.exists() and REFERENCE_JSON.exists() and LEGACY_FIXTURE.exists()),
    reason="Reference Prompt 2 fixtures missing.",
)
def test_prompt2_validator_matches_legacy(tmp_path: Path):
    """New validator must align with reference baseline behaviour."""
    with LEGACY_FIXTURE.open(encoding="utf-8") as handle:
        legacy_analysis = json.load(handle)

    run_dir = tmp_path
    yaml_path = run_dir / "prompt_2_config_fixed.yaml"
    json_path = run_dir / "prompt_2_config.json"
    shutil.copy2(REFERENCE_YAML, yaml_path)
    shutil.copy2(REFERENCE_JSON, json_path)

    modern = Prompt2Validator()
    modern_analysis = modern.analyze(run_dir)

    legacy_score = float(legacy_analysis["score"])
    modern_score = modern.score(modern_analysis)
    assert modern_score == pytest.approx(legacy_score, abs=1e-6)

    modern_breakdown = modern.category_breakdown(modern_analysis)
    legacy_breakdown = {
        key: float(value.get("earned", 0.0)) for key, value in legacy_analysis["detailed_scoring"].items()
    }
    for category, legacy_value in legacy_breakdown.items():
        assert modern_breakdown[category] == pytest.approx(legacy_value, abs=1e-6)

    modern_tests = modern.tests_passed(modern_analysis)
    legacy_tests = {key: bool(value) for key, value in legacy_analysis.get("tests_passed", {}).items()}
    for key, expected in legacy_tests.items():
        assert modern_tests.get(key) == expected

    legacy_passed = bool(legacy_analysis.get("passed"))
    threshold = float(legacy_analysis.get("max_score", 25)) * 0.6
    modern_passed = bool(modern_score >= threshold)
    assert modern_passed == legacy_passed
