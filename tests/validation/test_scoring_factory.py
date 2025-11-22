# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for validation.utils.scoring_factory."""

from __future__ import annotations

from aibugbench.validation.utils import create_prompt2_categories


def test_create_prompt2_categories_preserves_order_and_totals():
    categories = create_prompt2_categories()

    expected_order = [
        "syntax",
        "structure",
        "execution",
        "quality",
        "security",
        "performance",
        "maintainability",
    ]
    assert list(categories.keys()) == expected_order
    assert sum(categories.values()) == 25.0
    assert categories["performance"] == 0.0
    assert categories["maintainability"] == 0.0
