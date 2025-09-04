# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `benchmark.platform_validator.PlatformBenchmarkValidator`.

Focused on pure logic methods (no actual benchmark subprocess execution).
"""

from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

from benchmark.platform_validator import CURRENT_PLATFORM, PlatformBenchmarkValidator


@pytest.fixture
def validator(temp_dir: Path) -> PlatformBenchmarkValidator:
    return PlatformBenchmarkValidator(temp_dir)


def _sample_benchmark_results(model_name: str, prompt_scores: dict[str, float]) -> dict:
    # Minimal emulation of latest_results.json structure consumed by extract_scores
    return {
        "platform": CURRENT_PLATFORM,
        "platform_ci": "local-test",
        "execution_time": 0.123,
        "timestamp": "2024-01-01T00:00:00",
        "python_version": "3.x",
        "model_name": model_name,
        "results": {
            "models": {
                model_name: {
                    "prompts": {prompt: {"score": score} for prompt, score in prompt_scores.items()}
                }
            }
        },
        "stdout": "",
        "stderr": "",
    }


@pytest.mark.unit
def test_extract_scores_rounding(validator: PlatformBenchmarkValidator):
    results = _sample_benchmark_results("m1", {"prompt_1": 12.3456, "prompt_2": 7.899})
    scores = validator.extract_scores(results)
    assert scores == {"prompt_1": 12.35, "prompt_2": 7.9}


@pytest.mark.unit
def test_compare_insufficient_data(validator: PlatformBenchmarkValidator):
    comparison = validator.compare_results([_sample_benchmark_results("m", {"prompt_1": 1.0})])
    assert comparison["status"] == "insufficient_data"


@pytest.mark.unit
def test_compare_consistent_and_inconsistent(validator: PlatformBenchmarkValidator):
    r1 = _sample_benchmark_results("m", {"prompt_1": 5.0, "prompt_2": 10.0})
    r2 = _sample_benchmark_results("m", {"prompt_1": 5.0, "prompt_2": 10.0})
    # Simulate different platforms so dictionary keys don't collide
    r1["platform"] = "platform_a"
    r2["platform"] = "platform_b"
    consistent = validator.compare_results([r1, r2])
    assert consistent["status"] == "consistent"

    r3 = _sample_benchmark_results("m", {"prompt_1": 5.0, "prompt_2": 9.0})  # diff on prompt_2
    r3["platform"] = "platform_c"
    inconsistent = validator.compare_results([r1, r3])
    assert inconsistent["status"] == "inconsistent"
    assert any(inc.get("prompt") == "prompt_2" for inc in inconsistent["inconsistencies"])


@pytest.mark.unit
def test_compare_performance_regression(validator: PlatformBenchmarkValidator):
    fast = _sample_benchmark_results("m", {"prompt_1": 1.0})
    slow = _sample_benchmark_results("m", {"prompt_1": 1.0})
    fast["execution_time"] = 1.0
    slow["execution_time"] = 2.0  # 100% slower (>20% threshold)
    fast["platform"] = "fast_platform"
    slow["platform"] = "slow_platform"
    comparison = validator.compare_results([fast, slow])
    assert any(inc.get("type") == "performance" for inc in comparison["inconsistencies"])


@pytest.mark.unit
def test_save_results_writes_file(validator: PlatformBenchmarkValidator, temp_dir: Path):
    data = {"status": "ok", "ts": time.time()}
    path = validator.save_results(data, "unit_platform_results.json")
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["status"] == "ok"
