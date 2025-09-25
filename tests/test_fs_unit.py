"""Unit tests for aibugbench.io.fs helpers (text/json/toml/yaml)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aibugbench.io import fs


@pytest.mark.unit
def test_write_and_read_text_normalizes_newlines(tmp_path: Path):
    p = tmp_path / "file.txt"
    fs.write_text(p, "a\r\nb\rc\n")
    data = fs.read_text(p)
    assert data == "a\nb\nc\n"  # normalized to LF


@pytest.mark.unit
def test_atomic_write_json_and_load_json(tmp_path: Path):
    p = tmp_path / "data.json"
    obj = {"z": 1, "a": [1, 2, 3]}
    fs.atomic_write_json(p, obj)
    loaded = fs.load_json(p)
    assert loaded == obj


@pytest.mark.unit
def test_loaders_graceful_on_missing(tmp_path: Path):
    assert fs.load_json(tmp_path / "missing.json") is None
    assert fs.load_toml(tmp_path / "missing.toml") is None
    assert fs.load_yaml(tmp_path / "missing.yml") is None


@pytest.mark.unit
def test_atomic_write_text(tmp_path: Path):
    p = tmp_path / "dir" / "note.txt"
    fs.atomic_write_text(p, "hello")
    assert fs.read_text(p) == "hello"
