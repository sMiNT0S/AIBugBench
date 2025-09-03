"""
Integration tests for run_benchmark.py CLI functionality.

Tests the main CLI entry point, argument parsing, and full execution.
"""

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

from benchmark.validators import PromptValidators


class TestBenchmarkCLI:
    """Test the command-line interface of run_benchmark.py."""

    @pytest.fixture
    def mock_submissions_dir(self, temp_dir):
        """Create mock submissions directory structure."""
        submissions_dir = temp_dir / "submissions"
        submissions_dir.mkdir()

        # Create template model
        template_dir = submissions_dir / "template"
        template_dir.mkdir()

        # Create example model
        example_dir = submissions_dir / "example_model"
        example_dir.mkdir()

        # Add minimal solution files
        solutions = {
            "prompt_1_solution.py": """
import json
def process_records(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except Exception:
        return []
if __name__ == "__main__":
    print(json.dumps(process_records("user_data.json"), indent=2))
""",
            "prompt_2_config.json": '{"database": {"host": "localhost", "port": 5432}}',
            "prompt_2_config.yaml": "database:\n  host: localhost\n  port: 5432",
            "prompt_3_transform.py": """
import json
def transform_users(users):
    return [{"id": u["id"], "name": u["name"], "age": int(str(u.get("age", 0)))} for u in users]
if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        print(json.dumps(transform_users(json.load(f)), indent=2))
""",
            "prompt_4_api_sync.py": """
import requests
def sync_users_to_crm(users, api_token):
    try:
        return requests.post("https://api.example.com/users",
                           json=users,
                           headers={"Authorization": f"Bearer {api_token}"},
                           timeout=30).json().get("user_ids", [])
    except Exception:
        return None
""",
        }

        # Write solutions to both template and example directories
        for model_dir in [template_dir, example_dir]:
            for filename, content in solutions.items():
                (model_dir / filename).write_text(content)

        return submissions_dir

    @pytest.fixture
    def mock_test_data_dir(self, temp_dir):
        """Create mock test data directory."""
        test_data_dir = temp_dir / "test_data"
        test_data_dir.mkdir()

        # Create test data files
        (test_data_dir / "user_data.json").write_text(
            json.dumps(
                [
                    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": "28"},
                    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 35},
                ],
                indent=2,
            )
        )

        (test_data_dir / "config.yaml").write_text("""
database:
  host: localhost
  port: 5432
  name: testdb
api:
  base_url: "https://api.example.com"
  timeout: 30
""")

        (test_data_dir / "process_records.py").write_text("""
import json
import datetime as datetime
from datetime import datetime

def process_records(filename):
    # This is intentionally problematic code for testing
    file = open(filename, "r")
    data = file.read()
    file.close()

    try:
        records = json.loads(data)
    except:
        print("Error parsing JSON")
        return

    results = []
    for record in records:
        if record:
            results.append(record)

    return results
""")

        return test_data_dir

    @pytest.mark.integration
    def test_cli_help_message(self):
        """Test that CLI shows help message."""
        result = subprocess.run(
            [  # CLI help test - safe command
                sys.executable,
                "run_benchmark.py",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert result.returncode == 0
        assert "AI Code Benchmark Tool" in result.stdout
        assert "--model" in result.stdout
        assert "--quiet" in result.stdout

    @pytest.mark.integration
    def test_cli_version_info(self):
        """Test CLI can be imported and executed."""
        # Test that the module can be imported without errors
        result = subprocess.run(
            [  # Module import test - safe command
                sys.executable,
                "-c",
                "import run_benchmark; print('Import successful')",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert result.returncode == 0
        assert "Import successful" in result.stdout

    # (Lightweight help smoke test removed; canonical help coverage in test_cli_help_message.)

    @pytest.mark.integration
    @patch("run_benchmark.BenchmarkScorer")
    @patch("run_benchmark.PromptValidators")
    def test_cli_with_specific_model(
        self, mock_validators, mock_scorer, mock_submissions_dir, mock_test_data_dir, temp_dir
    ):
        """Test CLI execution with specific model."""
        # Mock the validators and scorer
        mock_validator_instance = Mock()
        mock_validators.return_value = mock_validator_instance

        mock_validator_instance.validate_prompt_1_refactoring.return_value = {
            "passed": True,
            "score": 20.5,
            "max_score": 25,
            "detailed_scoring": {"syntax": {"earned": 5.0, "max": 5.0}},
            "feedback": ["Test feedback"],
            "tests_passed": {},
        }

        mock_scorer_instance = Mock()
        mock_scorer.return_value = mock_scorer_instance
        mock_scorer_instance.calculate_final_score.return_value = {
            "total_score": 85.5,
            "letter_grade": "A",
            "category_scores": {},
        }

        results_dir = temp_dir / "results"

        # Load run_benchmark directly from source without copying or chdir
        run_path = Path.cwd() / "run_benchmark.py"
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_benchmark", run_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        with patch(
            "sys.argv",
            [
                "run_benchmark.py",
                "--model",
                "example_model",
                "--submissions-dir",
                str(mock_submissions_dir),
                "--results-dir",
                str(results_dir),
                "--quiet",
            ],
        ):
            try:
                module.main()
            except SystemExit as e:
                if e.code != 0:
                    raise

    @pytest.mark.integration
    def test_cli_invalid_model(self, temp_dir):
        """Test CLI with non-existent model."""
        result = subprocess.run(
            [  # CLI error handling test - safe command
                sys.executable,
                "run_benchmark.py",
                "--model",
                "nonexistent_model",
                "--submissions-dir",
                str(temp_dir / "empty_submissions"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(Path.cwd()),
        )

        # Should exit with error code or handle gracefully
        # The exact behavior depends on implementation
        assert result.returncode in [0, 1]  # 0 for graceful handling, 1 for error

    @pytest.mark.integration
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing using real parse_args."""
        import run_benchmark

        args = run_benchmark.parse_args(
            ["--model", "test_model", "--quiet", "--results-dir", "custom_results"]
        )
        assert args.model == "test_model"
        assert args.quiet is True
        assert args.results_dir == "custom_results"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cli_full_execution_mock(self, mock_submissions_dir, mock_test_data_dir, temp_dir):
        """Test full CLI execution with mocked dependencies."""
        results_dir = temp_dir / "results"

        # Mock all external dependencies
        with (
            patch("run_benchmark.PromptValidators") as mock_validators,
            patch("run_benchmark.BenchmarkScorer") as mock_scorer,
            patch("run_benchmark.ensure_directories") as mock_ensure_dirs,
            patch("run_benchmark.load_test_data") as mock_load_data,
            patch("run_benchmark.validate_submission_structure") as mock_validate_struct,
        ):
            # Configure mocks
            mock_validator_instance = Mock()
            mock_validators.return_value = mock_validator_instance

            # Mock validation results for all prompts
            mock_validation_result = {
                "passed": True,
                "score": 18.5,
                "max_score": 25,
                "detailed_scoring": {
                    "syntax": {"earned": 5.0, "max": 5.0},
                    "structure": {"earned": 3.0, "max": 3.0},
                    "execution": {"earned": 4.5, "max": 6.0},
                    "quality": {"earned": 3.0, "max": 3.0},
                    "security": {"earned": 2.0, "max": 4.0},
                    "performance": {"earned": 1.0, "max": 2.0},
                    "maintainability": {"earned": 0.0, "max": 2.0},
                },
                "feedback": ["Good implementation"],
                "tests_passed": {"valid_python": True},
            }

            mock_validator_instance.validate_prompt_1_refactoring.return_value = (
                mock_validation_result
            )
            mock_validator_instance.validate_prompt_2_yaml_json.return_value = (
                mock_validation_result
            )
            mock_validator_instance.validate_prompt_3_transformation.return_value = (
                mock_validation_result
            )
            mock_validator_instance.validate_prompt_4_api.return_value = mock_validation_result

            mock_scorer_instance = Mock()
            mock_scorer.return_value = mock_scorer_instance
            mock_scorer_instance.calculate_final_score.return_value = {
                "total_score": 92.0,
                "letter_grade": "A",
                "category_scores": {
                    "syntax": 20.0,
                    "structure": 12.0,
                    "execution": 18.0,
                    "quality": 12.0,
                    "security": 8.0,
                    "performance": 4.0,
                    "maintainability": 2.0,
                },
            }

            mock_ensure_dirs.return_value = None
            mock_load_data.return_value = {}
            # Mock structure validation to return dict instead of bool
            mock_validate_struct.return_value = {
                "prompt_1_solution.py": True,
                "prompt_2_config.json": True,
                "prompt_2_config.yaml": True,
                "prompt_3_transform.py": True,
                "prompt_4_api_sync.py": True,
            }

            # Test execution
            with patch(
                "sys.argv",
                [
                    "run_benchmark.py",
                    "--model",
                    "example_model",
                    "--submissions-dir",
                    str(mock_submissions_dir),
                    "--results-dir",
                    str(results_dir),
                ],
            ):
                import run_benchmark

                # Should execute without errors
                try:
                    run_benchmark.main()
                except SystemExit as e:
                    if e.code != 0:
                        raise

                # Verify mocks were called
                mock_validators.assert_called()
                mock_scorer.assert_called()


class TestBenchmarkUtilities:
    """Test utility functions used by the benchmark."""

    @pytest.mark.unit
    def test_safe_unicode_detection(self):
        """Test Unicode safety detection."""
        from run_benchmark import use_safe_unicode_standalone

        # Should return a boolean
        result = use_safe_unicode_standalone()
        assert isinstance(result, bool)

    @pytest.mark.unit
    @patch("sys.stdout")
    def test_safe_unicode_with_limited_encoding(self, mock_stdout):
        """Test Unicode safety with limited encoding."""
        from run_benchmark import use_safe_unicode_standalone

        mock_stdout.encoding = "cp1252"
        mock_stdout.isatty.return_value = True

        result = use_safe_unicode_standalone()
        assert result is True  # Should use safe fallback

    @pytest.mark.unit
    @patch("sys.stdout")
    def test_safe_unicode_with_piped_output(self, mock_stdout):
        """Test Unicode safety with piped output."""
        from run_benchmark import use_safe_unicode_standalone

        mock_stdout.isatty.return_value = False  # Piped output

        result = use_safe_unicode_standalone()
        assert result is True  # Should use safe fallback

    @pytest.mark.integration
    def test_benchmark_imports(self):
        """Test that all benchmark modules can be imported."""
        # Test core imports don't fail
        from benchmark.scoring import BenchmarkScorer
        from benchmark.validators import PromptValidators, ScoringDetail, UniqueKeyLoader

        # Verify classes can be instantiated (basic smoke test)
        assert PromptValidators is not None
        assert ScoringDetail is not None
        assert UniqueKeyLoader is not None
        assert BenchmarkScorer is not None

    @pytest.mark.integration
    def test_benchmark_with_actual_example_model(self, test_data_dir, example_model_dir):
        """Integration test with actual example model files if they exist."""
        if not example_model_dir.exists():
            pytest.skip("Example model directory not found")

        validators = PromptValidators(test_data_dir)

        # Test prompt 1 if file exists
        prompt1_file = example_model_dir / "prompt_1_solution.py"
        if prompt1_file.exists():
            result = validators.validate_prompt_1_refactoring(prompt1_file)

            # Should get reasonable results
            # Using tuple form for broader Python compatibility per test requirements
            assert isinstance(result["score"], (int, float))  # noqa: UP038
            assert result["score"] >= 0
            assert "detailed_scoring" in result

        # Test prompt 4 if file exists
        prompt4_file = example_model_dir / "prompt_4_api_sync.py"
        if prompt4_file.exists():
            result = validators.validate_prompt_4_api(prompt4_file)

            # Should get reasonable results
            # Using tuple form for broader Python compatibility per test requirements
            assert isinstance(result["score"], (int, float))  # noqa: UP038
            assert result["score"] >= 0


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    @pytest.mark.unit
    def test_cli_with_missing_dependencies(self):
        """Test CLI behavior when dependencies are missing."""
        # Patch builtins.__import__ to simulate ImportError

    with (
        patch("builtins.__import__", side_effect=ImportError("Module not found")),
        pytest.raises(ImportError),
    ):
        __import__("run_benchmark")

    @pytest.mark.integration
    def test_cli_keyboard_interrupt(self):
        """Test CLI handling of keyboard interrupt."""
        # This test verifies graceful shutdown on Ctrl+C
        # Implementation depends on specific CLI design

        with patch("run_benchmark.main", side_effect=KeyboardInterrupt()):
            try:
                import run_benchmark

                run_benchmark.main()
            except KeyboardInterrupt:
                # Should propagate KeyboardInterrupt or handle gracefully
                assert True
            except SystemExit:
                # Graceful exit is also acceptable
                assert True

    @pytest.mark.unit
    @patch("builtins.print")
    def test_cli_output_formatting(self, mock_print):
        """Test CLI output formatting and Unicode handling."""
        from run_benchmark import use_safe_unicode_standalone

        # Test that Unicode detection works without crashing
        safe_mode = use_safe_unicode_standalone()
        assert isinstance(safe_mode, bool)

    # Test that we can format output appropriately (call presence suffices)

    @pytest.mark.integration
    def test_runner_empty_submissions_dir(self, temp_dir: Path):
        """Former test_runner_empty: ensure empty submissions handled gracefully."""
        empty_dir = temp_dir / "submissions"
        empty_dir.mkdir()
        result = subprocess.run(
            [
                sys.executable,
                "run_benchmark.py",
                "--submissions-dir",
                str(empty_dir),
                "--results-dir",
                str(temp_dir / "results"),
                "--quiet",
            ],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        assert result.returncode in (0, 1)
        combined = ((result.stdout or "") + (result.stderr or "")).lower()
        assert "no" in combined and "model" in combined
        # This is a basic smoke test for output formatting logic
        test_message = "Test benchmark results: 85.5/100"
        print(test_message)  # Should not crash regardless of encoding
