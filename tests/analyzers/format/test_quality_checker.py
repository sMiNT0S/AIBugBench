# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for quality checker."""

from pathlib import Path

import yaml

from aibugbench.validation.analyzers.format.quality_checker import check_quality


def _write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _get_check(checks: list[dict], check_id: str) -> dict:
    return next(check for check in checks if check["id"] == check_id)


def test_check_quality_all_ok(tmp_path: Path):
    """Well-formed YAML/JSON should pass all quality checks."""
    yaml_path = _write_file(
        tmp_path / "config.yaml",
        """use_legacy_paths: true
paths:
  data_source: /srv/data
validation_rules:
  min_age_years: 21
api_keys:
  - abc123
feature_flags:
  enable_email_notifications: false
server_settings:
  port: 8080
""",
    )
    yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    json_data = {
        "use_legacy_paths": True,
        "paths": {"data_source": "/srv/data"},
        "validation_rules": {"min_age_years": 21},
        "api_keys": ["abc123"],
        "feature_flags": {"enable_email_notifications": False},
        "server_settings": {"port": 8080},
    }

    checks, stats = check_quality(yaml_path, tmp_path / "config.json", yaml_data, json_data)

    assert all(check["ok"] for check in checks)
    assert stats["indentation_issues"] == []
    assert stats["literal_issues"] == []
    assert stats["duplicate_details"] == []


def test_check_quality_detects_yaml_tabs(tmp_path: Path):
    """Tabs in YAML indentation should trigger warning."""
    yaml_path = _write_file(
        tmp_path / "config.yaml",
        "paths:\n\tdata_source: /srv/data\n",
    )
    yaml_data = yaml.safe_load("paths:\n  data_source: /srv/data\n")

    checks, stats = check_quality(yaml_path, tmp_path / "config.json", yaml_data, {})
    indentation = _get_check(checks, "fmt.quality.indentation")

    assert indentation["ok"] is False
    assert indentation["severity"] == "warning"
    assert stats["yaml_tabs_detected"] is True
    assert any("tabs" in issue.lower() for issue in stats["indentation_issues"])


def test_check_quality_detects_json_literal_issues(tmp_path: Path):
    """String literals where ints/bools expected should warn."""
    yaml_path = _write_file(
        tmp_path / "config.yaml",
        "use_legacy_paths: true\n",
    )
    yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    json_data = {
        "use_legacy_paths": "true",
        "validation_rules": {"min_age_years": "21"},
        "server_settings": {"port": "8080"},
    }

    checks, stats = check_quality(yaml_path, tmp_path / "config.json", yaml_data, json_data)
    literals = _get_check(checks, "fmt.quality.literal_types")

    assert literals["ok"] is False
    assert literals["severity"] == "warning"
    assert len(stats["literal_issues"]) == 3


def test_check_quality_detects_duplicate_keys(tmp_path: Path):
    """Duplicate YAML keys reported as error."""
    yaml_path = _write_file(
        tmp_path / "config.yaml",
        "paths:\n  data_source: /srv\n  data_source: /tmp\n",
    )

    checks, stats = check_quality(yaml_path, tmp_path / "config.json", None, {})
    duplicates = _get_check(checks, "fmt.quality.duplicates")

    assert duplicates["ok"] is False
    assert duplicates["severity"] == "error"
    assert any("duplicate" in detail.lower() for detail in stats["duplicate_details"])
