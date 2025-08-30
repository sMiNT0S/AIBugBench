"""Informational tests for templates (Phase 3).

These are non-blocking in CI (continue-on-error job).
"""
from __future__ import annotations

from pathlib import Path

TEMPLATES_DIR = Path("submissions/templates")


class TestTemplates:
    def test_structure_exists(self) -> None:
        assert TEMPLATES_DIR.exists(), "templates directory missing"
        assert TEMPLATES_DIR.is_dir()

    def test_template_files(self) -> None:
        template = TEMPLATES_DIR / "template"
        if not template.exists():  # Graceful if absent
            return
        expected = {
            "prompt_1_solution.py",
            "prompt_2_config.json",
            "prompt_2_config_fixed.yaml",
        }
        available = {p.name for p in template.iterdir() if p.is_file()}
        missing = expected - available
        assert not missing, f"Missing template core files: {missing}"
        assert any(
            name in available for name in {"prompt_3_transform.py", "prompt_3_regex_fixed.txt"}
        ), "Expected a prompt 3 artifact (transform or regex)."
