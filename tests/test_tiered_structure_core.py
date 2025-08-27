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
