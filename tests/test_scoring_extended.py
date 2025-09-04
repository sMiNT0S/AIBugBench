# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Extended tests for BenchmarkScorer to raise coverage.

Covers: calculate_grade boundaries, feedback summary branches, improvement suggestions,
model comparison, and badge generation.
"""

import pytest

from benchmark.scoring import BenchmarkScorer


@pytest.mark.unit
@pytest.mark.parametrize(
    "percentage,expected",
    [
        (96, "A+"),
        (95, "A+"),
        (92, "A"),
        (90, "A"),
        (87, "A-"),
        (85, "A-"),
        (82, "B+"),
        (80, "B+"),
        (77, "B"),
        (75, "B"),
        (72, "B-"),
        (70, "B-"),
        (67, "C+"),
        (65, "C+"),
        (60, "C"),
        (59.9, "F"),
        (10, "F"),
    ],
)
def test_calculate_grade_boundaries(percentage, expected):
    scorer = BenchmarkScorer()
    assert scorer.calculate_grade(percentage) == expected


@pytest.mark.unit
def test_feedback_summary_strengths_and_weaknesses():
    scorer = BenchmarkScorer()
    results = {
        "percentage": 88,
        "prompts": {
            "prompt_1": {"score": 22, "max_score": 25},  # 88% -> strength
            "prompt_2": {"score": 10, "max_score": 25},  # 40% -> weakness
            "prompt_3": {"error": "Runtime failure"},  # error branch
            "prompt_4": {"score": 15, "max_score": 25},  # 60% -> neutral
        },
    }
    feedback = scorer.generate_feedback_summary(results)
    joined = " ".join(feedback)
    assert "Strengths" in joined and "Areas for improvement" in joined
    assert any("Code Refactoring" in f for f in feedback)
    assert any("YAML/JSON Handling" in f for f in feedback)


@pytest.mark.unit
def test_improvement_suggestions_all_prompts():
    scorer = BenchmarkScorer()
    results = {
        "prompts": {
            "prompt_1": {"tests_passed": {"valid_python": False}},
            "prompt_2": {"tests_passed": {"valid_yaml": False}},
            "prompt_3": {"tests_passed": {"no_crash": False}},
            "prompt_4": {"tests_passed": {"uses_requests": False}},
        }
    }
    suggestions = scorer.generate_improvement_suggestions(results)
    assert len(suggestions) == 4
    assert any("syntax" in s.lower() for s in suggestions)


@pytest.mark.unit
def test_improvement_suggestions_none_needed():
    scorer = BenchmarkScorer()
    results = {
        "prompts": {
            "prompt_1": {
                "tests_passed": {
                    "valid_python": True,
                    "runs_successfully": True,
                    "good_structure": True,
                }
            },
            "prompt_2": {"tests_passed": {"valid_yaml": True, "correct_types": True}},
            "prompt_3": {
                "tests_passed": {
                    "no_crash": True,
                    "email_provider": True,
                    "account_tiers": True,
                }
            },
            "prompt_4": {"tests_passed": {"uses_requests": True, "error_handling": True}},
        }
    }
    suggestions = scorer.generate_improvement_suggestions(results)
    assert suggestions == []


@pytest.mark.unit
def test_compare_models_and_badges():
    scorer = BenchmarkScorer()
    all_results = {
        "models": {
            "m1": {
                "overall_score": 90,
                "percentage": 90,
                "prompts": {"prompt_1": {"score": 20, "max_score": 25}},
            },
            "m2": {
                "overall_score": 70,
                "percentage": 70,
                "prompts": {"prompt_1": {"score": 10, "max_score": 25}},
            },
            "m3": {"error": "Failed"},
        }
    }
    cmp = scorer.compare_models(all_results)
    assert cmp["best_overall"]["model"] == "m1"
    assert "prompt_1" in cmp["best_by_prompt"]

    assert scorer.generate_badge(96).startswith("🏆")
    assert scorer.generate_badge(91).startswith("🥇")
    # Mid 80s returns one of the achievement tiers just below top
    assert scorer.generate_badge(85)[0] in {"🥈", "🥉", "🥇"}
    assert scorer.generate_badge(10).startswith("📚")
