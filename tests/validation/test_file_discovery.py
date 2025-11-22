# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Tests for validation.utils.file_discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from aibugbench.validation.errors import SchemaError
from aibugbench.validation.utils import find_prompt2_files
from aibugbench.validation.utils.file_discovery import JSON_NAME, YAML_NAME


def _write_pair(root: Path) -> None:
    (root / YAML_NAME).write_text("key: value\n", encoding="utf-8")
    (root / JSON_NAME).write_text("{}", encoding="utf-8")


def test_find_prompt2_files_success(tmp_path: Path):
    _write_pair(tmp_path)
    yaml_path, json_path = find_prompt2_files(tmp_path)
    assert yaml_path == tmp_path / YAML_NAME
    assert json_path == tmp_path / JSON_NAME


def test_find_prompt2_files_missing_yaml(tmp_path: Path):
    (tmp_path / JSON_NAME).write_text("{}", encoding="utf-8")
    with pytest.raises(SchemaError):
        find_prompt2_files(tmp_path)


def test_find_prompt2_files_missing_json(tmp_path: Path):
    (tmp_path / YAML_NAME).write_text("key: value\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        find_prompt2_files(tmp_path)


def test_find_prompt2_files_wrong_extension(tmp_path: Path):
    (tmp_path / "prompt_2_config_fixed.yml").write_text("key: value\n", encoding="utf-8")
    (tmp_path / JSON_NAME).write_text("{}", encoding="utf-8")
    with pytest.raises(SchemaError):
        find_prompt2_files(tmp_path)
