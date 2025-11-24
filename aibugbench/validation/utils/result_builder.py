# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Helpers for constructing schema-compliant validation results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aibugbench.validation.schema import ARTIFACTS_KEY, CHECKS_KEY, STATS_KEY


def build_validation_result(*, category_weights: Mapping[str, float]) -> dict[str, Any]:
    """Return a schema-v1 scaffold with legacy-style detailed scoring shell.

    The returned mapping is ready for analyzers to mutate in-place.
    """

    detailed_scoring = {
        category: {"earned": 0.0, "max": float(weight)}
        for category, weight in category_weights.items()
    }
    return {
        CHECKS_KEY: [],
        STATS_KEY: {},
        ARTIFACTS_KEY: {},
        "detailed_scoring": detailed_scoring,
    }


__all__ = ["build_validation_result"]
