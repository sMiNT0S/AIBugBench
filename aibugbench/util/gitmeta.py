"""Lightweight git metadata helper extracted from legacy code."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

__all__ = ["resolve_git_commit"]


def _run_git(args: list[str], cwd: Path | None = None) -> str | None:
    """Run a safe, fixed git subcommand and return stripped stdout or None.

    Security considerations:
    - Command is always the literal executable "git" plus caller-provided *args*.
      The caller controls *args* but only with trusted internal usage (no user
      input passes through unvalidated in current code paths).
    - We do not use shell=True.
    - Justify ignores: S603 (subprocess use) and S607 (partial path) — relying
      on PATH resolution for standard developer tooling (git) is acceptable in
      this context.
    """
    try:
        git_exe = shutil.which("git")
        if not git_exe:
            return None
        result = subprocess.run(  # noqa: S603
            [git_exe, *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # pragma: no cover - git may be absent
        return None
    return None


def resolve_git_commit(repo_root: Path | None = None) -> str | None:
    """Return short commit hash for the repository at *repo_root* (or cwd)."""
    return _run_git(["rev-parse", "--short", "HEAD"], cwd=repo_root)
