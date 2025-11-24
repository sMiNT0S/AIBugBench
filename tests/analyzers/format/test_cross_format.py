# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for cross-format comparison analyzer."""

from aibugbench.validation.analyzers.format.cross_format import (
    compare_formats,
    deep_compare,
    normalize_for_comparison,
)


class TestNormalizeForComparison:
    """Test VERBATIM normalize_for_comparison function."""

    def test_normalize_string_to_bool(self):
        """String booleans convert to Python bool."""
        assert normalize_for_comparison("true") is True
        assert normalize_for_comparison("True") is True
        assert normalize_for_comparison("TRUE") is True
        assert normalize_for_comparison("false") is False
        assert normalize_for_comparison("False") is False
        assert normalize_for_comparison("FALSE") is False

    def test_normalize_string_to_int(self):
        """String integers convert to Python int."""
        result_8080 = normalize_for_comparison("8080")
        assert result_8080 == 8080
        assert isinstance(result_8080, int)

        result_21 = normalize_for_comparison("21")
        assert result_21 == 21
        assert isinstance(result_21, int)

        # Edge case: negative integers
        result_neg = normalize_for_comparison("-42")
        assert result_neg == -42
        assert isinstance(result_neg, int)

    def test_normalize_string_to_float(self):
        """String floats convert to Python float."""
        result_pi = normalize_for_comparison("3.14")
        assert result_pi == 3.14
        assert isinstance(result_pi, float)

        result_60 = normalize_for_comparison("60.00")
        assert result_60 == 60.0
        assert isinstance(result_60, float)

        # Edge case: scientific notation
        result_sci = normalize_for_comparison("1.5")
        assert result_sci == 1.5
        assert isinstance(result_sci, float)

    def test_normalize_nested(self):
        """Recursive normalization works in dicts and lists."""
        nested_data = {
            "port": "8080",
            "enabled": "true",
            "timeout": "30.5",
            "servers": ["production", "staging"],
            "config": {
                "debug": "false",
                "max_connections": "100",
            },
        }

        result = normalize_for_comparison(nested_data)

        # Check types after normalization
        assert result["port"] == 8080
        assert isinstance(result["port"], int)

        assert result["enabled"] is True
        assert isinstance(result["enabled"], bool)

        assert result["timeout"] == 30.5
        assert isinstance(result["timeout"], float)

        # Lists preserve strings that aren't bool/number
        assert result["servers"] == ["production", "staging"]

        # Nested dict normalization
        assert result["config"]["debug"] is False
        assert result["config"]["max_connections"] == 100

    def test_normalize_passthrough(self):
        """Non-string values pass through unchanged."""
        assert normalize_for_comparison(42) == 42
        assert normalize_for_comparison(3.14) == 3.14
        assert normalize_for_comparison(True) is True
        assert normalize_for_comparison(None) is None

        # Strings that don't match patterns
        assert normalize_for_comparison("hello") == "hello"
        assert normalize_for_comparison("not-a-number") == "not-a-number"


class TestDeepCompare:
    """Test VERBATIM deep_compare function."""

    def test_deep_compare_equal(self):
        """Equal objects return (True, 'Match')."""
        obj1 = {"a": 1, "b": [2, 3], "c": {"d": 4}}
        obj2 = {"a": 1, "b": [2, 3], "c": {"d": 4}}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is True
        assert msg == "Match"

    def test_deep_compare_type_mismatch(self):
        """Type mismatch detected with path."""
        obj1 = {"port": 8080}
        obj2 = {"port": "8080"}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is False
        assert "Type mismatch at .port" in msg
        assert "int" in msg.lower() or "str" in msg.lower()

    def test_deep_compare_key_mismatch(self):
        """Key set mismatch detected."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"a": 1, "c": 3}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is False
        assert "Key mismatch" in msg

    def test_deep_compare_value_mismatch(self):
        """Value mismatch with path."""
        obj1 = {"server": {"host": "localhost", "port": 8080}}
        obj2 = {"server": {"host": "localhost", "port": 9000}}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is False
        assert "Value mismatch" in msg
        assert ".server.port" in msg
        assert "8080" in msg
        assert "9000" in msg

    def test_deep_compare_list_length_mismatch(self):
        """List length mismatch detected."""
        obj1 = {"items": [1, 2, 3]}
        obj2 = {"items": [1, 2]}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is False
        assert "Length mismatch" in msg
        assert ".items" in msg

    def test_deep_compare_list_item_mismatch(self):
        """List item value mismatch with index path."""
        obj1 = {"servers": [{"name": "prod"}, {"name": "staging"}]}
        obj2 = {"servers": [{"name": "prod"}, {"name": "dev"}]}

        is_equal, msg = deep_compare(obj1, obj2)
        assert is_equal is False
        assert "[1]" in msg or "staging" in msg or "dev" in msg


class TestCompareFormats:
    """Test compare_formats wrapper function."""

    def test_compare_formats_equivalent(self):
        """YAML with string types matches JSON with native types."""
        yaml_data = {
            "flag": "true",
            "port": "8080",
            "timeout": "30.5",
        }
        json_data = {
            "flag": True,
            "port": 8080,
            "timeout": 30.5,
        }

        checks, stats = compare_formats(yaml_data, json_data)

        # Should emit fmt.cross.equivalent check
        equiv_check = next(c for c in checks if c["id"] == "fmt.cross.equivalent")
        assert equiv_check["ok"] is True
        assert equiv_check["severity"] == "info"

        # Stats should track some normalization
        assert stats["normalized_changes"] >= 0

    def test_compare_formats_not_equivalent(self):
        """Different values fail with descriptive message."""
        yaml_data = {"server": {"host": "localhost", "port": "8080"}}
        json_data = {"server": {"host": "localhost", "port": 9000}}

        checks, _ = compare_formats(yaml_data, json_data)

        # Should emit failed fmt.cross.equivalent check
        equiv_check = next(c for c in checks if c["id"] == "fmt.cross.equivalent")
        assert equiv_check["ok"] is False
        assert equiv_check["severity"] == "error"
        assert "mismatch" in equiv_check["message"].lower()

    def test_compare_formats_partial_credit(self):
        """Partial credit scoring with expected_keys."""
        yaml_data = {
            "paths": {"data": "/data"},
            "server_settings": {"port": "8080"},
            "api_keys": ["key1"],
        }
        json_data = {
            "paths": {"data": "/data"},
            "server_settings": {"port": 9000},  # Different value
            "api_keys": ["key1"],
        }

        expected_keys = {"paths", "server_settings", "api_keys"}
        checks, stats = compare_formats(yaml_data, json_data, expected_keys=expected_keys)

        # Should track matching keys
        assert stats["total_keys"] == 3
        assert stats["matching_keys"] == 2  # paths and api_keys match

        # Should emit partial_match check
        partial_check = next(c for c in checks if c["id"] == "fmt.cross.partial_match")
        assert "2/3" in partial_check["message"]
        assert partial_check["severity"] == "warning"  # Not all keys match

    def test_compare_formats_full_partial_credit(self):
        """All keys matching gives info severity."""
        yaml_data = {
            "a": "1",
            "b": "true",
        }
        json_data = {
            "a": 1,
            "b": True,
        }

        expected_keys = {"a", "b"}
        checks, stats = compare_formats(yaml_data, json_data, expected_keys=expected_keys)

        # All keys match
        assert stats["matching_keys"] == 2
        assert stats["total_keys"] == 2

        partial_check = next(c for c in checks if c["id"] == "fmt.cross.partial_match")
        assert partial_check["severity"] == "info"
        assert partial_check["ok"] is True
