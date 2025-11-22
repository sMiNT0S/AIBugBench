# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Structure validation for Prompt 2 YAML/JSON submissions."""

from typing import Any

# HARDCODED: Expected top-level keys for Prompt 2 configs (must stay in sync with legacy).
EXPECTED_KEYS: set[str] = {
    "use_legacy_paths",
    "paths",
    "validation_rules",
    "api_keys",
    "feature_flags",
    "server_settings",
}

# HARDCODED: Keys that must remain dictionaries in both formats.
DICT_KEYS: set[str] = {"paths", "validation_rules", "server_settings"}


def validate_structure(
    yaml_data: Any,
    json_data: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate structural correctness across YAML and JSON payloads.

    Returns:
        Tuple of (checks, stats). Checks contain fmt.structure.* IDs while stats capture
        key counts and shape information for downstream scoring.
    """
    checks: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "required_keys_yaml": 0,
        "required_keys_json": 0,
        "missing_keys_yaml": [],
        "missing_keys_json": [],
        "shape_matches": 0,
        "total_shape_checks": 0,
        "arrays_scalar_correct": True,
    }

    if not isinstance(yaml_data, dict) or not isinstance(json_data, dict):
        checks.append(
            {
                "id": "fmt.structure.required_keys",
                "ok": False,
                "severity": "error",
                "message": "Root objects must be mappings in both YAML and JSON.",
            }
        )
        return checks, stats

    yaml_keys = set(yaml_data.keys())
    json_keys = set(json_data.keys())
    missing_yaml = sorted(EXPECTED_KEYS - yaml_keys)
    missing_json = sorted(EXPECTED_KEYS - json_keys)

    stats["required_keys_yaml"] = len(EXPECTED_KEYS & yaml_keys)
    stats["required_keys_json"] = len(EXPECTED_KEYS & json_keys)
    stats["missing_keys_yaml"] = missing_yaml
    stats["missing_keys_json"] = missing_json

    if not missing_yaml and not missing_json:
        checks.append(
            {
                "id": "fmt.structure.required_keys",
                "ok": True,
                "severity": "info",
                "message": "All required sections present in both formats.",
            }
        )
    elif len(missing_yaml) < len(EXPECTED_KEYS) or len(missing_json) < len(EXPECTED_KEYS):
        missing_parts = []
        if missing_yaml:
            missing_parts.append(f"YAML missing: {', '.join(missing_yaml)}")
        if missing_json:
            missing_parts.append(f"JSON missing: {', '.join(missing_json)}")
        checks.append(
            {
                "id": "fmt.structure.required_keys",
                "ok": False,
                "severity": "warning",
                "message": "; ".join(missing_parts),
            }
        )
    else:
        checks.append(
            {
                "id": "fmt.structure.required_keys",
                "ok": False,
                "severity": "error",
                "message": "Major sections missing from both formats.",
            }
        )

    # Nested shape validation (dicts remain dicts).
    shape_matches = 0
    total_shape_checks = 0
    for key in DICT_KEYS:
        if key in yaml_data and key in json_data:
            total_shape_checks += 1
            if isinstance(yaml_data[key], dict) and isinstance(json_data[key], dict):
                shape_matches += 1
    stats["shape_matches"] = shape_matches
    stats["total_shape_checks"] = total_shape_checks

    if total_shape_checks:
        all_match = shape_matches == total_shape_checks
        message = f"Nested dictionary sections aligned: {shape_matches}/{total_shape_checks}."
        checks.append(
            {
                "id": "fmt.structure.nested_shapes",
                "ok": all_match,
                "severity": "info" if all_match else "warning",
                "message": message,
            }
        )

    # Arrays vs scalar expectations (api_keys should remain a list).
    array_scalar_correct = True
    if "api_keys" in yaml_data and "api_keys" in json_data:
        array_scalar_correct = isinstance(yaml_data["api_keys"], list) and isinstance(
            json_data["api_keys"], list
        )
    stats["arrays_scalar_correct"] = array_scalar_correct
    checks.append(
        {
            "id": "fmt.structure.arrays_scalars",
            "ok": array_scalar_correct,
            "severity": "info" if array_scalar_correct else "warning",
            "message": (
                "List-valued fields preserved across formats."
                if array_scalar_correct
                else "Expected api_keys to remain a list in both formats."
            ),
        }
    )

    return checks, stats
