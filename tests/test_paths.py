"""Tests for aibugbench.io.paths helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from aibugbench.io.paths import project_root


def test_project_root_detects_git(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.chdir(repo)
    assert project_root() == repo


def test_project_root_detects_pyproject(tmp_path, monkeypatch):
    repo = tmp_path / "repo2"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[build-system]\n", newline="\n")
    child = repo / "subdir/inner"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    assert project_root() == repo


def test_project_root_failure(monkeypatch):
    """project_root should raise when no marker (.git or pyproject.toml) exists.

    We intentionally avoid pytest's tmp_path here because the suite config sets
    a --basetemp inside the repository ('.pytest_tmp'), which would cause
    `project_root()` to discover the real repo root (containing a marker) and
    thus NOT raise. Using a system TemporaryDirectory ensures we are outside
    the repository tree so the ascent terminates at the filesystem root.
    """
    with TemporaryDirectory() as td:
        p = Path(td)
        # Sanity guard: ensure no marker exists in this temp subtree
        assert not any((p / m).exists() for m in (".git", "pyproject.toml"))
        monkeypatch.chdir(p)
        with pytest.raises(FileNotFoundError):
            project_root()
