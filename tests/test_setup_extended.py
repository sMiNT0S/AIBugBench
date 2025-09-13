"""Extended tests for setup.py to improve coverage of helper functions and main flow.

Covers:
 - use_safe_unicode() branches (isatty false, limited encodings)
 - display_ai_prompt() skip, safe mode, and unicode mode branches
 - create_directory_structure() directory creation
 - create_test_data() fixture file generation
 - create_template_files() template generation
 - create_requirements_txt() base requirements file
 - __main__ bootstrap guard execution path (via runpy)
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent


def _import_setup(repo_root: Path):
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    import importlib

    return importlib.import_module("setup")


def test_use_safe_unicode_branches(repo_root, tmp_path, monkeypatch):
    setup = _import_setup(repo_root)

    # Case 1: piped output (isatty False) -> expect True (safe fallback)
    fake_stdout = SimpleNamespace(isatty=lambda: False, encoding="utf-8")
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    assert setup.use_safe_unicode() is True

    # Case 2: interactive but limited encoding cp1252 -> True
    fake_stdout = SimpleNamespace(isatty=lambda: True, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    assert setup.use_safe_unicode() is True

    # Case 3: interactive utf-8 and emoji supported -> False
    fake_stdout = SimpleNamespace(isatty=lambda: True, encoding="utf-8", write=lambda *_: None)
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    assert setup.use_safe_unicode() is False


def test_display_ai_prompt_skip_noninteractive(repo_root, monkeypatch):
    setup = _import_setup(repo_root)
    monkeypatch.setenv("AIBUGBENCH_NONINTERACTIVE", "1")
    buf = StringIO()
    fake_tty = SimpleNamespace(isatty=lambda: True, encoding="utf-8", write=buf.write)
    monkeypatch.setattr(sys, "stdout", fake_tty)
    monkeypatch.setattr(sys, "stdin", fake_tty)
    setup.display_ai_prompt()  # Should early-return silently
    assert buf.getvalue() == ""


def test_display_ai_prompt_safe_mode(repo_root, monkeypatch):
    setup = _import_setup(repo_root)
    # Ensure no early skip
    monkeypatch.delenv("AIBUGBENCH_NONINTERACTIVE", raising=False)
    buf = StringIO()
    fake_stdout = SimpleNamespace(isatty=lambda: True, encoding="utf-8", write=buf.write)
    fake_stdin = SimpleNamespace(isatty=lambda: True)
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    monkeypatch.setattr(sys, "stdin", fake_stdin)
    monkeypatch.setattr(setup, "use_safe_unicode", lambda: True)
    # Avoid waiting for input by forcing non-interactive branch second guard
    monkeypatch.setenv("CI", "1")
    setup.display_ai_prompt()
    out = buf.getvalue()
    assert "[TARGET] WHAT IS AIBUGBENCH?" in out
    assert "🎯" not in out  # No emoji in safe mode


def test_display_ai_prompt_unicode_mode(repo_root, monkeypatch):
    setup = _import_setup(repo_root)
    buf = StringIO()
    fake_stdout = SimpleNamespace(isatty=lambda: True, encoding="utf-8", write=buf.write)
    fake_stdin = SimpleNamespace(isatty=lambda: True)
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    monkeypatch.setattr(sys, "stdin", fake_stdin)
    monkeypatch.setattr(setup, "use_safe_unicode", lambda: False)
    # Patch input so interactive branch executes without blocking
    with patch("builtins.input", return_value=""):
        setup.display_ai_prompt()
    out = buf.getvalue()
    assert "🎯 WHAT IS AIBUGBENCH?" in out
    assert "Press Enter" in out


def test_create_directory_structure(repo_root, tmp_path, monkeypatch):
    setup = _import_setup(repo_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup, "use_safe_unicode", lambda: True)
    setup.create_directory_structure()
    expected_dirs = [
        "benchmark",
        "test_data",
        "prompts",
        "submissions/templates/template",
        "submissions/reference_implementations",
        "submissions/user_submissions",
        "results",
    ]
    for d in expected_dirs:
        assert (tmp_path / d).exists(), f"Missing expected directory {d}"


def test_create_test_data(repo_root, tmp_path, monkeypatch):
    setup = _import_setup(repo_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup, "use_safe_unicode", lambda: True)
    # Minimal prerequisite directory
    (tmp_path / "test_data").mkdir(parents=True, exist_ok=True)
    setup.create_test_data()
    assert (tmp_path / "test_data" / "process_records.py").exists()
    assert (tmp_path / "test_data" / "config.yaml").exists()
    user_json = tmp_path / "test_data" / "user_data.json"
    assert user_json.exists()
    # Validate JSON structure loads
    import json

    json.loads(user_json.read_text(encoding="utf-8"))


def test_create_template_files(repo_root, tmp_path, monkeypatch):
    setup = _import_setup(repo_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(setup, "use_safe_unicode", lambda: True)
    setup.create_template_files()
    template_dir = tmp_path / "submissions" / "templates" / "template"
    for filename in [
        "prompt_1_solution.py",
        "prompt_2_config_fixed.yaml",
        "prompt_2_config.json",
        "prompt_3_transform.py",
        "prompt_4_api_sync.py",
    ]:
        assert (template_dir / filename).exists(), f"Template {filename} missing"


def test_create_requirements_txt(repo_root, tmp_path, monkeypatch):
    setup = _import_setup(repo_root)
    monkeypatch.chdir(tmp_path)
    setup.create_requirements_txt()
    req = (tmp_path / "requirements.txt").read_text(encoding="utf-8").strip().splitlines()
    assert req[0] == "# AI Code Benchmark Requirements"
    assert "pyyaml" in req[1]
    assert "requests" in req[2]


def test_run_module_main_guard(repo_root, tmp_path, monkeypatch):
    # Simulate environment and ensure bootstrap path executes without interactive pause
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIBUGBENCH_BOOTSTRAP", "1")
    monkeypatch.setenv("AIBUGBENCH_NONINTERACTIVE", "1")  # Force display_ai_prompt early skip
    # Ensure repo root import path
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    # Run setup as a script (__main__) to exercise guard
    runpy.run_path(str(repo_root / "setup.py"), run_name="__main__")
    # Spot check: directories and files created
    assert (tmp_path / "prompts" / "ai_prompt.md").exists()
    assert (tmp_path / "requirements.txt").exists()
    assert (tmp_path / "test_data" / "user_data.json").exists()
