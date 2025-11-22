# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Contract tests for Prompt2Validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aibugbench.validation.impl.prompt2 import Prompt2Validator
from aibugbench.validation.schema import is_valid_analysis_v1


def _write_pair(tmp_path: Path, *, yaml_text: str, json_obj: dict[str, object]) -> Path:
    yaml_path = tmp_path / "prompt_2_config_fixed.yaml"
    yaml_path.write_text(yaml_text, encoding="utf-8")
    json_path = tmp_path / "prompt_2_config.json"
    json_path.write_text(json.dumps(json_obj), encoding="utf-8")
    return tmp_path


def test_prompt2_analysis_schema_and_score_range(tmp_path: Path):
    """Analysis must satisfy schema v1 and produce scores within [0, 25]."""
    run_dir = _write_pair(
        tmp_path,
        yaml_text=(
            "use_legacy_paths: true\n"
            "paths:\n  data_source: /srv/data\n"
            "validation_rules:\n  min_age_years: 21\n"
            "api_keys:\n  - key: abc\n"
            "feature_flags:\n  enable_email_notifications: false\n"
            "server_settings:\n  port: 8080\n"
        ),
        json_obj={
            "use_legacy_paths": True,
            "paths": {"data_source": "/srv/data"},
            "validation_rules": {"min_age_years": 21},
            "api_keys": [{"key": "abc"}],
            "feature_flags": {"enable_email_notifications": False},
            "server_settings": {"port": 8080},
        },
    )

    validator = Prompt2Validator()
    analysis = validator.analyze(run_dir)
    is_valid, errors = is_valid_analysis_v1(analysis)
    assert is_valid, errors
    score = validator.score(analysis)
    assert 0.0 <= score <= 25.0


def test_prompt2_analysis_is_deterministic(tmp_path: Path):
    """Repeated analyze calls over identical inputs must be deterministic."""
    run_dir = _write_pair(
        tmp_path,
        yaml_text="use_legacy_paths: false\npaths: {}\nvalidation_rules: {}\napi_keys: []\n"
        "feature_flags: {}\nserver_settings: {port: 9000}\n",
        json_obj={
            "use_legacy_paths": False,
            "paths": {},
            "validation_rules": {},
            "api_keys": [],
            "feature_flags": {},
            "server_settings": {"port": 9000},
        },
    )

    validator = Prompt2Validator()
    first = validator.analyze(run_dir)
    second = validator.analyze(run_dir)
    assert first == second
    assert validator.score(first) == pytest.approx(validator.score(second), rel=0, abs=1e-9)


def test_prompt2_score_monotonicity(tmp_path: Path):
    """Improving a failing check should never reduce the computed score."""
    run_dir = _write_pair(
        tmp_path,
        yaml_text=(
            "use_legacy_paths: 'true'\n"
            "paths:\n  data_source: /srv/data\n"
            "validation_rules:\n  min_age_years: '21'\n"
            "api_keys: []\n"
            "feature_flags: {}\n"
            "server_settings:\n  port: '8080'\n"
        ),
        json_obj={
            "use_legacy_paths": "true",
            "paths": {"data_source": "/srv/data"},
            "validation_rules": {"min_age_years": "21"},
            "api_keys": [],
            "feature_flags": {},
            "server_settings": {"port": "8080"},
        },
    )

    validator = Prompt2Validator()
    analysis = validator.analyze(run_dir)
    baseline = validator.score(analysis)

    improved = {
        **analysis,
        "checks": [
            {**check, "ok": True}
            if check.get("id") == "fmt.quality.literal_types"
            else dict(check)
            for check in analysis["checks"]
        ],
    }
    improved_score = validator.score(improved)
    assert improved_score >= baseline


def test_prompt2_score_breakdown_matches_categories(tmp_path: Path):
    """Category totals must align with legacy weight distribution."""
    run_dir = _write_pair(
        tmp_path,
        yaml_text="use_legacy_paths: true\npaths: {}\nvalidation_rules: {}\napi_keys: []\n"
        "feature_flags: {}\nserver_settings: {port: 8080}\n",
        json_obj={
            "use_legacy_paths": True,
            "paths": {},
            "validation_rules": {},
            "api_keys": [],
            "feature_flags": {},
            "server_settings": {"port": 8080},
        },
    )

    validator = Prompt2Validator()
    analysis = validator.analyze(run_dir)
    category_scores = validator._compute_category_scores(analysis)
    assert set(category_scores.keys()) == {
        "syntax",
        "structure",
        "execution",
        "quality",
        "security",
        "performance",
        "maintainability",
    }
    total = sum(category_scores.values())
    assert validator.score(analysis) == pytest.approx(total, rel=0, abs=1e-9)
