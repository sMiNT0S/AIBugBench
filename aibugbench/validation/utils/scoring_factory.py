# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Scoring metadata factories for validators."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping


def create_prompt2_categories() -> Mapping[str, float]:
    """Return ordered category weights for Prompt 2 scoring.

    Includes zero-weight performance and maintainability slots to satisfy legacy
    detail reporting expectations.
    """

    return OrderedDict(
        [
            ("syntax", 4.0),
            ("structure", 6.0),
            ("execution", 8.0),
            ("quality", 6.0),
            ("security", 1.0),
            ("performance", 0.0),
            ("maintainability", 0.0),
        ]
    )


__all__ = ["create_prompt2_categories"]
