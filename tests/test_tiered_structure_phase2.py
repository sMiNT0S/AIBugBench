"""
Phase 2 tests expanding coverage of tiered submissions structure.

Focus:
- Discovery summary line correctness
- Exact legacy layout error message content
- Behavior when templates/template missing (should still run but summary shows MISSING)
"""
from pathlib import Path
import tempfile

import pytest

from run_benchmark import AICodeBenchmark


def make_basic_tiered(submissions_dir: Path, with_template: bool = True) -> None:
    (submissions_dir / "reference_implementations").mkdir()
    (submissions_dir / "user_submissions").mkdir()
    templates_dir = submissions_dir / "templates"
    templates_dir.mkdir()
    if with_template:
        (templates_dir / "template").mkdir()


def test_discovery_summary_line(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base)
        # Add models
        (base / "reference_implementations" / "ref_model").mkdir()
        (base / "user_submissions" / "user_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()
        assert sorted(models) == ["ref_model", "user_model"]
        out = capsys.readouterr().out
        # Summary format: Discovered models: reference=<n> user=<n> templates=OK
        assert "Discovered models: reference=1 user=1 templates=OK" in out


def test_legacy_error_exact_message():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        # Legacy only
        (base / "example_model").mkdir()
        (base / "template").mkdir()
        bench = AICodeBenchmark(str(base), "results")
        with pytest.raises(SystemExit) as exc:
            bench.discover_models()
        msg = str(exc.value)
        # Ensure key fragments present (maintain stable wording for docs/tests)
        assert msg.startswith("Legacy submissions layout detected")
        assert "Legacy support was removed before public release" in msg
        assert "reference_implementations/example_model" in msg
        assert msg.strip().endswith("user_submissions/")


def test_missing_template_marker(capsys):
    """Test discovery output shows MISSING when templates/template doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base, with_template=False)
        bench = AICodeBenchmark(str(base), "results")
        bench.discover_models()
        out = capsys.readouterr().out
        assert "templates=MISSING" in out


def test_discovery_multiple_models_format(capsys):
    """Test discovery summary format with multiple models in each tier."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base)

        # Add multiple models to each tier
        ref_dir = base / "reference_implementations"
        user_dir = base / "user_submissions"
        (ref_dir / "model_a").mkdir()
        (ref_dir / "model_b").mkdir()
        (ref_dir / "model_c").mkdir()
        (user_dir / "user_x").mkdir()
        (user_dir / "user_y").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        # Should find all models sorted
        expected = ["model_a", "model_b", "model_c", "user_x", "user_y"]
        assert sorted(models) == expected

        # Check exact discovery summary format
        out = capsys.readouterr().out
        assert "Discovered models: reference=3 user=2 templates=OK" in out


def test_discovery_single_model_format(capsys):
    """Test discovery summary format with single model."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base)

        # Add single model to reference tier only
        (base / "reference_implementations" / "solo_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["solo_model"]

        # Check exact discovery summary format
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out


def test_edge_case_templates_dir_missing(capsys):
    """Test when templates directory is completely missing."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create only reference and user dirs, no templates dir
        (base / "reference_implementations").mkdir()
        (base / "user_submissions").mkdir()
        (base / "reference_implementations" / "test_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["test_model"]

        # Should show MISSING when templates dir doesn't exist
        out = capsys.readouterr().out
        assert "templates=MISSING" in out


def test_edge_case_empty_reference_implementations(capsys):
    """Test when reference_implementations exists but is empty."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base)

        # Add only user models, keep reference empty
        (base / "user_submissions" / "user_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["user_model"]

        # Should show 0 reference models
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=1 templates=OK" in out


def test_edge_case_empty_user_submissions(capsys):
    """Test when user_submissions exists but is empty."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base)

        # Add only reference models, keep user empty
        (base / "reference_implementations" / "ref_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["ref_model"]

        # Should show 0 user models
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out


def test_edge_case_user_submissions_dir_missing(capsys):
    """Test when user_submissions directory is completely missing."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create only reference and templates dirs
        (base / "reference_implementations").mkdir()
        (base / "templates").mkdir()
        (base / "templates" / "template").mkdir()
        (base / "reference_implementations" / "ref_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["ref_model"]

        # Should show 0 user models when dir missing
        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out


def test_edge_case_reference_implementations_dir_missing(capsys):
    """Test when reference_implementations directory is completely missing."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create only user and templates dirs
        (base / "user_submissions").mkdir()
        (base / "templates").mkdir()
        (base / "templates" / "template").mkdir()
        (base / "user_submissions" / "user_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == ["user_model"]

        # Should show 0 reference models when dir missing
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=1 templates=OK" in out


def test_edge_case_all_tiers_empty(capsys):
    """Test when all tier directories exist but are completely empty."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()
        make_basic_tiered(base, with_template=False)  # No template either

        bench = AICodeBenchmark(str(base), "results")
        models = bench.discover_models()

        assert models == []

        # Should show all zeros and MISSING
        out = capsys.readouterr().out
        assert "Discovered models: reference=0 user=0 templates=MISSING" in out


def test_legacy_error_message_completeness():
    """Test legacy error message includes all required migration guidance."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create legacy structure with both example_model and template
        (base / "example_model").mkdir()
        (base / "template").mkdir()

        bench = AICodeBenchmark(str(base), "results")

        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()

        error_msg = str(exc_info.value)

        # Verify all key components of error message
        assert error_msg.startswith("Legacy submissions layout detected")
        assert "Legacy support was removed before public release" in error_msg
        assert "Please migrate to:" in error_msg
        assert "submissions/" in error_msg
        assert "reference_implementations/example_model/" in error_msg
        assert "templates/template/" in error_msg
        assert "user_submissions/" in error_msg

        # Ensure message is actionable and complete
        assert "example_model" in error_msg  # References the detected legacy structure


def test_legacy_error_message_example_only():
    """Test legacy error triggers with only example_model present."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create legacy structure with only example_model
        (base / "example_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")

        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()

        error_msg = str(exc_info.value)
        assert "Legacy submissions layout detected" in error_msg
        assert "reference_implementations/example_model/" in error_msg


def test_legacy_error_message_template_only():
    """Test legacy error triggers with only template present."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create legacy structure with only template
        (base / "template").mkdir()

        bench = AICodeBenchmark(str(base), "results")

        with pytest.raises(SystemExit) as exc_info:
            bench.discover_models()

        error_msg = str(exc_info.value)
        assert "Legacy submissions layout detected" in error_msg
        assert "templates/template/" in error_msg


def test_mixed_legacy_and_tiered_no_error(capsys):
    """Test no legacy error when tiered structure is detected alongside legacy."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        base.mkdir()

        # Create both legacy and tiered structures
        (base / "example_model").mkdir()  # Legacy
        (base / "template").mkdir()       # Legacy
        make_basic_tiered(base)           # Tiered
        (base / "reference_implementations" / "new_model").mkdir()

        bench = AICodeBenchmark(str(base), "results")

        # Should NOT raise SystemExit - tiered structure takes precedence
        models = bench.discover_models()

        # Should discover the tiered model, ignore legacy
        assert "new_model" in models
        assert "example_model" not in models  # Legacy ignored
        assert "template" not in models      # Legacy ignored

        out = capsys.readouterr().out
        assert "Discovered models: reference=1 user=0 templates=OK" in out
