# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for structure validator."""

from aibugbench.validation.analyzers.format import structure_validator


def _get_check(checks: list[dict], check_id: str) -> dict:
    return next(check for check in checks if check["id"] == check_id)


def test_validate_structure_all_sections_ok():
    """All required keys present with correct shapes should pass."""
    yaml_data = {
        "use_legacy_paths": True,
        "paths": {"data_source": "/srv"},
        "validation_rules": {"min_age_years": 21},
        "api_keys": ["k1", "k2"],
        "feature_flags": {"beta": True},
        "server_settings": {"port": 8080},
    }
    json_data = {
        "use_legacy_paths": False,
        "paths": {"data_source": "/srv"},
        "validation_rules": {"min_age_years": 21},
        "api_keys": ["k1"],
        "feature_flags": {"beta": False},
        "server_settings": {"port": 9000},
    }

    checks, stats = structure_validator.validate_structure(yaml_data, json_data)

    required = _get_check(checks, "fmt.structure.required_keys")
    nested = _get_check(checks, "fmt.structure.nested_shapes")
    arrays = _get_check(checks, "fmt.structure.arrays_scalars")

    assert required["ok"] is True
    assert nested["ok"] is True
    assert arrays["ok"] is True
    assert stats["required_keys_yaml"] == len(structure_validator.EXPECTED_KEYS)
    assert stats["required_keys_json"] == len(structure_validator.EXPECTED_KEYS)
    assert stats["shape_matches"] == stats["total_shape_checks"] == len(structure_validator.DICT_KEYS)
    assert stats["arrays_scalar_correct"] is True


def test_validate_structure_missing_keys_generates_warning():
    """Missing keys in either document emits warning with details."""
    yaml_data = {
        "use_legacy_paths": True,
        "paths": {},
        "api_keys": [],
    }
    json_data = {
        "use_legacy_paths": True,
        "paths": {},
        "validation_rules": {},
        "api_keys": [],
    }

    checks, stats = structure_validator.validate_structure(yaml_data, json_data)
    required = _get_check(checks, "fmt.structure.required_keys")

    assert required["ok"] is False
    assert required["severity"] == "warning"
    assert "YAML missing" in required["message"]
    assert stats["required_keys_yaml"] == 3  # YAML has three expected keys
    assert stats["required_keys_json"] == 4  # JSON missing two keys


def test_validate_structure_detects_wrong_nested_shape():
    """Non-dict nested sections trigger warning."""
    yaml_data = {
        "use_legacy_paths": True,
        "paths": [],
        "validation_rules": {"min_age_years": 21},
        "api_keys": [],
        "feature_flags": {},
        "server_settings": {"port": 8080},
    }
    json_data = {
        "use_legacy_paths": True,
        "paths": {"data_source": "/srv"},
        "validation_rules": [],
        "api_keys": [],
        "feature_flags": {},
        "server_settings": {"port": 8080},
    }

    checks, stats = structure_validator.validate_structure(yaml_data, json_data)
    nested = _get_check(checks, "fmt.structure.nested_shapes")

    assert nested["ok"] is False
    assert nested["severity"] == "warning"
    # Two nested keys appear in both payloads, only one matches shape.
    assert stats["shape_matches"] == 1
    assert stats["total_shape_checks"] == 3


def test_validate_structure_array_scalar_mismatch():
    """api_keys must remain a list in both payloads."""
    yaml_data = {
        "use_legacy_paths": True,
        "paths": {},
        "validation_rules": {},
        "api_keys": "not-a-list",
        "feature_flags": {},
        "server_settings": {},
    }
    json_data = {
        "use_legacy_paths": True,
        "paths": {},
        "validation_rules": {},
        "api_keys": [],
        "feature_flags": {},
        "server_settings": {},
    }

    checks, stats = structure_validator.validate_structure(yaml_data, json_data)
    arrays = _get_check(checks, "fmt.structure.arrays_scalars")

    assert arrays["ok"] is False
    assert arrays["severity"] == "warning"
    assert stats["arrays_scalar_correct"] is False


def test_validate_structure_non_mapping_inputs_fail_fast():
    """Non-dict roots should short-circuit with error."""
    checks, stats = structure_validator.validate_structure([], {})

    assert stats["required_keys_yaml"] == 0
    required = _get_check(checks, "fmt.structure.required_keys")
    assert required["ok"] is False
    assert required["severity"] == "error"
