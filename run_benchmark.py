#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""
AIBugBench - AI Code Evaluation Tool
Main entry point for running comprehensive AI code evaluation tests.

Usage: python run_benchmark.py [options]
"""

# Ensure UTF-8 encoding for cross-platform compatibility
import argparse  # noqa: I001
import concurrent.futures
import contextlib
from datetime import UTC, datetime
import hashlib
import json
import os
import platform
import subprocess  # Bandit B404/B603: git hash & internal runs (shell=False)
import sys
import traceback
from pathlib import Path
from shutil import which
from typing import Any, TypedDict, cast

from benchmark.scoring import BenchmarkScorer
from benchmark.types import ModelResults, PromptResult
from benchmark.utils import (
    ensure_directories,
    generate_comparison_chart,
    load_test_data,
    validate_submission_structure,
)
from benchmark.validators import PromptValidators
from aibugbench.validation.factory import make_validator
from aibugbench.validation.utils import create_prompt2_categories

# Default directory constant (Phase 1 restructure)
DEFAULT_SUBMISSIONS_DIR = Path(__file__).parent / "submissions" / "user_submissions"


class ModelRank(TypedDict):
    model: str
    score: float
    percentage: float


class PromptScore(TypedDict):
    model: str
    score: float
    passed: bool


def use_safe_unicode_standalone() -> bool:
    """Standalone Unicode safety detection for use outside of class."""
    try:
        # Check if output is being piped or redirected
        if not sys.stdout.isatty():
            return True  # Use safe fallback for piped output

        # Test if current encoding supports emojis
        encoding = sys.stdout.encoding or "utf-8"
        if encoding.lower() in ["cp1252", "ascii"]:
            return True  # Use safe fallback for limited encodings

        "🚀".encode(encoding)
        return False  # Unicode is safe
    except (UnicodeEncodeError, LookupError, AttributeError):
        return True  # Use safe fallback


def _resolve_git_commit() -> str:
    """Best-effort short git commit hash for metadata embedding."""
    try:
        git_exe = which("git")
        if not git_exe:
            return "unknown"
        result = subprocess.run(  # noqa: S603  # Git version check - safe command
            [git_exe, "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        commit = result.stdout.strip()
        return commit or "unknown"
    except Exception:
        return "unknown"


class AICodeBenchmark:
    """Main benchmark runner class."""

    # Configuration constants
    DEFAULT_MAX_SCORE = 25
    DEFAULT_PASS_THRESHOLD = 0.6  # 60%
    DEFAULT_TIMEOUT = 30  # seconds
    SPEC_VERSION = "0.8.0"  # Benchmark spec version (update when scoring rules change)

    def __init__(
        self,
        submissions_dir: str = str(DEFAULT_SUBMISSIONS_DIR),
        results_dir: str = "results",
        disable_metadata: bool | None = None,
    ):
        self.submissions_dir = Path(submissions_dir)
        # Results directory override precedence (environment first, then arg)
        # Allows tooling (e.g., pre-commit smoke tests) to redirect all artifact writes
        # away from the working tree. Chosen variable cascade:
        # 1. AIB_RESULTS_DIR (explicit path)
        # 2. AIB_ARTIFACT_DIR or AIBUGBENCH_ARTIFACT_DIR root + '/results'
        # 3. CLI / function argument (results_dir)
        env_results = os.getenv("AIB_RESULTS_DIR")
        env_artifact_root = os.getenv("AIB_ARTIFACT_DIR") or os.getenv("AIBUGBENCH_ARTIFACT_DIR")
        if env_results and env_results.strip():
            chosen_results = Path(env_results.strip())
        elif env_artifact_root and env_artifact_root.strip():
            chosen_results = Path(env_artifact_root.strip()) / "results"
        else:
            chosen_results = Path(results_dir)
        self.results_dir = chosen_results
        self.test_data_dir = Path("test_data")
        # Cache run start timestamp (per-run directory)
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Cache unicode capability once
        self._unicode_safe = self._detect_unicode_safety()
        # Determine metadata collection preference (env var overrides default if set)
        env_disable = os.getenv("AIBUGBENCH_DISABLE_METADATA")
        if disable_metadata is None:
            self.disable_metadata = bool(env_disable and env_disable != "0")
        else:
            # Explicit flag passed; still allow env var to force disable if truthy
            self.disable_metadata = disable_metadata or bool(env_disable and env_disable != "0")

        # Initialize components
        self.validators = PromptValidators(self.test_data_dir)
        self.prompt2_validator = make_validator("p2", env=os.environ)
        self.scorer = BenchmarkScorer()

        # Ensure directories exist
        ensure_directories([self.submissions_dir, self.results_dir])

        # Load test data
        self.test_data = load_test_data(self.test_data_dir)

        # Pre-compute dependency fingerprint once (best effort; avoid repeated I/O & hashing)
        self.dependency_fingerprint: str | None = None
        try:
            req_path = Path("requirements.txt")
            if req_path.exists():
                self.dependency_fingerprint = hashlib.sha256(req_path.read_bytes()).hexdigest()[:16]
        except Exception:  # pragma: no cover - non-critical
            self.dependency_fingerprint = None

    def _detect_unicode_safety(self) -> bool:
        try:
            if not sys.stdout.isatty():
                return True
            encoding = sys.stdout.encoding or "utf-8"
            if encoding.lower() in ["cp1252", "ascii"]:
                return True
            "🚀".encode(encoding)
            return False
        except (UnicodeEncodeError, LookupError, AttributeError):  # pragma: no cover
            return True

    def use_safe_unicode(self) -> bool:
        return self._unicode_safe

    def safe_print(self, message: str) -> None:
        """Print message with Unicode safety and error handling."""
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: strip non-ASCII characters and try again
            try:
                ascii_message = message.encode("ascii", "ignore").decode("ascii")
                print(ascii_message)
            except Exception:
                with contextlib.suppress(Exception):
                    print("(Output encoding error - message suppressed)")
        except Exception as e:  # pragma: no cover - very uncommon
            with contextlib.suppress(Exception):
                print(f"Print error: {e!s}")

    def format_detailed_score(self, detailed_scoring: dict[str, Any]) -> str:
        """Format detailed scoring for terminal display."""
        lines: list[str] = []
        if detailed_scoring:
            categories: list[str] = []
            category_order = [
                "syntax",
                "structure",
                "execution",
                "quality",
                "security",
                "performance",
                "maintainability",
            ]
            for category in category_order:
                if category in detailed_scoring:
                    scores = detailed_scoring[category]
                    earned = scores.get("earned", 0)
                    max_pts = scores.get("max", 0)
                    categories.append(f"{category.title()}: {earned:.1f}/{max_pts:.1f}")
            mid = len(categories) // 2
            if categories:
                lines.append(f"     └─ {', '.join(categories[:mid])}")
                if len(categories) > mid:
                    lines.append(f"        {', '.join(categories[mid:])}")
        return "\n".join(lines)

    # Prompt test helpers (return typed PromptResult directly)
    def _test_prompt_1(self, model_dir: Path) -> PromptResult:
        """Test Prompt 1: Code Refactoring & Analysis."""
        solution_file = model_dir / "prompt_1_solution.py"
        return self.validators.validate_prompt_1_refactoring(solution_file)

    def _test_prompt_2(self, model_dir: Path) -> PromptResult:
        """Test Prompt 2: YAML/JSON Correction."""
        validator = self.prompt2_validator
        analysis = validator.analyze(str(model_dir))
        score = validator.score(analysis)

        breakdown: dict[str, float] = {}
        category_breakdown = getattr(validator, "category_breakdown", None)
        if callable(category_breakdown):
            breakdown = cast(dict[str, float], category_breakdown(analysis))

        tests_passed: dict[str, bool] = {}
        tests_passed_fn = getattr(validator, "tests_passed", None)
        if callable(tests_passed_fn):
            tests_passed = cast(dict[str, bool], tests_passed_fn(analysis))

        category_weights = getattr(validator, "category_weights", create_prompt2_categories())
        detailed_scoring = {
            category: {
                "earned": breakdown.get(category, 0.0),
                "max": category_weights.get(category, 0.0),
            }
            for category in category_weights
        }
        feedback: list[str] = []
        for category in category_weights:
            earned = breakdown.get(category, 0.0)
            max_cat = category_weights.get(category, 0.0)
            feedback.append(f"{category.title()}: {earned:.1f}/{max_cat:.1f}")
        if not feedback:
            feedback.append(f"Total: {score:.1f}/{sum(category_weights.values()):.1f}")
        max_score = int(sum(category_weights.values()))

        return PromptResult(
            passed=score >= 15.0,
            score=score,
            max_score=max_score,
            feedback=feedback,
            tests_passed=tests_passed,
            detailed_scoring=detailed_scoring,
        )

    def _test_prompt_3(self, model_dir: Path) -> PromptResult:
        """Test Prompt 3: Data Transformation."""
        transform_file = model_dir / "prompt_3_transform.py"
        return self.validators.validate_prompt_3_transformation(transform_file)

    def _test_prompt_4(self, model_dir: Path) -> PromptResult:
        """Test Prompt 4: API Simulation."""
        api_file = model_dir / "prompt_4_api_sync.py"
        return self.validators.validate_prompt_4_api(api_file)

    def discover_models(self) -> list[str]:
        """Discover model submissions across tiered structure with fallback.

            Tiers:
              - reference_implementations/* (fully linted + covered)
              - user_submissions/* (excluded by default, still runnable)
              - templates/template (not a model; skip)
        Legacy layout support has been removed prior to public release to simplify
        maintenance. A clear error is emitted if legacy directories are detected.
        """
        if not self.submissions_dir.exists():
            safe_unicode = self.use_safe_unicode()
            error_icon = "ERROR:" if safe_unicode else "❌"
            self.safe_print(
                f"{error_icon} Submissions directory '{self.submissions_dir}' not found!"
            )
            return []
        ref_dir = self.submissions_dir / "reference_implementations"
        user_dir = self.submissions_dir / "user_submissions"
        tmpl_dir = self.submissions_dir / "templates"

        reference_models: list[str] = []
        user_models: list[str] = []

        # New tiered layout
        if ref_dir.exists():
            for item in ref_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    reference_models.append(item.name)
        if user_dir.exists():
            for item in user_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    user_models.append(item.name)

        # Detect legacy structure presence and abort with guidance
        legacy_example = (self.submissions_dir / "example_model").exists()
        legacy_template = (self.submissions_dir / "template").exists()
        tiered_detected = ref_dir.exists() or tmpl_dir.exists() or user_dir.exists()
        if (legacy_example or legacy_template) and not tiered_detected:
            raise SystemExit(
                "Legacy submissions layout detected (e.g. submissions/example_model). "
                "Legacy support was removed before public release. Please migrate to:\n"
                "submissions/\n  reference_implementations/example_model/\n  "
                "templates/template/\n  user_submissions/\n"
            )

        # Emit discovery summary
        summary = (
            f"Discovered models: reference={len(reference_models)} user={len(user_models)} "
            f"templates={'OK' if (tmpl_dir / 'template').exists() else 'MISSING'}"
        )
        self.safe_print(summary)
        return sorted(reference_models + user_models)

    def _resolve_model_path(self, model_name: str) -> Path | None:
        """Resolve model path within tiered structure."""
        ref_path = self.submissions_dir / "reference_implementations" / model_name
        if ref_path.exists():
            return ref_path
        user_path = self.submissions_dir / "user_submissions" / model_name
        if user_path.exists():
            return user_path
        return None

    def run_single_model(self, model_name: str) -> ModelResults:
        """Run all benchmark tests for a single model."""
        safe_unicode = self.use_safe_unicode()
        print(f"\nTesting model: {model_name}")
        print("=" * 50)

        model_dir = self._resolve_model_path(model_name)
        if model_dir is None:
            return {
                "error": (
                    f"Model '{model_name}' not found in any tier "
                    "(reference_implementations/, user_submissions/, or legacy root)"
                )
            }

        # Validate submission structure first
        structure_validation = validate_submission_structure(model_dir)
        missing_files = [file for file, exists in structure_validation.items() if not exists]
        if missing_files:
            warning_icon = "WARNING:" if safe_unicode else "⚠️"
            self.safe_print(f"{warning_icon} Missing or empty files: {', '.join(missing_files)}")

        results: ModelResults = {
            "model_name": model_name,
            "timestamp": datetime.now().isoformat(),
            "prompts": {},
            "overall_score": 0,
            "total_possible": 0,
        }

        # Test each prompt
        prompt_tests = [
            ("prompt_1", "Refactoring & Analysis", self._test_prompt_1),
            ("prompt_2", "YAML/JSON Correction", self._test_prompt_2),
            ("prompt_3", "Data Transformation", self._test_prompt_3),
            ("prompt_4", "API Simulation", self._test_prompt_4),
        ]

        for prompt_id, prompt_name, test_func in prompt_tests:
            test_icon = "" if safe_unicode else "📝 "
            self.safe_print(f"\n{test_icon}Testing {prompt_name}...")
            try:
                prompt_result = test_func(model_dir)
                results["prompts"][prompt_id] = prompt_result
                results["overall_score"] += prompt_result.get("score", 0)
                results["total_possible"] += prompt_result.get("max_score", self.DEFAULT_MAX_SCORE)

                passed = prompt_result.get("passed", False)
                if safe_unicode:
                    status = "PASSED" if passed else "FAILED"
                else:
                    status = "✅ PASSED" if passed else "❌ FAILED"
                score = prompt_result.get("score", 0)
                max_score = prompt_result.get("max_score", self.DEFAULT_MAX_SCORE)

                # Display enhanced scoring details if available
                if prompt_result.get("detailed_scoring"):
                    detailed_display = self.format_detailed_score(
                        prompt_result.get("detailed_scoring", {})
                    )
                    self.safe_print(f"   {status} - Score: {score:.2f}/{max_score}")
                    self.safe_print(detailed_display)
                else:
                    self.safe_print(f"   {status} - Score: {score:.2f}/{max_score}")

            except Exception as e:
                error_icon = "ERROR:" if safe_unicode else "❌ ERROR:"
                self.safe_print(f"   {error_icon} {e!s}")
                results["prompts"][prompt_id] = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "passed": False,
                    "score": 0,
                    "max_score": self.DEFAULT_MAX_SCORE,
                }
                results["total_possible"] += self.DEFAULT_MAX_SCORE

        # Calculate final percentage
        if results["total_possible"] > 0:
            results["percentage"] = round(
                (results["overall_score"] / results["total_possible"]) * 100, 1
            )
        else:
            results["percentage"] = 0

        final_icon = "" if safe_unicode else "🎯 "

        self.safe_print(
            f"\n{final_icon}Final Score: {results['overall_score']:.2f}/"
            f"{results['total_possible']} ({results['percentage']}%)"
        )

        return results

    def run_all_models(self, workers: int = 1) -> dict[str, Any]:
        """Run benchmark tests for all discovered models.

        Parameters
        ----------
        workers : int
            Number of concurrent workers (1 => sequential).
        """
        models = self.discover_models()

        if not models:
            safe_unicode = self.use_safe_unicode()
            error_icon = "ERROR:" if safe_unicode else "❌"
            self.safe_print(f"{error_icon} No models found in submissions directory!")
            self.safe_print(f"Please add model submissions to: {self.submissions_dir}")
            return {"error": "No models found"}
        safe_unicode = self.use_safe_unicode()
        discovery_icon = "" if safe_unicode else "🔍 "
        self.safe_print(f"{discovery_icon}Discovered {len(models)} model(s): {', '.join(models)}")

        all_results: dict[str, Any] = {
            "benchmark_run": {
                "timestamp": datetime.now().isoformat(),
                "total_models": len(models),
            },
            "models": {},
            "comparison": {},
        }

        # Test each model (optionally concurrently)
        if workers and workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {executor.submit(self.run_single_model, m): m for m in models}
                for future in concurrent.futures.as_completed(future_map):
                    model_name = future_map[future]
                    try:
                        all_results["models"][model_name] = future.result()
                    except Exception as exc:  # pragma: no cover - defensive
                        all_results["models"][model_name] = {"error": str(exc)}
        else:
            for model_name in models:
                all_results["models"][model_name] = self.run_single_model(model_name)

        # Generate comparison data
        all_results["comparison"] = self._generate_comparison(all_results["models"])

        # Save results
        self._save_results(all_results)

        return all_results

    def _generate_comparison(self, models_results: dict[str, Any]) -> dict[str, Any]:
        """Generate comparison statistics across all models."""
        if not models_results:
            return {}

        comparison: dict[str, Any] = {
            "ranking": [],
            "prompt_performance": {},
            "summary_stats": {},
        }

        # Create ranking
        model_scores: list[ModelRank] = []
        for model_name, result_any in models_results.items():
            result = cast(ModelResults, result_any)
            if "error" in result:
                continue
            score = float(result.get("overall_score", 0) or 0.0)
            percentage = float(result.get("percentage", 0) or 0.0)
            model_scores.append({"model": model_name, "score": score, "percentage": percentage})

        comparison["ranking"] = sorted(
            model_scores, key=lambda x: cast(float, x["score"]), reverse=True
        )

        # Dynamically derive prompt IDs from available data instead of hard-coded list
        prompt_ids: set[str] = set()
        for model_result_any in models_results.values():
            model_result = cast(ModelResults, model_result_any)
            prompts = model_result.get("prompts", {}) or {}
            prompt_ids.update(prompts.keys())

        for prompt_id in sorted(prompt_ids):
            prompt_scores: list[PromptScore] = []
            for model_name, result_any in models_results.items():
                result = cast(ModelResults, result_any)
                prompts = result.get("prompts", {}) or {}
                if "error" in result or prompt_id not in prompts:
                    continue
                pr = cast(PromptResult, prompts[prompt_id])
                score = float(pr.get("score", 0) or 0.0)
                passed = bool(pr.get("passed", False))
                prompt_scores.append({"model": model_name, "score": score, "passed": passed})

            if prompt_scores:
                comparison["prompt_performance"][prompt_id] = {
                    "best_score": max(s["score"] for s in prompt_scores),
                    "avg_score": round(
                        sum(s["score"] for s in prompt_scores) / len(prompt_scores), 1
                    ),
                    "pass_rate": round(
                        (sum(1 for s in prompt_scores if s["passed"]) / len(prompt_scores)) * 100, 1
                    ),
                    "ranking": sorted(
                        prompt_scores, key=lambda x: cast(float, x["score"]), reverse=True
                    ),
                }

        return comparison

    def _save_results(self, results: dict[str, Any]) -> None:
        """Save results atomically into a per-run directory with metadata injection."""
        timestamp = self.run_timestamp

        # Inject metadata honoring opt-out
        meta = results.setdefault("_metadata", {})
        if self.disable_metadata:
            meta.clear()
            meta["spec_version"] = self.SPEC_VERSION
        else:
            meta.clear()
            meta["spec_version"] = self.SPEC_VERSION
            meta["git_commit"] = os.environ.get("GITHUB_SHA") or _resolve_git_commit()
            meta["python_version"] = platform.python_version()
            meta["platform"] = platform.platform()
            meta["timestamp_utc"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            if self.dependency_fingerprint:
                meta["dependency_fingerprint"] = self.dependency_fingerprint

        # Per-run directory structure
        run_dir = self.results_dir / timestamp
        detailed_dir = run_dir / "detailed"
        charts_dir = run_dir / "comparison_charts"
        ensure_directories([run_dir, detailed_dir, charts_dir])

        run_results_file = run_dir / "latest_results.json"
        detailed_results_file = detailed_dir / "detailed_results.json"
        root_latest = self.results_dir / "latest_results.json"  # backwards compatible pointer

        for target in [run_results_file, detailed_results_file, root_latest]:
            self._atomic_write_json(target, results)

        # Generate summary & chart
        try:
            self._generate_summary_report(results, timestamp, detailed_dir)
        except Exception as e:  # pragma: no cover
            self.safe_print(f"Warning: Failed to generate summary report: {e}")
        try:
            chart_file = charts_dir / "comparison_chart.txt"
            generate_comparison_chart(results, chart_file)
            chart_icon = "" if self.use_safe_unicode() else "📊 "
            self.safe_print(f"{chart_icon}Comparison chart: {chart_file}")
        except Exception as e:  # pragma: no cover
            self.safe_print(f"Warning: Failed to generate comparison chart: {e}")

    def _atomic_write_json(self, path: Path, data: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=True)
                os.replace(tmp, path)
            except Exception as e2:  # pragma: no cover
                self.safe_print(f"CRITICAL: Failed to save {path}: {e2}")
                with contextlib.suppress(Exception):
                    if tmp.exists():
                        tmp.unlink()

    def _generate_summary_report(
        self, results: dict[str, Any], timestamp: str, output_dir: Path | None = None
    ) -> None:
        """Generate a human-readable summary report."""
        if output_dir is None:
            output_dir = self.results_dir
        report_file = output_dir / f"summary_report_{timestamp}.txt"

        tmp_file = report_file.with_suffix(report_file.suffix + ".tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write("AI CODE BENCHMARK RESULTS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Run Date: {results['benchmark_run']['timestamp']}\n")
                f.write(f"Models Tested: {results['benchmark_run']['total_models']}\n\n")

                if "ranking" in results.get("comparison", {}):
                    f.write("OVERALL RANKING\n")
                    f.write("-" * 20 + "\n")
                    for i, model in enumerate(results["comparison"]["ranking"], 1):
                        line = (
                            f"{i}. {model['model']}: {model['score']} points "
                            f"({model['percentage']}%)\n"
                        )
                        f.write(line)
                    f.write("\n")

                f.write("DETAILED RESULTS\n")
                f.write("-" * 20 + "\n")
                for model_name, model_result in results["models"].items():
                    f.write(f"\n{model_name}:\n")
                    if "error" in model_result:
                        f.write(f"  ERROR: {model_result['error']}\n")
                        continue
                    f.write(
                        f"  Overall Score: {model_result['overall_score']:.2f}/"
                        f"{model_result['total_possible']} "
                        f"({model_result['percentage']}%)\n"
                    )

                    prompts_data = model_result.get("prompts", {})
                    for prompt_id, prompt_result in prompts_data.items():
                        prompt_name = prompt_id.replace("_", " ").title()
                        status = "PASSED" if prompt_result.get("passed", False) else "FAILED"
                        score = prompt_result.get("score", 0)
                        max_score = prompt_result.get("max_score", 25)
                        f.write(f"  {prompt_name}: {status} - {score}/{max_score}\n")
                        if "feedback" in prompt_result:
                            for feedback_line in prompt_result["feedback"]:
                                f.write(f"    • {feedback_line}\n")
            os.replace(tmp_file, report_file)
        except Exception as e:  # pragma: no cover
            self.safe_print(f"Warning: Failed to write summary report atomically: {e}")
            with contextlib.suppress(Exception):
                if tmp_file.exists():
                    tmp_file.unlink()

        safe_unicode = self.use_safe_unicode()
        report_icon = "" if safe_unicode else "📄 "
        self.safe_print(f"{report_icon}Summary report: {report_file}")


# Removed alternate discover_models implementation (pre-release simplification)


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser.

    Separated to allow tests to import and verify CLI flags without executing main logic.
    """
    parser = argparse.ArgumentParser(description="AI Code Benchmark Tool")
    parser.add_argument("--model", help="Test specific model only")
    # Phase 3 security flags
    parser.add_argument(
        "--unsafe",
        action="store_true",
        help="DANGEROUS: Disable sandbox/resource isolation (gives submitted code normal access)",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow network access during execution (future enforcement; currently advisory)",
    )
    parser.add_argument(
        "--trusted-model",
        action="store_true",
        help="Skip unsafe mode confirmation prompt (CI / trusted submissions only)",
    )
    parser.add_argument(
        "--submissions-dir",
        default="submissions",
        help="Directory containing model submissions",
    )
    parser.add_argument("--results-dir", default="results", help="Directory to save results")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress detailed output")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable environment/git/dependency metadata collection (spec_version retained)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent workers for model evaluation (default: 1)",
    )
    parser.add_argument(
        "--mem",
        type=int,
        default=512,
        choices=[256, 384, 512, 768, 1024],
        help="Memory limit (MB) for sandboxed execution (default: 512)",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments (test hook)."""
    return build_arg_parser().parse_args(argv)


def _print_security_status(
    args: argparse.Namespace, unicode_safe: bool, trusted_display: str | None = None
) -> None:
    """Display security status banner each run (Phase 3)."""
    # Determine symbols based on environment
    sandbox_enabled = not args.unsafe
    network_allowed = args.allow_network
    # Display-oriented trusted indicator: allow override when known.
    # If not provided, infer a best-effort value from args for display only.
    if trusted_display is None:
        trusted_flag = args.trusted_model
        try:
            model_name = getattr(args, "model", None)
            submissions_root = (
                Path(args.submissions_dir)
                if getattr(args, "submissions_dir", None)
                else Path("submissions")
            )
            ref_dir = submissions_root / "reference_implementations"
            usr_dir = submissions_root / "user_submissions"
            if model_name:
                # Single model: YES if it's under reference_implementations
                trusted_flag = trusted_flag or (ref_dir / str(model_name)).exists()
                trusted_display = "YES" if trusted_flag else "NO"
            else:
                # All models: show MIXED if both categories exist, otherwise YES/NO accordingly
                has_ref = ref_dir.exists() and any(p.is_dir() for p in ref_dir.iterdir())
                has_usr = usr_dir.exists() and any(p.is_dir() for p in usr_dir.iterdir())
                if has_ref and has_usr:
                    trusted_display = "MIXED"
                elif has_ref:
                    trusted_display = "YES"
                elif has_usr:
                    trusted_display = "NO"
                else:
                    trusted_display = "NO"
        except Exception as exc:  # pragma: no cover - banner display robustness
            try:
                import logging as _log

                _log.getLogger(__name__).debug("Trusted-model display inference failed: %s", exc)
            except Exception:
                from contextlib import suppress as _suppress

                with _suppress(Exception):
                    import sys as _sys

                    _sys.stderr.write("[debug] trusted-model banner inference failed\n")
    lines = []
    lines.append("Sandboxing:     {}".format("ENABLED" if sandbox_enabled else "DISABLED"))
    lines.append("Network:        {}".format("ALLOWED" if network_allowed else "BLOCKED"))
    lines.append("Subprocess:     {}".format("BLOCKED" if sandbox_enabled else "ALLOWED"))
    lines.append("Filesystem:     {}".format("CONFINED" if sandbox_enabled else "FULL ACCESS"))
    lines.append("Env Clean:      {}".format("CLEANED" if sandbox_enabled else "FULL"))
    lines.append("ResourceLimits: {}".format("ENFORCED" if sandbox_enabled else "NONE"))
    lines.append(
        "Trusted Model:  {}".format(trusted_display or ("YES" if args.trusted_model else "NO"))
    )

    # Box drawing borders: if unicode is NOT safe, use ASCII borders
    if unicode_safe:
        top = "+" + "-" * 38 + "+"
        bottom = top
    else:
        top = "╔" + "═" * 38 + "╗"
        bottom = "╚" + "═" * 38 + "╝"

    print(top)
    title = "AIBugBench Security Status"
    print("|" + title.center(38) + "|") if unicode_safe else print("║" + title.center(38) + "║")
    mid_border = "+" + "-" * 38 + "+" if unicode_safe else "╠" + "═" * 38 + "╣"
    print(mid_border)
    for line in lines:
        print(("|" if unicode_safe else "║") + line.ljust(38) + ("|" if unicode_safe else "║"))
    print(bottom)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    args = parse_args(argv)
    global_unicode_safe = use_safe_unicode_standalone()

    # Always display security status (even in quiet mode)
    _print_security_status(args, global_unicode_safe)

    # Phase 5.5: Run security audit gating unless explicitly unsafe.
    # Testing accommodation: when running under pytest, default to non-strict mode
    # unless explicitly forced via AIBUGBENCH_AUDIT_STRICT=1. This keeps unit tests
    # focused on CLI behavior rather than full security posture.
    if not args.unsafe:
        in_pytest = bool(os.getenv("PYTEST_CURRENT_TEST"))
        audit_strict_env = os.getenv("AIBUGBENCH_AUDIT_STRICT", "1").lower()
        audit_strict = (audit_strict_env not in {"0", "false", "no"}) and not in_pytest
        audit_script = Path("scripts/security_audit.py")
        if audit_script.exists():
            try:
                # Run audit in a lightweight subprocess to avoid importing benchmark state.
                proc = subprocess.run(  # noqa: S603  # Security audit execution - controlled script
                    [sys.executable, str(audit_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
            except Exception as e:  # pragma: no cover - defensive
                print(f"Security audit invocation failed: {e}")
                # CRITICAL: Security audit invocation failure must halt execution
                print("Security audit could not be executed. Refusing to run benchmark for safety.")
                return 1
            if proc.returncode != 0:
                print(proc.stdout.rstrip())
                if audit_strict:
                    print(
                        "Security audit failed. Refusing to run benchmark. "
                        "Re-run with --unsafe to bypass (NOT RECOMMENDED)."
                    )
                    # CRITICAL: Security audit failure must halt execution immediately
                    return 1
                else:
                    print("[audit] Non-strict mode: continuing despite audit failure (test mode).")
        else:
            if audit_strict:
                print(
                    "Security audit script missing (scripts/security_audit.py). "
                    "Refusing to run benchmark for safety. "
                    "Re-run with --unsafe to bypass (NOT RECOMMENDED)."
                )
                # CRITICAL: Missing security audit script must halt execution
                return 1
            else:
                print("[audit] Non-strict mode: audit script missing; proceeding (test mode).")

    # Confirm unsafe mode unless trusted
    if args.unsafe and not args.trusted_model:
        try:
            resp = input("WARNING: UNSAFE mode disables sandbox & limits. Type 'yes' to continue: ")
        except EOFError:  # Non-interactive context defaults to abort for safety
            print("Aborted (non-interactive unsafe request)")
            return 1
        if resp.strip().lower() != "yes":
            print("Aborted.")
            return 1

    # Propagate environment flags BEFORE benchmark creation so any later components can read
    if args.unsafe:
        os.environ["AIBUGBENCH_UNSAFE"] = "true"
    else:
        # Ensure variable not set to force sandbox
        if os.environ.get("AIBUGBENCH_UNSAFE"):
            os.environ.pop("AIBUGBENCH_UNSAFE", None)
    if args.allow_network:
        os.environ["AIBUGBENCH_ALLOW_NETWORK"] = "true"

    # Create benchmark instance AFTER env is configured
    benchmark = AICodeBenchmark(
        args.submissions_dir,
        args.results_dir,
        disable_metadata=args.no_metadata,
    )
    # Propagate memory limit to validators (temporary attribute contract)
    benchmark.sandbox_memory_mb = args.mem  # type: ignore[attr-defined]

    try:
        if args.model:
            # Test single model
            single_result = benchmark.run_single_model(args.model)

            # Create results structure compatible with _save_results
            results_for_save: dict[str, Any] = {
                "benchmark_run": {
                    "timestamp": datetime.now().isoformat(),
                    "total_models": 1,
                    "prompts_tested": 4,
                },
                "models": {args.model: single_result},
            }

            # Generate comparison data for single model runs
            results_for_save["comparison"] = benchmark._generate_comparison(
                results_for_save["models"]
            )

            # Save results for single model runs
            benchmark._save_results(results_for_save)

            if not args.quiet:
                print(f"\nSingle model test completed: {args.model}")

                # Inform user about detailed results location
                results_icon = "" if global_unicode_safe else "📁 "
                print(f"\n{results_icon}Detailed results have been saved to:")
                print(
                    f"  • {benchmark.results_dir}/latest_results.json - Complete benchmark data "
                    f"with detailed scoring"
                )
                print(
                    f"  • {benchmark.results_dir}/detailed/summary_report_*.txt "
                    f"- Human-readable summary "
                    f"with enhanced feedback"
                )
                print(
                    f"  • {benchmark.results_dir}/comparison_charts/comparison_chart_*.txt "
                    f"- Visual comparison "
                    f"with progress bars"
                )
                print(
                    "\nFor complete scoring breakdowns and analysis, check these files "
                    "in the /results directory."
                )
        else:
            # Test all models
            results = benchmark.run_all_models(workers=max(1, args.workers))
            if not args.quiet and "models" in results:
                complete_icon = "" if global_unicode_safe else "🎉 "
                try:
                    print(
                        f"\n{complete_icon}Benchmark completed! "
                        f"Tested {len(results['models'])} model(s)"
                    )
                except UnicodeEncodeError:
                    print(f"\nBenchmark completed! Tested {len(results['models'])} model(s)")

                # Show quick summary
                if "ranking" in results.get("comparison", {}):
                    trophy_icon = "" if global_unicode_safe else "🏆 "
                    try:
                        print(f"\n{trophy_icon}Top Performers:")
                    except UnicodeEncodeError:
                        print("\nTop Performers:")
                    ranking = results["comparison"]["ranking"][:3]
                    for i, model in enumerate(ranking, 1):
                        try:
                            print(f"  {i}. {model['model']}: {model['percentage']}%")
                        except UnicodeEncodeError:
                            print(f"  {i}. {model['model']}: {model['percentage']}%")

                # Inform user about detailed results location for all models
                results_icon = "" if global_unicode_safe else "📁 "
                try:
                    print(f"\n{results_icon}Detailed results have been saved to:")
                except UnicodeEncodeError:
                    print("\nDetailed results have been saved to:")

                try:
                    print(
                        f"  • {benchmark.results_dir}/latest_results.json - Complete data "
                        f"with detailed scoring"
                    )
                    print(
                        f"  • {benchmark.results_dir}/detailed/summary_report_*.txt - Summary "
                        f"with enhanced feedback"
                    )
                    print(
                        f"  • {benchmark.results_dir}/comparison_charts/comparison_chart_*.txt "
                        f"- Visual comparison "
                        f"with progress bars"
                    )
                    print(
                        "\nFor complete scoring breakdowns and analysis, check these files "
                        "in the /results directory."
                    )
                except UnicodeEncodeError:
                    print(
                        f"  • {benchmark.results_dir}/latest_results.json - Complete data "
                        f"with detailed scoring"
                    )
                    print(
                        f"  • {benchmark.results_dir}/detailed/summary_report_*.txt - Summary "
                        f"with enhanced feedback"
                    )
                    print(
                        f"  • {benchmark.results_dir}/comparison_charts/comparison_chart_*.txt "
                        f"- Visual comparison "
                        f"with progress bars"
                    )
                    print(
                        "\nFor complete scoring breakdowns and analysis, check these files "
                        "in the /results directory."
                    )
        return 0

    except KeyboardInterrupt:
        interrupt_icon = "" if global_unicode_safe else "⏹️  "
        try:
            print(f"\n\n{interrupt_icon}Benchmark interrupted by user")
        except UnicodeEncodeError:
            print("\n\nBenchmark interrupted by user")
        return 1
    except Exception as e:
        error_icon = "" if global_unicode_safe else "❌ "
        try:
            print(f"\n{error_icon}Benchmark failed: {e!s}")
        except UnicodeEncodeError:
            print(f"\nBenchmark failed: {e!s}")
        if not args.quiet:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
