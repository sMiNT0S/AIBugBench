"""Tests for aibugbench.util.gitmeta.resolve_git_commit with safe mocks."""

from __future__ import annotations

from pathlib import Path

import pytest

from aibugbench.util import gitmeta


@pytest.mark.unit
def test_resolve_git_commit_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Pretend git exists
    monkeypatch.setattr(gitmeta.shutil, "which", lambda name: "/usr/bin/git")

    # Fake subprocess.run returning a short hash
    class DummyCompleted:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = "abc123\n"
            self.stderr = ""

    def fake_run(cmd, cwd=None, capture_output=True, text=True, check=False):
        assert cmd[:2] == ["/usr/bin/git", "rev-parse"]
        return DummyCompleted()

    monkeypatch.setattr(gitmeta.subprocess, "run", fake_run)

    got = gitmeta.resolve_git_commit(repo_root=tmp_path)
    assert got == "abc123"


@pytest.mark.unit
def test_resolve_git_commit_no_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Simulate missing git in PATH
    monkeypatch.setattr(gitmeta.shutil, "which", lambda name: None)
    assert gitmeta.resolve_git_commit(repo_root=tmp_path) is None
