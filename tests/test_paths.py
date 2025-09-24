"""Tests for aibugbench.io.paths helpers."""

from __future__ import annotations

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
    (repo / "pyproject.toml").write_text("[build-system]\n")
    child = repo / "subdir/inner"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    assert project_root() == repo


@pytest.mark.xfail(strict=True, reason="No markers present should raise")
def test_project_root_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project_root()
