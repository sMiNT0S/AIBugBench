"""Tests for repo_audit.list_files hidden directory handling.

Ensures that:
- Hidden directories (and their files) are skipped by default
- Hidden files in normal dirs are skipped by default
- When include_hidden_dirs=True both hidden dirs and hidden files are included
- Explicit SKIP_DIRS are always skipped
"""

from pathlib import Path

import pytest

from validation.repo_audit_enhanced import SKIP_DIRS, list_files


def write(p: Path, content: str = "test") -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


@pytest.mark.unit
def test_list_files_hidden_directories_skipped_by_default(temp_dir: Path):
    # Layout
    visible = write(temp_dir / "src" / "a.py")
    hidden_dir_file = write(temp_dir / ".hidden" / "b.py")
    hidden_file = write(temp_dir / "src" / ".c.py")

    # Act
    result = list_files(temp_dir, (".py",))

    # Assert: only visible a.py present
    assert visible in result
    assert hidden_dir_file not in result
    assert hidden_file not in result


@pytest.mark.unit
def test_list_files_hidden_included_when_flag_true(temp_dir: Path):
    visible = write(temp_dir / "src" / "a.py")
    hidden_dir_file = write(temp_dir / ".hidden" / "b.py")
    hidden_file = write(temp_dir / "src" / ".c.py")

    result = list_files(temp_dir, (".py",), include_hidden_dirs=True)

    assert visible in result
    assert hidden_dir_file in result
    assert hidden_file in result


@pytest.mark.unit
def test_list_files_respects_skip_dirs(temp_dir: Path):
    # Pick one known skip dir or create a custom one to simulate; use first entry
    skip_dir_name = next(iter(SKIP_DIRS)) if SKIP_DIRS else "__pycache__"
    skip_file = write(temp_dir / skip_dir_name / "skip_me.py")
    normal_file = write(temp_dir / "normal" / "keep.py")

    result = list_files(temp_dir, (".py",), include_hidden_dirs=True)

    assert normal_file in result
    assert skip_file not in result


@pytest.mark.unit
def test_list_files_no_extensions(temp_dir: Path):
    write(temp_dir / "x.py")
    result = list_files(temp_dir, ())
    assert result == []
