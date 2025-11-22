# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""YAML format analyzer with duplicate key detection."""

from pathlib import Path
import re
from typing import Any

import yaml
from yaml.constructor import ConstructorError


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that detects duplicate keys in YAML mappings.

    CRITICAL: This class is ported VERBATIM from validators.py:114-127.
    Any changes may break duplicate detection behavior.
    """

    def construct_mapping(self, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def analyze_yaml(file_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyze YAML file for syntax, duplicates, indentation, and dangerous constructs.

    Args:
        file_path: Path to YAML file (LLM-generated output)

    Returns:
        Tuple of (checks, stats):
        - checks: List of check dicts with keys: id, ok, severity, message
        - stats: Dict of metrics: yaml_lines, yaml_keys, etc.

    Emitted check IDs:
        - fmt.yaml.file_exists: File exists at given path
        - fmt.yaml.file_read: File can be read successfully
        - fmt.yaml.valid_syntax: YAML parses without errors
        - fmt.yaml.duplicate_keys: No duplicate keys detected
        - fmt.yaml.indentation: Consistent 2-space indentation
        - fmt.yaml.dangerous_constructs: No !!python/ or other dangerous tags
    """
    checks: list[dict[str, Any]] = []
    stats: dict[str, Any] = {"yaml_lines": 0, "yaml_keys": 0, "yaml_depth": 0}

    # Check file existence
    if not file_path.exists():
        checks.append(
            {
                "id": "fmt.yaml.file_exists",
                "ok": False,
                "severity": "error",
                "message": f"YAML file not found: {file_path}",
            }
        )
        return checks, stats

    # Read content
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        checks.append(
            {
                "id": "fmt.yaml.file_read",
                "ok": False,
                "severity": "error",
                "message": f"Failed to read YAML file: {e}",
            }
        )
        return checks, stats

    stats["yaml_lines"] = len(content.splitlines())

    # Check for dangerous constructs BEFORE parsing
    dangerous_patterns = [
        (r"!!python/", "Python object instantiation"),
        (r"!!map", "Explicit mapping tag"),
    ]

    dangerous_found = []
    for pattern, description in dangerous_patterns:
        if re.search(pattern, content):
            dangerous_found.append(description)

    if dangerous_found:
        checks.append(
            {
                "id": "fmt.yaml.dangerous_constructs",
                "ok": False,
                "severity": "error",
                "message": f"Dangerous YAML constructs: {', '.join(dangerous_found)}",
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.yaml.dangerous_constructs",
                "ok": True,
                "severity": "info",
                "message": "No dangerous YAML constructs detected",
            }
        )

    # Indentation validation (check BEFORE parsing so we can catch tabs even if they break parsing)
    lines = content.split("\n")
    has_tabs = "\t" in content
    indent_levels = set()

    for line in lines:
        if line.strip():  # Non-empty
            leading_spaces = len(line) - len(line.lstrip(" "))
            if leading_spaces > 0:
                indent_levels.add(leading_spaces)

    indentation_issues = []
    if has_tabs:
        indentation_issues.append("Contains tabs instead of spaces")

    # Check for 2-space multiples
    if indent_levels and not all(level % 2 == 0 for level in indent_levels):
        indentation_issues.append("Inconsistent indentation (not 2-space multiples)")

    if indentation_issues:
        checks.append(
            {
                "id": "fmt.yaml.indentation",
                "ok": False,
                "severity": "warning",
                "message": f"Indentation issues: {'; '.join(indentation_issues)}",
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.yaml.indentation",
                "ok": True,
                "severity": "info",
                "message": "Indentation is consistent (2-space)",
            }
        )

    # Duplicate key detection
    has_duplicates = False
    duplicate_msg = ""
    try:
        yaml.load(content, Loader=UniqueKeyLoader)  # nosec B506  # noqa: S506
    except ConstructorError as e:
        has_duplicates = True
        duplicate_msg = str(e)
    except yaml.YAMLError:
        pass  # Will be caught by syntax check below

    if has_duplicates:
        checks.append(
            {
                "id": "fmt.yaml.duplicate_keys",
                "ok": False,
                "severity": "error",
                "message": f"Duplicate YAML keys detected: {duplicate_msg}",
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.yaml.duplicate_keys",
                "ok": True,
                "severity": "info",
                "message": "No duplicate keys detected",
            }
        )

    # Syntax validation (safe_load)
    yaml_data = None
    try:
        yaml_data = yaml.safe_load(content)
        checks.append(
            {
                "id": "fmt.yaml.valid_syntax",
                "ok": True,
                "severity": "info",
                "message": "YAML parses successfully with safe_load",
            }
        )

        # Count keys (if dict)
        if isinstance(yaml_data, dict):
            stats["yaml_keys"] = len(yaml_data)
            stats["yaml_depth"] = _calculate_depth(yaml_data)

    except yaml.YAMLError as e:
        checks.append(
            {
                "id": "fmt.yaml.valid_syntax",
                "ok": False,
                "severity": "error",
                "message": f"YAML parsing failed: {e}",
            }
        )
    return checks, stats


def _calculate_depth(obj: Any, current_depth: int = 1) -> int:
    """Calculate maximum nesting depth of a data structure."""
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_calculate_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_calculate_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth
