# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for JSON analyzer."""

import json
from pathlib import Path
import tempfile

from aibugbench.validation.analyzers.format.json_analyzer import analyze_json


def test_analyze_json_valid():
    """Valid JSON with correct literals passes."""
    data = {
        "use_legacy_paths": True,  # Proper boolean
        "paths": {"data_source": "/srv/data"},
        "validation_rules": {"min_age_years": 21},  # Proper integer
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_path = Path(f.name)

    try:
        checks, _ = analyze_json(json_path)

        # Syntax check should pass
        syntax_check = next((c for c in checks if c["id"] == "fmt.json.valid_syntax"), None)
        assert syntax_check is not None
        assert syntax_check["ok"]

        # Literal types check should pass
        literal_check = next((c for c in checks if c["id"] == "fmt.json.literal_types"), None)
        assert literal_check is not None
        assert literal_check["ok"]

    finally:
        json_path.unlink()


def test_analyze_json_string_booleans():
    """String booleans are detected."""
    data = {
        "use_legacy_paths": "true",  # Should be boolean True
        "enable_logging": "false",  # Should be boolean False
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_path = Path(f.name)

    try:
        checks, stats = analyze_json(json_path)

        literal_check = next((c for c in checks if c["id"] == "fmt.json.literal_types"), None)
        assert literal_check is not None
        assert not literal_check["ok"], "String booleans should fail check"
        assert stats["string_bools_found"] == 2

    finally:
        json_path.unlink()


def test_analyze_json_string_integers():
    """String integers are detected."""
    data = {
        "port": "8080",  # Should be integer 8080
        "min_age": "21",  # Should be integer 21
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_path = Path(f.name)

    try:
        checks, stats = analyze_json(json_path)

        literal_check = next((c for c in checks if c["id"] == "fmt.json.literal_types"), None)
        assert literal_check is not None
        assert not literal_check["ok"], "String integers should fail check"
        assert stats["string_ints_found"] == 2

    finally:
        json_path.unlink()


def test_analyze_json_file_not_found():
    """Missing file is handled gracefully."""
    checks, _ = analyze_json(Path("/nonexistent/file.json"))

    exists_check = next((c for c in checks if c["id"] == "fmt.json.file_exists"), None)
    assert exists_check is not None
    assert not exists_check["ok"]


def test_analyze_json_invalid_syntax():
    """Invalid JSON syntax is handled gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{invalid json: missing quotes}")
        json_path = Path(f.name)

    try:
        checks, _ = analyze_json(json_path)

        syntax_check = next((c for c in checks if c["id"] == "fmt.json.valid_syntax"), None)
        assert syntax_check is not None
        assert not syntax_check["ok"], "Invalid JSON should fail syntax check"
        assert "parsing failed" in syntax_check["message"].lower()

    finally:
        json_path.unlink()


def test_analyze_json_nested_structures():
    """Nested objects and arrays with string literals are detected."""
    data = {
        "config": {
            "database": {
                "port": "5432",  # String integer in nested object
                "ssl_enabled": "true",  # String boolean in nested object
            }
        },
        "features": [
            {"name": "auth", "enabled": "yes"},  # String boolean in array item
            {"name": "cache", "timeout": "300"},  # String integer in array item
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_path = Path(f.name)

    try:
        checks, stats = analyze_json(json_path)

        literal_check = next((c for c in checks if c["id"] == "fmt.json.literal_types"), None)
        assert literal_check is not None
        assert not literal_check["ok"], "Nested string literals should fail check"
        assert stats["string_bools_found"] == 2
        assert stats["string_ints_found"] == 2
        assert stats["json_objects"] >= 3  # root + config.database + 2 array items
        assert stats["json_arrays"] >= 1  # features array

    finally:
        json_path.unlink()


def test_analyze_json_array_literals():
    """String literals in arrays are detected."""
    data = {
        "ports": ["8080", "8443", "9000"],  # String integers in array
        "flags": ["true", "false", "yes", "no"],  # String booleans in array
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_path = Path(f.name)

    try:
        checks, stats = analyze_json(json_path)

        literal_check = next((c for c in checks if c["id"] == "fmt.json.literal_types"), None)
        assert literal_check is not None
        assert not literal_check["ok"], "Array string literals should fail check"
        assert stats["string_bools_found"] == 4
        assert stats["string_ints_found"] == 3

    finally:
        json_path.unlink()
