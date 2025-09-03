"""Unit tests for newly extracted validation core helpers.

These focus on pure parsing / classification logic to raise coverage without
invoking subprocesses or performing I/O heavy operations.
"""

from pathlib import Path

from validation.docs_core import DocumentationValidator
from validation.security_core import check_security_files


def test_docs_core_extract_basic(tmp_path: Path):
    text = """Some intro
```bash
python run_benchmark.py --help
echo done \
 && echo second
```
```cmd
dir
```
"""
    validator = DocumentationValidator(project_root=tmp_path)
    commands = validator.extract_commands_from_text(text, tmp_path / "README.md")
    # Expect 3 commands: python, echo chain collapsed, dir
    extracted = [c.content for c in commands]
    assert any(c.startswith("python run_benchmark.py") for c in extracted)
    assert any(
        c.startswith("echo done  && echo second") or c.startswith("echo done && echo second")
        for c in extracted
    )
    assert any(c.lower() == "dir" for c in extracted)


def test_security_core_file_presence(tmp_path: Path, monkeypatch):
    # Simulate project root missing most files
    monkeypatch.setattr("validation.security_core.PROJECT_ROOT", tmp_path)
    # Create one file to verify detection
    (tmp_path / ".github").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".github" / "dependabot.yml").write_text("version: 2", encoding="utf-8")
    results = check_security_files()
    assert results[".github/dependabot.yml"] is True
    # At least one expected missing
    assert any(not v for k, v in results.items() if k != ".github/dependabot.yml")
