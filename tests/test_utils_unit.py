"""Unit tests for `benchmark.utils` covering error/edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark import utils


@pytest.mark.unit
def test_validate_submission_structure_missing(temp_dir: Path):
    model_dir = temp_dir / "model_x"
    model_dir.mkdir()
    validation = utils.validate_submission_structure(model_dir)
    # All required files absent -> all False
    assert any(v is False for v in validation.values())
    assert all(
        name.endswith(".py") or name.endswith(".yaml") or name.endswith(".json")
        for name in validation
    )


@pytest.mark.unit
def test_validate_submission_structure_partial(temp_dir: Path):
    model_dir = temp_dir / "model_y"
    model_dir.mkdir()
    # Create two required files with content
    (model_dir / "prompt_1_solution.py").write_text("# impl\nprint('x')\n")
    (model_dir / "prompt_2_config_fixed.yaml").write_text("a: 1\n")
    validation = utils.validate_submission_structure(model_dir)
    assert validation["prompt_1_solution.py"] is True
    assert validation["prompt_2_config_fixed.yaml"] is True
    # Others should be False
    assert validation["prompt_3_transform.py"] is False


@pytest.mark.unit
def test_get_model_statistics_empty():
    stats = utils.get_model_statistics({})
    assert stats == {}


@pytest.mark.unit
def test_get_model_statistics_populated():
    results = {
        "models": {
            "m1": {"percentage": 80, "prompts": {"prompt_1": {"score": 20, "passed": True}}},
            "m2": {"percentage": 60, "prompts": {"prompt_1": {"score": 15, "passed": True}}},
            "m3": {"error": "failed"},  # should count as failure
        }
    }
    stats = utils.get_model_statistics(results)
    assert stats["total_models"] == 3
    assert stats["successful_runs"] == 2
    assert stats["failed_runs"] == 1
    assert stats["average_score"] == 70.0
    assert "prompt_1" in stats["prompt_stats"]
    assert stats["prompt_stats"]["prompt_1"]["max_score"] == 20


@pytest.mark.unit
def test_generate_comparison_chart(temp_dir: Path):
    results = {
        "comparison": {
            "ranking": [
                {"model": "m1", "percentage": 90.0},
                {"model": "m2", "percentage": 75.0},
            ],
            "prompt_performance": {
                "prompt_1": {"best_score": 23.0, "avg_score": 20.0, "pass_rate": 100},
            },
        }
    }
    out = temp_dir / "chart.txt"
    utils.generate_comparison_chart(results, out)
    content = out.read_text(encoding="utf-8")
    assert "COMPARISON CHART" in content
    assert "m1" in content and "m2" in content
