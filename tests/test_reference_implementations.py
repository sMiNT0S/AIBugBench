"""Tests for reference implementations (Phase 3)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REF_DIR = Path("submissions/reference_implementations")


class TestReferenceImplementations:
    """Test suite for reference implementations.

    These tests are gating (must pass in CI).
    """

    def test_structure_exists(self) -> None:
        assert REF_DIR.exists(), "reference_implementations directory missing"
        assert REF_DIR.is_dir()

    def test_required_files_present(self) -> None:
        # Adapt dynamically to model directories
        for model_dir in REF_DIR.iterdir():
            if not model_dir.is_dir():
                continue
            expected = {
                "prompt_1_solution.py",
                "prompt_2_config.json",
                "prompt_2_config_fixed.yaml",
            }
            # Allow either a transform or regex artifact depending on prompt evolution
            # Accept presence of either prompt_3_transform.py OR prompt_3_regex_fixed.txt
            # plus subsequent prompt_4_api_sync.py where applicable.
            available = {p.name for p in model_dir.iterdir() if p.is_file()}
            missing_core = expected - available
            assert not missing_core, f"Missing core files in {model_dir.name}: {missing_core}"
            assert any(
                name in available for name in {"prompt_3_transform.py", "prompt_3_regex_fixed.txt"}
            ), "Expected a prompt 3 artifact (transform or regex)."

    def test_python_files_compile(self) -> None:
        for py_file in REF_DIR.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            # Using compile purely to validate syntax of reference python files.
            compile(source, str(py_file), "exec")

    def test_json_files_valid(self) -> None:
        for json_file in REF_DIR.rglob("*.json"):
            with json_file.open(encoding="utf-8") as fh:
                json.load(fh)

    def test_yaml_files_valid(self) -> None:
        for yaml_file in REF_DIR.rglob("*.yaml"):
            with yaml_file.open(encoding="utf-8") as fh:
                yaml.safe_load(fh)

    @pytest.mark.parametrize(
        "path",
        [
            "prompt_1_solution.py",
            "prompt_3_transform.py",
            "prompt_4_api_sync.py",
        ],
    )
    def test_reference_python_no_noqa(self, path: str) -> None:
        # Ensure we didn't reintroduce blanket suppressions.
        # Allow security-specific noqa comments for intentional test patterns
        for py in REF_DIR.rglob(path):
            content = py.read_text(encoding="utf-8")
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if "# noqa" in line:
                    # Allow security-specific noqa for test tokens and intentional patterns
                    allowed_patterns = [
                        "# noqa: S105",  # Hardcoded passwords in test examples
                        "# noqa: S603",  # Subprocess calls in examples
                    ]
                    if not any(pattern in line for pattern in allowed_patterns):
                        raise AssertionError(
                            f"Unexpected noqa in {py}:{line_num}: {line.strip()}\n"
                            f"Only security-specific noqa comments are allowed in reference implementations"
                        )

