# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for validation.utils.result_builder."""

from __future__ import annotations

from aibugbench.validation.utils import build_validation_result


def test_build_validation_result_returns_schema_scaffold():
    weights = {"syntax": 4.0, "quality": 2.5}

    result = build_validation_result(category_weights=weights)

    assert set(result.keys()) == {"checks", "stats", "artifacts", "detailed_scoring"}
    assert result["checks"] == []
    assert result["stats"] == {}
    assert result["artifacts"] == {}
    assert result["detailed_scoring"]["syntax"] == {"earned": 0.0, "max": 4.0}
    assert result["detailed_scoring"]["quality"] == {"earned": 0.0, "max": 2.5}
