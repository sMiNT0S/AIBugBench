# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Cross-format comparison with normalization.

CRITICAL: normalize_for_comparison and deep_compare are ported VERBATIM
from validators.py:1299-1322 and 1329-1350. Do NOT modify without regression testing.
"""

from typing import Any


def normalize_for_comparison(data: Any) -> Any:
    """Normalize data for cross-format comparison.

    PORTED VERBATIM from validators.py:1432-1455.
    """
    if isinstance(data, dict):
        normalized = {}
        for k, v in data.items():
            normalized[k] = normalize_for_comparison(v)
        return normalized
    elif isinstance(data, list):
        return [normalize_for_comparison(item) for item in data]
    elif isinstance(data, str):
        # Convert string booleans and numbers
        lower_val = data.lower()
        if lower_val in ("true", "false"):
            return lower_val == "true"
        try:
            # Try integer first
            if "." not in data:
                return int(data)
            else:
                return float(data)
        except ValueError:
            return data
    else:
        return data


def deep_compare(obj1: Any, obj2: Any, path: str = "") -> tuple[bool, str]:
    """Deep comparison of two normalized objects with path tracking.

    PORTED VERBATIM from validators.py:1456-1478.
    """
    if not isinstance(obj1, type(obj2)):
        return False, f"Type mismatch at {path}: {type(obj1)} vs {type(obj2)}"

    if isinstance(obj1, dict):
        if set(obj1.keys()) != set(obj2.keys()):
            return False, f"Key mismatch at {path}"
        for key in obj1:
            equal, msg = deep_compare(obj1[key], obj2[key], f"{path}.{key}")
            if not equal:
                return False, msg
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False, f"Length mismatch at {path}"
        for i, (item1, item2) in enumerate(zip(obj1, obj2, strict=False)):
            equal, msg = deep_compare(item1, item2, f"{path}[{i}]")
            if not equal:
                return False, msg
    elif obj1 != obj2:
        return False, f"Value mismatch at {path}: {obj1} vs {obj2}"

    return True, "Match"


def _count_strings(data: Any) -> int:
    """Count total string values in nested data structure.

    Helper for estimating normalization impact.
    """
    count = 0
    if isinstance(data, dict):
        for v in data.values():
            count += _count_strings(v)
    elif isinstance(data, list):
        for item in data:
            count += _count_strings(item)
    elif isinstance(data, str):
        count += 1
    return count


def compare_formats(
    yaml_data: Any,
    json_data: Any,
    expected_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compare YAML and JSON data after normalization.

    Args:
        yaml_data: Parsed YAML data structure
        json_data: Parsed JSON data structure
        expected_keys: Optional set of top-level keys for partial credit scoring

    Returns:
        Tuple of (checks, stats) where:
        - checks: List of check dictionaries with id, severity, message
        - stats: Dictionary with normalized_changes, matching_keys, total_keys
    """
    checks: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "normalized_changes": 0,
        "matching_keys": 0,
        "total_keys": 0,
    }

    # Guard against parse failures
    if yaml_data is None or json_data is None:
        checks.append(
            {
                "id": "fmt.cross.equivalent",
                "ok": False,
                "severity": "error",
                "message": "Cannot compare: one or both files failed to parse",
            }
        )
        return checks, stats

    # Track normalization changes (count strings before normalization)
    yaml_str_count = _count_strings(yaml_data)
    json_str_count = _count_strings(json_data)

    # Normalize both structures
    normalized_yaml = normalize_for_comparison(yaml_data)
    normalized_json = normalize_for_comparison(json_data)

    # Deep comparison
    is_equivalent, comparison_msg = deep_compare(normalized_yaml, normalized_json)

    if is_equivalent:
        checks.append(
            {
                "id": "fmt.cross.equivalent",
                "severity": "info",
                "message": "Perfect cross-format equivalence after normalization",
                "ok": True,
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.cross.equivalent",
                "severity": "error",
                "message": f"Cross-format mismatch: {comparison_msg}",
                "ok": False,
            }
        )

    # Partial credit: count matching top-level keys
    if (
        expected_keys is not None
        and isinstance(normalized_yaml, dict)
        and isinstance(normalized_json, dict)
    ):
        matching = 0
        for key in expected_keys:
            if key in normalized_yaml and key in normalized_json:
                key_equal, _ = deep_compare(normalized_yaml[key], normalized_json[key], path=key)
                if key_equal:
                    matching += 1

        stats["matching_keys"] = matching
        stats["total_keys"] = len(expected_keys)

        checks.append(
            {
                "id": "fmt.cross.partial_match",
                "severity": "info" if matching == len(expected_keys) else "warning",
                "message": f"Key-level matches: {matching}/{len(expected_keys)}",
                "ok": matching == len(expected_keys),
            }
        )

    # Track normalized changes (delta across both formats)
    norm_yaml_str_count = _count_strings(normalized_yaml)
    norm_json_str_count = _count_strings(normalized_json)
    stats["normalized_changes"] = (yaml_str_count + json_str_count) - (
        norm_yaml_str_count + norm_json_str_count
    )

    return checks, stats
