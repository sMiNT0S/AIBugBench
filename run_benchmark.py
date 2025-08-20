#!/usr/bin/env python3
"""
RealityCheckBench - AI Code Evaluation Tool
Main entry point for running comprehensive AI code evaluation tests.

Usage: python run_benchmark.py [options]
"""

# Ensure UTF-8 encoding for cross-platform compatibility
import os
if os.name == 'nt':  # Windows
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from benchmark.utils import (
    load_test_data,
    ensure_directories,
    validate_submission_structure,
    generate_comparison_chart
)
from benchmark.scoring import BenchmarkScorer
from benchmark.validators import PromptValidators
import sys
import json
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the benchmark package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "benchmark"))


def use_safe_unicode_standalone() -> bool:
    """Standalone Unicode safety detection for use outside of class."""
    try:
        # Check if output is being piped or redirected
        if not sys.stdout.isatty():
            return True  # Use safe fallback for piped output
        
        # Test if current encoding supports emojis
        encoding = sys.stdout.encoding or 'utf-8'
        if encoding.lower() in ['cp1252', 'ascii']:
            return True  # Use safe fallback for limited encodings
            
        "🚀".encode(encoding)
        return False  # Unicode is safe
    except (UnicodeEncodeError, LookupError, AttributeError):
        return True   # Use safe fallback


class AICodeBenchmark:
    """Main benchmark runner class."""

    # Configuration constants
    DEFAULT_MAX_SCORE = 25
    DEFAULT_PASS_THRESHOLD = 0.6  # 60%
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        submissions_dir: str = "submissions",
        results_dir: str = "results"
    ):
        self.submissions_dir = Path(submissions_dir)
        self.results_dir = Path(results_dir)
        self.test_data_dir = Path("test_data")

        # Initialize components
        self.validators = PromptValidators(self.test_data_dir)
        self.scorer = BenchmarkScorer()

        # Ensure directories exist
        ensure_directories([self.submissions_dir, self.results_dir])

        # Load test data
        self.test_data = load_test_data(self.test_data_dir)

    def use_safe_unicode(self) -> bool:
        """Detect if Unicode emojis are safe to use."""
        try:
            import sys
            # Check if output is being piped or redirected
            if not sys.stdout.isatty():
                return True  # Use safe fallback for piped output
            
            # Test if current encoding supports emojis
            encoding = sys.stdout.encoding or 'utf-8'
            if encoding.lower() in ['cp1252', 'ascii']:
                return True  # Use safe fallback for limited encodings
                
            "🚀".encode(encoding)
            return False  # Unicode is safe
        except (UnicodeEncodeError, LookupError, AttributeError):
            return True   # Use safe fallback

    def safe_print(self, message: str) -> None:
        """Print message with Unicode safety and error handling."""
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: strip non-ASCII characters and try again
            try:
                ascii_message = message.encode('ascii', 'ignore').decode('ascii')
                print(ascii_message)
            except Exception:
                # Last resort: print a basic message
                print("(Output encoding error - message suppressed)")
        except Exception as e:
            # Any other printing error
            try:
                print(f"Print error: {str(e)}")
            except Exception:
                pass  # Even error reporting failed

    def format_detailed_score(self, detailed_scoring: Dict[str, Any]) -> str:
        """Format detailed scoring for terminal display."""
        lines = []
        
        # Category breakdown
        if detailed_scoring:
            categories = []
            # Consistent category ordering
            category_order = ["syntax", "structure", "execution", "quality", "security", "performance", "maintainability"]
            
            for category in category_order:
                if category in detailed_scoring:
                    scores = detailed_scoring[category]
                    earned = scores.get("earned", 0)
                    max_pts = scores.get("max", 0)
                    categories.append(f"{category.title()}: {earned:.1f}/{max_pts:.1f}")
            
            # Split into two lines for readability
            mid = len(categories) // 2
            if categories:
                lines.append(f"     └─ {', '.join(categories[:mid])}")
                if len(categories) > mid:
                    lines.append(f"        {', '.join(categories[mid:])}")
        
        return '\n'.join(lines)

    def discover_models(self) -> List[str]:
        """Discover all model submissions in the submissions directory."""
        models = []
        if not self.submissions_dir.exists():
            safe_unicode = self.use_safe_unicode()
            error_icon = "ERROR:" if safe_unicode else "❌"
            self.safe_print(f"{error_icon} Submissions directory '{self.submissions_dir}' not found!")
            return models

        for item in self.submissions_dir.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and item.name != "template"
            ):
                models.append(item.name)

        return sorted(models)

    def run_single_model(self, model_name: str) -> Dict[str, Any]:
        """Run all benchmark tests for a single model."""
        print(f"\nTesting model: {model_name}")
        print("=" * 50)

        model_dir = self.submissions_dir / model_name
        if not model_dir.exists():
            return {"error": f"Model directory '{model_dir}' not found"}

        # Validate submission structure first
        structure_validation = validate_submission_structure(model_dir)
        missing_files = [
            file for file, exists in structure_validation.items() if not exists
        ]
        if missing_files:
            safe_unicode = self.use_safe_unicode()
            warning_icon = "WARNING:" if safe_unicode else "⚠️"
            self.safe_print(f"{warning_icon} Missing or empty files: {', '.join(missing_files)}")

        results = {
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
            safe_unicode = self.use_safe_unicode()
            test_icon = "" if safe_unicode else "📝 "
            self.safe_print(f"\n{test_icon}Testing {prompt_name}...")
            try:
                prompt_result = test_func(model_dir)
                results["prompts"][prompt_id] = prompt_result
                results["overall_score"] += prompt_result.get("score", 0)
                results["total_possible"] += prompt_result.get(
                    "max_score", self.DEFAULT_MAX_SCORE
                )

                safe_unicode = self.use_safe_unicode()
                passed = prompt_result.get("passed", False)
                if safe_unicode:
                    status = "PASSED" if passed else "FAILED"
                else:
                    status = ("✅ PASSED" if passed else "❌ FAILED")
                score = prompt_result.get("score", 0)
                max_score = prompt_result.get(
                    "max_score", self.DEFAULT_MAX_SCORE
                )
                
                # Display enhanced scoring details if available
                if prompt_result.get("detailed_scoring"):
                    detailed_display = self.format_detailed_score(prompt_result["detailed_scoring"])
                    self.safe_print(f"   {status} - Score: {score:.2f}/{max_score}")
                    self.safe_print(detailed_display)
                else:
                    self.safe_print(f"   {status} - Score: {score:.2f}/{max_score}")

            except Exception as e:
                safe_unicode = self.use_safe_unicode()
                error_icon = "ERROR:" if safe_unicode else "❌ ERROR:"
                self.safe_print(f"   {error_icon} {str(e)}")
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

        safe_unicode = self.use_safe_unicode()
        final_icon = "" if safe_unicode else "🎯 "
        
        self.safe_print(
            f"\n{final_icon}Final Score: {results['overall_score']:.2f}/"
            f"{results['total_possible']} ({results['percentage']}%)"
        )

        return results

    def _test_prompt_1(self, model_dir: Path) -> Dict[str, Any]:
        """Test Prompt 1: Code Refactoring & Analysis."""
        solution_file = model_dir / "prompt_1_solution.py"
        return self.validators.validate_prompt_1_refactoring(solution_file)

    def _test_prompt_2(self, model_dir: Path) -> Dict[str, Any]:
        """Test Prompt 2: YAML/JSON Correction."""
        yaml_file = model_dir / "prompt_2_config_fixed.yaml"
        json_file = model_dir / "prompt_2_config.json"
        return self.validators.validate_prompt_2_yaml_json(
            yaml_file, json_file
        )

    def _test_prompt_3(self, model_dir: Path) -> Dict[str, Any]:
        """Test Prompt 3: Data Transformation."""
        transform_file = model_dir / "prompt_3_transform.py"
        return self.validators.validate_prompt_3_transformation(transform_file)

    def _test_prompt_4(self, model_dir: Path) -> Dict[str, Any]:
        """Test Prompt 4: API Simulation."""
        api_file = model_dir / "prompt_4_api_sync.py"
        return self.validators.validate_prompt_4_api(api_file)

    def run_all_models(self) -> Dict[str, Any]:
        """Run benchmark tests for all discovered models."""
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

        all_results = {
            "benchmark_run": {
                "timestamp": datetime.now().isoformat(),
                "total_models": len(models),
            },
            "models": {},
            "comparison": {},
        }

        # Test each model
        for model_name in models:
            all_results["models"][model_name] = self.run_single_model(
                model_name)

        # Generate comparison data
        all_results["comparison"] = self._generate_comparison(
            all_results["models"])

        # Save results
        self._save_results(all_results)

        return all_results

    def _generate_comparison(
        self, models_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comparison statistics across all models."""
        if not models_results:
            return {}

        comparison = {"ranking": [],
                      "prompt_performance": {}, "summary_stats": {}}

        # Create ranking
        model_scores = []
        for model_name, result in models_results.items():
            if "error" not in result:
                model_scores.append(
                    {
                        "model": model_name,
                        "score": result.get("overall_score", 0),
                        "percentage": result.get("percentage", 0),
                    }
                )

        comparison["ranking"] = sorted(
            model_scores, key=lambda x: x["score"], reverse=True
        )

        # Analyze prompt-specific performance
        for prompt_id in ["prompt_1", "prompt_2", "prompt_3", "prompt_4"]:
            prompt_scores = []
            for model_name, result in models_results.items():
                if ("error" not in result and
                        prompt_id in result.get("prompts", {})):
                    prompt_result = result["prompts"][prompt_id]
                    if "score" in prompt_result:
                        prompt_scores.append(
                            {
                                "model": model_name,
                                "score": prompt_result["score"],
                                "passed": prompt_result.get("passed", False),
                            }
                        )

            if prompt_scores:
                comparison["prompt_performance"][prompt_id] = {
                    "best_score": max(s["score"] for s in prompt_scores),
                    "avg_score": round(
                        sum(s["score"]
                            for s in prompt_scores) / len(prompt_scores), 1
                    ),
                    "pass_rate": round(
                        sum(1 for s in prompt_scores if s["passed"])
                        / len(prompt_scores)
                        * 100,
                        1,
                    ),
                    "ranking": sorted(
                        prompt_scores, key=lambda x: x["score"], reverse=True
                    ),
                }

        return comparison

    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save results to files with robust error handling."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main results with error handling
        results_file = self.results_dir / "latest_results.json"
        timestamped_file = self.results_dir / f"results_{timestamp}.json"

        saved_files = []
        for file_path in [results_file, timestamped_file]:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                saved_files.append(file_path)
            except Exception as e:
                # Critical: Try fallback ASCII encoding if UTF-8 fails
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=2, ensure_ascii=True)
                    saved_files.append(file_path)
                    self.safe_print(f"Warning: Saved {file_path} with ASCII encoding due to: {e}")
                except Exception as e2:
                    self.safe_print(f"CRITICAL: Failed to save {file_path}: {e2}")

        # Report saved files with safe Unicode handling
        safe_unicode = self.use_safe_unicode()
        save_icon = "" if safe_unicode else "💾 "
        
        if saved_files:
            self.safe_print(f"\n{save_icon}Results saved to:")
            for file_path in saved_files:
                self.safe_print(f"  - {file_path}")
        else:
            self.safe_print("\nERROR: Failed to save any results files!")

        # Generate summary report
        try:
            self._generate_summary_report(results, timestamp)
        except Exception as e:
            self.safe_print(f"Warning: Failed to generate summary report: {e}")
        
        # Generate comparison chart
        try:
            chart_file = self.results_dir / f"comparison_chart_{timestamp}.txt"
            generate_comparison_chart(results, chart_file)
            chart_icon = "" if safe_unicode else "📊 "
            self.safe_print(f"{chart_icon}Comparison chart: {chart_file}")
        except Exception as e:
            self.safe_print(f"Warning: Failed to generate comparison chart: {e}")

    def _generate_summary_report(
        self, results: Dict[str, Any], timestamp: str
    ) -> None:
        """Generate a human-readable summary report."""
        report_file = self.results_dir / f"summary_report_{timestamp}.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("AI CODE BENCHMARK RESULTS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Run Date: {results['benchmark_run']['timestamp']}\n")
            f.write(
                f"Models Tested: {results['benchmark_run']['total_models']}"
                f"\n\n"
            )

            # Overall ranking
            if "ranking" in results.get("comparison", {}):
                f.write("OVERALL RANKING\n")
                f.write("-" * 20 + "\n")
                for i, model in enumerate(results["comparison"]["ranking"], 1):
                    f.write(
                        f"{i}. {model['model']}: {model['score']} points "
                        f"({model['percentage']}%)\n"
                    )
                f.write("\n")

            # Detailed results for each model
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
                    status = (
                        "PASSED" if prompt_result.get(
                            "passed", False) else "FAILED"
                    )
                    score = prompt_result.get("score", 0)
                    max_score = prompt_result.get("max_score", 25)
                    f.write(
                        f"  {prompt_name}: {status} - {score}/{max_score}\n")

                    if "feedback" in prompt_result:
                        for feedback_line in prompt_result["feedback"]:
                            f.write(f"    • {feedback_line}\n")

        safe_unicode = self.use_safe_unicode()
        report_icon = "" if safe_unicode else "📄 "
        self.safe_print(f"{report_icon}Summary report: {report_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Code Benchmark Tool")
    parser.add_argument("--model", help="Test specific model only")
    parser.add_argument(
        "--submissions-dir",
        default="submissions",
        help="Directory containing model submissions",
    )
    parser.add_argument(
        "--results-dir", default="results", help="Directory to save results"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress detailed output"
    )

    args = parser.parse_args()

    # Create benchmark instance
    benchmark = AICodeBenchmark(args.submissions_dir, args.results_dir)

    try:
        if args.model:
            # Test single model
            benchmark.run_single_model(args.model)
            if not args.quiet:
                print(f"\nSingle model test completed: {args.model}")
                
                # Inform user about detailed results location
                safe_unicode = use_safe_unicode_standalone()
                results_icon = "" if safe_unicode else "📁 "
                print(f"\n{results_icon}Detailed results have been saved to:")
                print(f"  • {benchmark.results_dir}/latest_results.json - Complete benchmark data with detailed scoring")
                print(f"  • {benchmark.results_dir}/summary_report_*.txt - Human-readable summary with enhanced feedback")
                print(f"  • {benchmark.results_dir}/comparison_chart_*.txt - Visual comparison with progress bars")
                print("\nFor complete scoring breakdowns and analysis, check these files in the /results directory.")
        else:
            # Test all models
            results = benchmark.run_all_models()
            if not args.quiet and "models" in results:
                safe_unicode = use_safe_unicode_standalone()
                complete_icon = "" if safe_unicode else "🎉 "
                try:
                    print(f"\n{complete_icon}Benchmark completed! Tested {len(results['models'])} model(s)")
                except UnicodeEncodeError:
                    print(f"\nBenchmark completed! Tested {len(results['models'])} model(s)")

                # Show quick summary
                if "ranking" in results.get("comparison", {}):
                    trophy_icon = "" if safe_unicode else "🏆 "
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
                results_icon = "" if safe_unicode else "📁 "
                try:
                    print(f"\n{results_icon}Detailed results have been saved to:")
                except UnicodeEncodeError:
                    print("\nDetailed results have been saved to:")
                
                try:
                    print(f"  • {benchmark.results_dir}/latest_results.json - Complete benchmark data with detailed scoring")
                    print(f"  • {benchmark.results_dir}/summary_report_*.txt - Human-readable summary with enhanced feedback") 
                    print(f"  • {benchmark.results_dir}/comparison_chart_*.txt - Visual comparison with progress bars")
                    print("\nFor complete scoring breakdowns and analysis, check these files in the /results directory.")
                except UnicodeEncodeError:
                    print(f"  • {benchmark.results_dir}/latest_results.json - Complete benchmark data with detailed scoring")
                    print(f"  • {benchmark.results_dir}/summary_report_*.txt - Human-readable summary with enhanced feedback")
                    print(f"  • {benchmark.results_dir}/comparison_chart_*.txt - Visual comparison with progress bars")
                    print("\nFor complete scoring breakdowns and analysis, check these files in the /results directory.")

    except KeyboardInterrupt:
        safe_unicode = use_safe_unicode_standalone()
        interrupt_icon = "" if safe_unicode else "⏹️  "
        try:
            print(f"\n\n{interrupt_icon}Benchmark interrupted by user")
        except UnicodeEncodeError:
            print("\n\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        safe_unicode = use_safe_unicode_standalone()
        error_icon = "" if safe_unicode else "❌ "
        try:
            print(f"\n{error_icon}Benchmark failed: {str(e)}")
        except UnicodeEncodeError:
            print(f"\nBenchmark failed: {str(e)}")
        if not args.quiet:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
