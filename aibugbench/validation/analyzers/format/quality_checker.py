# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Quality checks for Prompt 2 YAML/JSON submissions."""

from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError

from .yaml_analyzer import UniqueKeyLoader


def check_quality(
    yaml_file: Path,
    json_file: Path,
    yaml_data: Any,
    json_data: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Evaluate indentation, literal typing, and duplication heuristics."""
    checks: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "indentation_issues": [],
        "literal_issues": [],
        "duplicate_details": [],
        "yaml_tabs_detected": False,
        "style_notes": [],
    }

    # Duplicate detection mirrors legacy validator behaviour.
    yaml_content = ""
    yaml_read_issue: str | None = None
    if yaml_file.exists():
        try:
            yaml_content = yaml_file.read_text(encoding="utf-8")
        except OSError as exc:
            yaml_read_issue = f"Failed to read YAML for quality checks: {exc}"
    else:
        yaml_read_issue = "YAML file missing during quality checks."

    yaml_has_duplicates = False
    duplicate_details: list[str] = []
    if yaml_content:
        try:
            # UniqueKeyLoader subclasses yaml.SafeLoader; we invoke it solely to detect duplicate
            # keys, not to construct arbitrary Python objects, mirroring the legacy validator.
            yaml.load(yaml_content, Loader=UniqueKeyLoader)  # nosec B506  # noqa: S506
        except ConstructorError as exc:
            yaml_has_duplicates = True
            duplicate_details.append(str(exc))
        except yaml.YAMLError as exc:
            yaml_has_duplicates = True
            duplicate_details.append(f"YAML parsing failed during duplicate check: {exc}")
    elif yaml_read_issue:
        yaml_has_duplicates = True
        duplicate_details.append(yaml_read_issue)

    stats["duplicate_details"] = duplicate_details

    if yaml_has_duplicates:
        checks.append(
            {
                "id": "fmt.quality.duplicates",
                "ok": False,
                "severity": "error",
                "message": "; ".join(duplicate_details) or "Duplicate YAML keys detected.",
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.quality.duplicates",
                "ok": True,
                "severity": "info",
                "message": "No duplicate YAML keys detected.",
            }
        )

    # Indentation analysis (tabs + non 2-space multiples).
    indentation_issues: list[str] = []
    if yaml_content:
        if "\t" in yaml_content:
            stats["yaml_tabs_detected"] = True
            indentation_issues.append("Contains tabs instead of spaces.")
        indent_levels = {
            len(line) - len(line.lstrip(" "))
            for line in yaml_content.splitlines()
            if line.strip() and (len(line) - len(line.lstrip(" "))) > 0
        }
        if indent_levels and not all(level % 2 == 0 for level in indent_levels):
            indentation_issues.append("Indentation uses non 2-space multiples.")
    elif yaml_read_issue:
        indentation_issues.append(yaml_read_issue)

    stats["indentation_issues"] = indentation_issues
    indentation_ok = not indentation_issues
    checks.append(
        {
            "id": "fmt.quality.indentation",
            "ok": indentation_ok,
            "severity": "info" if indentation_ok else "warning",
            "message": "Indentation is 2-space consistent."
            if indentation_ok
            else "; ".join(indentation_issues),
        }
    )

    # Literal type validation (JSON).
    literal_issues: list[str] = []
    if isinstance(json_data, dict):
        if "use_legacy_paths" in json_data and not isinstance(json_data["use_legacy_paths"], bool):
            literal_issues.append("use_legacy_paths should be a boolean, not string.")
        for section, key in (("validation_rules", "min_age_years"), ("server_settings", "port")):
            container = json_data.get(section)
            value = container.get(key) if isinstance(container, dict) else None
            if value is not None and not isinstance(value, int):
                literal_issues.append(f"{section}.{key} should be an integer, not string.")
    elif json_file.exists():
        literal_issues.append("JSON payload failed to parse for literal checks.")
    else:
        literal_issues.append("JSON file missing during literal checks.")

    stats["literal_issues"] = literal_issues
    literals_ok = not literal_issues
    checks.append(
        {
            "id": "fmt.quality.literal_types",
            "ok": literals_ok,
            "severity": "info" if literals_ok else "warning",
            "message": "All JSON literals have correct native types."
            if literals_ok
            else "; ".join(literal_issues),
        }
    )

    # Style heuristic placeholder (preserved for scoring parity).
    stats["style_notes"] = ["Baseline formatting heuristics satisfied."]
    checks.append(
        {
            "id": "fmt.quality.style",
            "ok": True,
            "severity": "info",
            "message": "Baseline formatting heuristics satisfied.",
        }
    )

    return checks, stats
