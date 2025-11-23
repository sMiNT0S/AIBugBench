# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Prompt 2 validator implementation."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import yaml

from ..analyzers.format import (
    analyze_json,
    analyze_yaml,
    cross_format,
    quality_checker,
    structure_validator,
)
from ..errors import SchemaError
from ..schema import ARTIFACTS_KEY, CHECKS_KEY, STATS_KEY, is_valid_analysis_v1
from ..utils.file_discovery import find_prompt2_files
from ..utils.result_builder import build_validation_result
from ..utils.scoring_factory import create_prompt2_categories

PASS_THRESHOLD_RATIO = 0.6


class Prompt2Validator:
    """Validate Prompt 2 YAML/JSON correction submissions."""

    category_weights = create_prompt2_categories()
    pass_threshold_ratio: float = PASS_THRESHOLD_RATIO

    @classmethod
    def pass_threshold(cls) -> float:
        """Return the numeric passing score for current category weights."""
        return sum(cls.category_weights.values()) * cls.pass_threshold_ratio

    def __init__(self, *, env: Mapping[str, str] | None = None) -> None:
        self._env = dict(env or {})

    def analyze(self, run_dir_or_yaml: str | Path, json_file: Path | None = None) -> dict[str, Any]:
        """Run format analyzers and assemble a schema v1 compliant analysis."""
        if json_file is None:
            yaml_file, json_file = find_prompt2_files(Path(run_dir_or_yaml))
        else:
            yaml_file = Path(run_dir_or_yaml)
            json_file = Path(json_file)

        analysis = build_validation_result(category_weights=self.category_weights)
        checks: list[dict[str, Any]] = analysis[CHECKS_KEY]
        stats: dict[str, float] = analysis[STATS_KEY]
        artifacts: dict[str, str] = analysis[ARTIFACTS_KEY]

        yaml_checks, yaml_stats = analyze_yaml(yaml_file)
        checks.extend(yaml_checks)
        stats.update(
            {
                f"yaml_{key}": float(value)
                for key, value in yaml_stats.items()
                if isinstance(value, int | float)
            }
        )

        yaml_data: Any = None
        if yaml_file.exists():
            try:
                with open(yaml_file, encoding="utf-8") as handle:
                    yaml_data = yaml.safe_load(handle)
            except yaml.YAMLError:
                yaml_data = None
            except OSError:
                yaml_data = None

        json_checks, json_stats = analyze_json(json_file)
        checks.extend(json_checks)
        stats.update(
            {
                f"json_{key}": float(value)
                for key, value in json_stats.items()
                if isinstance(value, int | float)
            }
        )

        json_data: Any = None
        if json_file.exists():
            try:
                with open(json_file, encoding="utf-8") as handle:
                    json_data = json.load(handle)
            except json.JSONDecodeError:
                json_data = None
            except OSError:
                json_data = None

        structure_stats: dict[str, Any] = {}
        if yaml_data is not None and json_data is not None:
            structure_checks, structure_stats = structure_validator.validate_structure(
                yaml_data, json_data
            )
            checks.extend(structure_checks)
            artifacts["prompt2_structure"] = json.dumps(structure_stats)

            cross_checks, cross_stats = cross_format.compare_formats(
                yaml_data, json_data, expected_keys=structure_validator.EXPECTED_KEYS
            )
            checks.extend(cross_checks)
        else:
            cross_stats = {
                "normalized_changes": 0,
                "matching_keys": 0,
                "total_keys": 0,
            }

        stats["structure_required_keys_yaml"] = float(structure_stats.get("required_keys_yaml", 0))
        stats["structure_required_keys_json"] = float(structure_stats.get("required_keys_json", 0))
        stats["structure_missing_yaml"] = float(len(structure_stats.get("missing_keys_yaml", [])))
        stats["structure_missing_json"] = float(len(structure_stats.get("missing_keys_json", [])))
        stats["structure_shape_matches"] = float(structure_stats.get("shape_matches", 0))
        stats["structure_shape_total"] = float(structure_stats.get("total_shape_checks", 0))
        stats["structure_arrays_scalar_correct"] = float(
            1 if structure_stats.get("arrays_scalar_correct") else 0
        )

        stats["cross_normalized_changes"] = float(cross_stats.get("normalized_changes", 0))
        stats["cross_matching_keys"] = float(cross_stats.get("matching_keys", 0))
        stats["cross_total_keys"] = float(cross_stats.get("total_keys", 0))

        quality_checks, quality_stats = quality_checker.check_quality(
            yaml_file, json_file, yaml_data, json_data
        )
        checks.extend(quality_checks)
        artifacts["prompt2_quality"] = json.dumps(quality_stats)
        stats["quality_indentation_issue_count"] = float(
            len(quality_stats.get("indentation_issues", []))
        )
        stats["quality_literal_issue_count"] = float(len(quality_stats.get("literal_issues", [])))
        stats["quality_duplicate_issue_count"] = float(
            len(quality_stats.get("duplicate_details", []))
        )
        stats["quality_yaml_tabs_detected"] = float(
            1 if quality_stats.get("yaml_tabs_detected") else 0
        )

        stats["quality_style_notes"] = float(len(quality_stats.get("style_notes", [])))

        for check in checks:
            if check.get("severity") == "warning":
                check["severity"] = "warn"

        is_valid, errors = is_valid_analysis_v1(analysis)
        if not is_valid:
            raise SchemaError(f"Invalid analysis schema: {errors}")
        return analysis

    def score(self, analysis: dict[str, Any]) -> float:
        """Calculate total score based on analyzer results."""
        category_scores = self._compute_category_scores(analysis)
        detailed = analysis.get("detailed_scoring")
        if isinstance(detailed, dict):
            for category, max_points in self.category_weights.items():
                entry = detailed.setdefault(category, {})
                entry["earned"] = float(category_scores.get(category, 0.0))
                entry["max"] = float(max_points)
        total = sum(category_scores.values())
        return min(25.0, max(0.0, total))

    def category_breakdown(self, analysis: dict[str, Any]) -> dict[str, float]:
        """Return per-category score breakdown."""
        return self._compute_category_scores(analysis)

    def tests_passed(self, analysis: dict[str, Any]) -> dict[str, bool]:
        """Derive legacy-style pass/fail indicators from checks."""
        checks = analysis.get("checks", [])

        def ok(check_id: str) -> bool:
            return any(item.get("id") == check_id and bool(item.get("ok")) for item in checks)

        return {
            "valid_yaml": ok("fmt.yaml.valid_syntax"),
            "valid_json": ok("fmt.json.valid_syntax"),
            "structure_preserved": ok("fmt.structure.required_keys"),
            "equivalence_test": ok("fmt.cross.equivalent"),
            "correct_types": ok("fmt.quality.literal_types"),
        }

    def _compute_category_scores(self, analysis: dict[str, Any]) -> dict[str, float]:
        """Return per-category scores mirroring the legacy validator."""
        checks = analysis.get("checks", [])
        stats = analysis.get("stats", {})

        def check_ok(check_id: str) -> bool:
            return any(check.get("id") == check_id and bool(check.get("ok")) for check in checks)

        syntax_score = 0.0
        if check_ok("fmt.yaml.valid_syntax"):
            syntax_score += 2.0
        if check_ok("fmt.json.valid_syntax"):
            syntax_score += 2.0

        required_yaml = stats.get("structure_required_keys_yaml", 0.0)
        required_json = stats.get("structure_required_keys_json", 0.0)
        total_expected = float(len(structure_validator.EXPECTED_KEYS))
        missing_yaml_count = stats.get("structure_missing_yaml", 0.0)
        missing_json_count = stats.get("structure_missing_json", 0.0)

        structure_score = 0.0
        if missing_yaml_count == 0 and missing_json_count == 0:
            structure_score += 3.0
        elif required_yaml == total_expected or required_json == total_expected:
            structure_score += 1.5

        shape_matches = stats.get("structure_shape_matches", 0.0)
        total_shape_checks = stats.get("structure_shape_total", 0.0)
        if total_shape_checks:
            structure_score += 2.0 * (shape_matches / total_shape_checks)

        if stats.get("structure_arrays_scalar_correct", 0.0) >= 0.5:
            structure_score += 1.0

        execution_score = 0.0
        if check_ok("fmt.cross.equivalent"):
            execution_score += 6.0
        matching_keys = stats.get("cross_matching_keys", 0.0)
        total_keys = stats.get("cross_total_keys", 0.0)
        if total_keys:
            execution_score += 2.0 * (matching_keys / total_keys)

        quality_score = 0.0
        if check_ok("fmt.quality.indentation"):
            quality_score += 2.0
        if check_ok("fmt.quality.literal_types"):
            quality_score += 2.0
        if check_ok("fmt.quality.duplicates"):
            quality_score += 1.0
        if check_ok("fmt.quality.style"):
            quality_score += 1.0

        security_score = 1.0 if check_ok("fmt.yaml.dangerous_constructs") else 0.0

        return {
            "syntax": syntax_score,
            "structure": structure_score,
            "execution": execution_score,
            "quality": quality_score,
            "security": security_score,
            "performance": 0.0,
            "maintainability": 0.0,
        }
