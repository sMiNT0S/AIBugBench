# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for YAML analyzer."""

from pathlib import Path
import tempfile

from aibugbench.validation.analyzers.format.yaml_analyzer import analyze_yaml


def test_analyze_yaml_valid():
    """Valid YAML file passes all checks."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
use_legacy_paths: true
paths:
  data_source: /srv/data
  log_file: /var/log/app.log
""")
        yaml_path = Path(f.name)

    try:
        checks, stats = analyze_yaml(yaml_path)

        # All checks should pass
        assert all(c["ok"] for c in checks), f"Failed checks: {[c for c in checks if not c['ok']]}"

        # Stats populated
        assert stats["yaml_lines"] > 0
        assert stats["yaml_keys"] > 0

    finally:
        yaml_path.unlink()


def test_analyze_yaml_duplicate_keys():
    """Duplicate keys are detected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
paths:
  log_file: /var/log/app.log
  log_file: /tmp/debug.log
""")
        yaml_path = Path(f.name)

    try:
        checks, _ = analyze_yaml(yaml_path)

        # Find duplicate check
        dup_check = next((c for c in checks if c["id"] == "fmt.yaml.duplicate_keys"), None)
        assert dup_check is not None
        assert not dup_check["ok"], "Duplicate keys should fail check"
        assert "duplicate" in dup_check["message"].lower()

    finally:
        yaml_path.unlink()


def test_analyze_yaml_indentation_tabs():
    """Tabs in indentation are detected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("paths:\n\tlog_file: /var/log/app.log\n")  # Tab instead of spaces
        yaml_path = Path(f.name)

    try:
        checks, _ = analyze_yaml(yaml_path)

        indent_check = next((c for c in checks if c["id"] == "fmt.yaml.indentation"), None)
        assert indent_check is not None
        assert not indent_check["ok"], "Tabs should fail indentation check"
        assert "tab" in indent_check["message"].lower()

    finally:
        yaml_path.unlink()


def test_analyze_yaml_dangerous_constructs():
    """Dangerous YAML tags are detected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("!!python/object:os.system\nargs: ['rm -rf /']")
        yaml_path = Path(f.name)

    try:
        checks, _ = analyze_yaml(yaml_path)

        danger_check = next((c for c in checks if c["id"] == "fmt.yaml.dangerous_constructs"), None)
        assert danger_check is not None
        assert not danger_check["ok"], "Dangerous constructs should fail check"
        assert "dangerous" in danger_check["message"].lower()

    finally:
        yaml_path.unlink()


def test_analyze_yaml_file_not_found():
    """Missing file is handled gracefully."""
    checks, _ = analyze_yaml(Path("/nonexistent/file.yaml"))

    exists_check = next((c for c in checks if c["id"] == "fmt.yaml.file_exists"), None)
    assert exists_check is not None
    assert not exists_check["ok"]
