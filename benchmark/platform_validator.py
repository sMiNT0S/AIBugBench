#!/usr/bin/env python3
"""
Platform Validation Script for AIBugBench
Ensures benchmark scoring consistency across Windows/macOS/Linux platforms.
"""

# Ensure UTF-8 encoding for cross-platform compatibility
import os

if os.name == "nt":  # Windows
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from datetime import datetime
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

# subprocess rationale: controlled internal invocations (fixed arg lists, shell=False);
# no user-supplied strings interpolated, so injection risk is minimal (Bandit B404/B603 noted).

# Platform detection
CURRENT_PLATFORM = platform.system().lower()
PLATFORM_MAPPING = {
    "windows": "windows-latest",
    "darwin": "macos-latest",
    "linux": "ubuntu-latest"
}


def safe_print(message: str) -> None:
    """Print message with Unicode safety for Windows cmd/PowerShell."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)


class PlatformBenchmarkValidator:
    """Validates benchmark consistency across platforms."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results_dir = project_root / "ci_results"
        self.results_dir.mkdir(exist_ok=True)

    def run_single_benchmark(self, model_name: str) -> dict[str, Any]:
        """Run benchmark for a single model and capture results."""
        safe_print(f"Running benchmark for model: {model_name}")

        # Record start time for performance monitoring
        start_time = time.time()

        # Ensure results directory exists
        (self.project_root / "results").mkdir(exist_ok=True)

        # Run benchmark command
        cmd = [sys.executable, "run_benchmark.py", "--model", model_name]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,  # 5-minute timeout
                check=True
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Load results from JSON file - check multiple possible locations
            results_file = self.project_root / "results" / "latest_results.json"

            if not results_file.exists():
                # Try the timestamped format
                results_dir = self.project_root / "results"
                timestamped_files = list(results_dir.glob("results_*.json"))
                if timestamped_files:
                    # Use the most recent one
                    results_file = max(timestamped_files, key=lambda x: x.stat().st_mtime)
                else:
                    raise FileNotFoundError(f"No results file found in {results_dir}")

            with open(results_file, encoding='utf-8') as f:
                benchmark_data = json.load(f)

            # Enhance with platform and timing data
            platform_results = {
                "platform": CURRENT_PLATFORM,
                "platform_ci": PLATFORM_MAPPING.get(CURRENT_PLATFORM, "unknown"),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "model_name": model_name,
                "results": benchmark_data,  # This is the loaded JSON data
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            return platform_results

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Benchmark timeout after 5 minutes for model: {model_name}") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Benchmark failed for model {model_name}:\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}"
            ) from e

    def extract_scores(self, results: dict[str, Any]) -> dict[str, float]:
        """Extract normalized scores from benchmark results."""
        scores = {}

        # Navigate the structure: results["results"] contains the loaded JSON
        if "results" not in results:
            return scores

        benchmark_data = results["results"]

        # JSON structure: models -> model_name -> prompts -> prompt_name
        if isinstance(benchmark_data, dict) and "models" in benchmark_data:
            for _model_name, model_data in benchmark_data["models"].items():
                if "prompts" in model_data:
                    for prompt_key, prompt_data in model_data["prompts"].items():
                        if isinstance(prompt_data, dict) and "score" in prompt_data:
                            # Round to 2 decimal places for comparison
                            scores[prompt_key] = round(float(prompt_data["score"]), 2)

        return scores

    def compare_results(self, results_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Compare benchmark results across platforms."""
        if len(results_list) < 2:
            return {"status": "insufficient_data", "message": "Need at least 2 platform results"}

        comparison = {
            "status": "consistent",
            "platforms": [r["platform"] for r in results_list],
            "model_name": results_list[0]["model_name"],
            "score_comparison": {},
            "performance_stats": {},
            "inconsistencies": []
        }

        # Extract scores from all platforms
        platform_scores = {}
        execution_times = {}

        for result in results_list:
            platform = result["platform"]
            platform_scores[platform] = self.extract_scores(result)
            execution_times[platform] = result["execution_time"]

        # Compare scores across platforms
        all_prompts = set()
        for scores in platform_scores.values():
            all_prompts.update(scores.keys())

        for prompt in all_prompts:
            prompt_scores = {}
            for platform, scores in platform_scores.items():
                if prompt in scores:
                    prompt_scores[platform] = scores[prompt]

            comparison["score_comparison"][prompt] = prompt_scores

            # Check for score inconsistencies (zero tolerance)
            if len(set(prompt_scores.values())) > 1:
                comparison["status"] = "inconsistent"
                comparison["inconsistencies"].append({
                    "prompt": prompt,
                    "scores": prompt_scores,
                    "difference": max(prompt_scores.values()) - min(prompt_scores.values())
                })

        # Performance analysis
        comparison["performance_stats"] = {
            "execution_times": execution_times,
            "avg_time": sum(execution_times.values()) / len(execution_times),
            "time_variance": max(execution_times.values()) - min(execution_times.values())
        }

        # Check for performance regressions (>20% difference)
        avg_time = comparison["performance_stats"]["avg_time"]
        for platform, time_val in execution_times.items():
            deviation = abs(time_val - avg_time) / avg_time
            if deviation > 0.20:  # 20% threshold
                comparison["inconsistencies"].append({
                    "type": "performance",
                    "platform": platform,
                    "deviation_percent": round(deviation * 100, 1),
                    "execution_time": time_val,
                    "average_time": avg_time
                })

        return comparison

    def save_results(self, results: dict[str, Any], filename: str) -> Path:
        """Save results to file."""
        output_path = self.results_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return output_path

    def validate_example_model(self) -> dict[str, Any]:
        """Run validation on example_model (baseline)."""
        expected_score = 92.17  # Move this to the beginning
        safe_print("Starting platform validation for example_model")

        try:
            results = self.run_single_benchmark("example_model")
            scores = self.extract_scores(results)

            # Validate against expected baseline (92.17/100)
            total_score = sum(scores.values())
            tolerance = 0.5  # Allow 0.5 point tolerance

            validation_result = {
                "platform": CURRENT_PLATFORM,
                "total_score": total_score,
                "expected_score": expected_score,
                "within_tolerance": abs(total_score - expected_score) <= tolerance,
                "individual_scores": scores,
                "full_results": results
            }

            if validation_result["within_tolerance"]:
                safe_print(
                    f"Platform validation PASSED: {total_score:.2f}/100 "
                    f"(expected ~{expected_score})"
                )
            else:
                safe_print(
                    f"Platform validation FAILED: {total_score:.2f}/100 "
                    f"(expected ~{expected_score})"
                )
                validation_result["status"] = "failed"

            return validation_result

        except Exception as e:
            safe_print(f"Platform validation ERROR: {e!s}")
            return {
                "platform": CURRENT_PLATFORM,
                "status": "error",
                "error_message": str(e),
                "total_score": 0.0,
                "expected_score": expected_score,
                "within_tolerance": False
            }


def main():
    """Main entry point for platform validation."""
    project_root = Path(__file__).parent.parent
    validator = PlatformBenchmarkValidator(project_root)

    safe_print(f"Platform Validation Tool - Running on {CURRENT_PLATFORM}")
    safe_print(f"Project root: {project_root}")

    # Run validation
    results = validator.validate_example_model()

    # Save results with platform-specific filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"platform_validation_{CURRENT_PLATFORM}_{timestamp}.json"
    output_path = validator.save_results(results, filename)

    safe_print(f"Results saved to: {output_path}")

    # Exit with appropriate code
    if results.get("status") == "error" or not results.get("within_tolerance", False):
        safe_print("Platform validation failed")
        sys.exit(1)
    else:
        safe_print("Platform validation successful")
        sys.exit(0)


if __name__ == "__main__":
    main()
