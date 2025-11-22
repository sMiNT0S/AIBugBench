# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""JSON format analyzer with literal type validation."""

import json
from pathlib import Path
from typing import Any


def analyze_json(file_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyze JSON file for syntax and literal type correctness.

    Args:
        file_path: Path to JSON file (LLM-generated output)

    Returns:
        Tuple of (checks, stats):
        - checks: List of check dicts with keys: id, ok, severity, message
        - stats: Dict of metrics: json_keys, string_bools_found, string_ints_found

    Emitted check IDs:
        - fmt.json.valid_syntax: JSON parses without errors
        - fmt.json.literal_types: Proper boolean/integer literals (not strings)
    """
    checks: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "json_keys": 0,
        "json_objects": 0,
        "json_arrays": 0,
        "string_bools_found": 0,
        "string_ints_found": 0,
    }

    # Check file existence
    if not file_path.exists():
        checks.append(
            {
                "id": "fmt.json.file_exists",
                "ok": False,
                "severity": "error",
                "message": f"JSON file not found: {file_path}",
            }
        )
        return checks, stats

    # Parse JSON
    json_data = None
    try:
        with open(file_path, encoding="utf-8") as f:
            json_data = json.load(f)

        checks.append(
            {
                "id": "fmt.json.valid_syntax",
                "ok": True,
                "severity": "info",
                "message": "JSON parses successfully",
            }
        )

        # Count structure elements
        if isinstance(json_data, dict):
            stats["json_keys"] = len(json_data)
            stats["json_objects"] = 1 + _count_objects(json_data)
            stats["json_arrays"] = _count_arrays(json_data)

    except json.JSONDecodeError as e:
        checks.append(
            {
                "id": "fmt.json.valid_syntax",
                "ok": False,
                "severity": "error",
                "message": f"JSON parsing failed: {e}",
            }
        )
        return checks, stats

    # Literal type validation
    if json_data is not None:
        string_bools, string_ints = _find_string_literals(json_data)
        stats["string_bools_found"] = len(string_bools)
        stats["string_ints_found"] = len(string_ints)

        issues = []
        if string_bools:
            issues.append(f"String booleans at: {', '.join(string_bools[:3])}")
        if string_ints:
            issues.append(f"String integers at: {', '.join(string_ints[:3])}")

        if issues:
            checks.append(
                {
                    "id": "fmt.json.literal_types",
                    "ok": False,
                    "severity": "warning",
                    "message": f"Literal type issues: {'; '.join(issues)}",
                }
            )
        else:
            checks.append(
                {
                    "id": "fmt.json.literal_types",
                    "ok": True,
                    "severity": "info",
                    "message": "All literals have correct types",
                }
            )

    return checks, stats


def _count_objects(obj: Any) -> int:
    """Recursively count dict objects."""
    count = 0
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, dict):
                count += 1
                count += _count_objects(v)
            elif isinstance(v, list):
                count += _count_objects(v)
    elif isinstance(obj, list):
        for item in obj:
            count += _count_objects(item)
    return count


def _count_arrays(obj: Any) -> int:
    """Recursively count list arrays."""
    count = 0
    if isinstance(obj, dict):
        for v in obj.values():
            count += _count_arrays(v)
    elif isinstance(obj, list):
        count += 1
        for item in obj:
            count += _count_arrays(item)
    return count


def _find_string_literals(obj: Any, path: str = "root") -> tuple[list[str], list[str]]:
    """Find string values that should be bool or int.

    Returns:
        Tuple of (string_bool_paths, string_int_paths)
    """
    string_bools: list[str] = []
    string_ints: list[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            if isinstance(value, str):
                # Check if looks like boolean
                if value.lower() in ("true", "false", "yes", "no", "on", "off"):
                    string_bools.append(child_path)
                # Check if looks like integer
                elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                    string_ints.append(child_path)
            else:
                child_bools, child_ints = _find_string_literals(value, child_path)
                string_bools.extend(child_bools)
                string_ints.extend(child_ints)

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            if isinstance(item, str):
                if item.lower() in ("true", "false", "yes", "no", "on", "off"):
                    string_bools.append(child_path)
                elif item.isdigit() or (item.startswith("-") and item[1:].isdigit()):
                    string_ints.append(child_path)
            else:
                child_bools, child_ints = _find_string_literals(item, child_path)
                string_bools.extend(child_bools)
                string_ints.extend(child_ints)

    return string_bools, string_ints
