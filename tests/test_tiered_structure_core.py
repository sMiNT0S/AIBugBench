# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Core tests for tiered submissions directory structure implementation."""

from pathlib import Path
import tempfile

import pytest

from run_benchmark import AICodeBenchmark


class TestTieredStructureCore:
    """Core tests for tiered submissions structure functionality."""

    @pytest.fixture
    def temp_submissions_dir(self):
        """Create temporary submissions directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submissions_dir = temp_path / "submissions"
            submissions_dir.mkdir()
            yield submissions_dir

    def test_model_discovery_new_layout(self, temp_submissions_dir):
        """Test model discovery works correctly with new tiered layout."""
        # Create new tiered structure
        ref_dir = temp_submissions_dir / "reference_implementations"
        user_dir = temp_submissions_dir / "user_submissions"
        templates_dir = temp_submissions_dir / "templates"

        ref_dir.mkdir()
        user_dir.mkdir()
        templates_dir.mkdir()

        # Add models to both tiers
        (ref_dir / "example_model").mkdir()
        (ref_dir / "baseline_model").mkdir()
        (user_dir / "user_model_1").mkdir()
        (user_dir / "user_model_2").mkdir()

        # Add template (should be excluded from discovery)
        (templates_dir / "template").mkdir()

        # Create benchmark instance
        benchmark = AICodeBenchmark(str(temp_submissions_dir), "results")

        # Test model discovery
        models = benchmark.discover_models()

        # Should find models from both reference and user tiers
        expected_models = ["baseline_model", "example_model", "user_model_1", "user_model_2"]
        assert sorted(models) == expected_models

        # Should not include template
        assert "template" not in models

    def test_legacy_layout_rejection(self, temp_submissions_dir):
        """Test legacy layout presence raises SystemExit with migration guidance."""
        # Create legacy structure only
        legacy_example = temp_submissions_dir / "example_model"
        legacy_template = temp_submissions_dir / "template"
        legacy_example.mkdir()
        legacy_template.mkdir()

        # Ensure no tiered directories exist
        assert not (temp_submissions_dir / "reference_implementations").exists()
        assert not (temp_submissions_dir / "user_submissions").exists()
        assert not (temp_submissions_dir / "templates").exists()

        # Create benchmark instance
        benchmark = AICodeBenchmark(str(temp_submissions_dir), "results")

        # Should raise SystemExit with migration guidance
        with pytest.raises(SystemExit) as exc:
            benchmark.discover_models()

        msg = str(exc.value)
        assert msg.startswith("Legacy submissions layout detected")
        assert "reference_implementations/example_model" in msg

    def test_user_submissions_isolation(self, temp_submissions_dir):
        """Test user submissions are discovered but logically isolated."""
        # Create tiered structure
        ref_dir = temp_submissions_dir / "reference_implementations"
        user_dir = temp_submissions_dir / "user_submissions"

        ref_dir.mkdir()
        user_dir.mkdir()

        # Add models to both tiers
        (ref_dir / "reference_model").mkdir()
        (user_dir / "user_model").mkdir()

        # Create benchmark instance
        benchmark = AICodeBenchmark(str(temp_submissions_dir), "results")

        # Test path resolution isolates tiers correctly
        ref_path = benchmark._resolve_model_path("reference_model")
        user_path = benchmark._resolve_model_path("user_model")

        # Should resolve to correct tier locations
        assert ref_path is not None
        assert "reference_implementations" in str(ref_path)
        assert user_path is not None
        assert "user_submissions" in str(user_path)

        # Models should be discoverable from both tiers
        models = benchmark.discover_models()
        assert "reference_model" in models
        assert "user_model" in models

    def test_empty_structure_error(self, temp_submissions_dir, capsys):
        """Test appropriate error handling when no models exist."""
        # Create empty tiered structure
        ref_dir = temp_submissions_dir / "reference_implementations"
        user_dir = temp_submissions_dir / "user_submissions"
        templates_dir = temp_submissions_dir / "templates"

        ref_dir.mkdir()
        user_dir.mkdir()
        templates_dir.mkdir()

        # Create benchmark instance
        benchmark = AICodeBenchmark(str(temp_submissions_dir), "results")

        # Test model discovery with empty structure
        models = benchmark.discover_models()

        # Should return empty list
        assert models == []

        # Test run_all_models handles empty case gracefully
        results = benchmark.run_all_models()

        # Should return error structure
        assert "error" in results
        assert results["error"] == "No models found"

        # Check for appropriate error message
        captured = capsys.readouterr()
        assert "No models found in submissions directory" in captured.out

    def test_model_path_resolution_priority(self, temp_submissions_dir):
        """Test model path resolution follows correct priority order."""
        # Create model with same name in multiple locations
        ref_dir = temp_submissions_dir / "reference_implementations"
        user_dir = temp_submissions_dir / "user_submissions"
        ref_dir.mkdir()
        user_dir.mkdir()

        # Add same model name to both locations
        (ref_dir / "test_model").mkdir()
        (user_dir / "test_model").mkdir()

        benchmark = AICodeBenchmark(str(temp_submissions_dir), "results")

        # Should resolve to reference_implementations first (highest priority)
        resolved_path = benchmark._resolve_model_path("test_model")
        assert "reference_implementations" in str(resolved_path)

        # Remove reference model, should find user model
        import shutil

        shutil.rmtree(ref_dir / "test_model")

        resolved_path = benchmark._resolve_model_path("test_model")
        assert "user_submissions" in str(resolved_path)

    # ---- Consolidated former phase2 tests below (discovery summary & legacy edge cases) ----

    def _make_basic_tiered(self, base: Path, with_template: bool = True) -> None:
        (base / "reference_implementations").mkdir()
        (base / "user_submissions").mkdir()
        templates_dir = base / "templates"
        templates_dir.mkdir()
        if with_template:
            (templates_dir / "template").mkdir()

    def test_discovery_summary_line(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir)
        (temp_submissions_dir / "reference_implementations" / "ref_model").mkdir()
        (temp_submissions_dir / "user_submissions" / "user_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert sorted(models) == ["ref_model", "user_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=1 templates=OK" in out

    def test_missing_template_marker(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir, with_template=False)
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        bench.discover_models()
        out = capsys.readouterr().out
        assert "templates=MISSING" in out

    def test_discovery_multiple_models_format(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir)
        ref_dir = temp_submissions_dir / "reference_implementations"
        user_dir = temp_submissions_dir / "user_submissions"
        for name in ["model_a", "model_b", "model_c"]:
            (ref_dir / name).mkdir()
        for name in ["user_x", "user_y"]:
            (user_dir / name).mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert sorted(models) == ["model_a", "model_b", "model_c", "user_x", "user_y"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=3 user=2 templates=OK" in out

    def test_discovery_single_model_format(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir)
        (temp_submissions_dir / "reference_implementations" / "solo_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["solo_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out

    def test_edge_case_templates_dir_missing(self, capsys, temp_submissions_dir):
        # Only reference + user, no templates dir
        (temp_submissions_dir / "reference_implementations").mkdir()
        (temp_submissions_dir / "user_submissions").mkdir()
        (temp_submissions_dir / "reference_implementations" / "test_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["test_model"]
        out = capsys.readouterr().out
        assert "templates=MISSING" in out

    def test_edge_case_empty_reference_implementations(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir)
        (temp_submissions_dir / "user_submissions" / "user_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["user_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=1 templates=OK" in out

    def test_edge_case_empty_user_submissions(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir)
        (temp_submissions_dir / "reference_implementations" / "ref_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["ref_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out

    def test_edge_case_user_submissions_dir_missing(self, capsys, temp_submissions_dir):
        (temp_submissions_dir / "reference_implementations").mkdir()
        (temp_submissions_dir / "templates").mkdir()
        (temp_submissions_dir / "templates" / "template").mkdir()
        (temp_submissions_dir / "reference_implementations" / "ref_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["ref_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out

    def test_edge_case_reference_implementations_dir_missing(self, capsys, temp_submissions_dir):
        (temp_submissions_dir / "user_submissions").mkdir()
        (temp_submissions_dir / "templates").mkdir()
        (temp_submissions_dir / "templates" / "template").mkdir()
        (temp_submissions_dir / "user_submissions" / "user_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == ["user_model"]
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=1 templates=OK" in out

    def test_edge_case_all_tiers_empty(self, capsys, temp_submissions_dir):
        self._make_basic_tiered(temp_submissions_dir, with_template=False)
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert models == []
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=0 templates=MISSING" in out

    def test_legacy_error_message_completeness(self, temp_submissions_dir):
        # Legacy structure present (no tiered dirs)
        (temp_submissions_dir / "example_model").mkdir()
        (temp_submissions_dir / "template").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()
        error_msg = str(exc_info.value)
        assert error_msg.startswith("Legacy submissions layout detected")
        assert "Legacy support was removed before public release" in error_msg
        assert "Please migrate to:" in error_msg
        assert "reference_implementations/example_model" in error_msg
        assert "templates/template" in error_msg
        assert "user_submissions" in error_msg

    def test_legacy_error_message_example_only(self, temp_submissions_dir):
        (temp_submissions_dir / "example_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()
        error_msg = str(exc_info.value)
        assert "Legacy submissions layout detected" in error_msg
        assert "reference_implementations/example_model" in error_msg

    def test_legacy_error_message_template_only(self, temp_submissions_dir):
        (temp_submissions_dir / "template").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()
        error_msg = str(exc_info.value)
        assert "Legacy submissions layout detected" in error_msg
        assert "templates/template" in error_msg

    def test_mixed_legacy_and_tiered_no_error(self, capsys, temp_submissions_dir):
        # Both legacy & tiered structure present -> tiered takes precedence
        (temp_submissions_dir / "example_model").mkdir()
        (temp_submissions_dir / "template").mkdir()
        self._make_basic_tiered(temp_submissions_dir)
        (temp_submissions_dir / "reference_implementations" / "new_model").mkdir()
        bench = AICodeBenchmark(str(temp_submissions_dir), "results")
        models = bench.discover_models()
        assert "new_model" in models
        assert "example_model" not in models
        assert "template" not in models
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out
