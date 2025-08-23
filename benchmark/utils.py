"""
Utility functions for AI Code Benchmark
"""

import json
from pathlib import Path
from typing import Any


def load_test_data(test_data_dir: Path) -> dict[str, Any]:
    """Load all test data files."""
    data = {}

    # Load user data
    user_data_file = test_data_dir / "user_data.json"
    if user_data_file.exists():
        with open(user_data_file) as f:
            data["user_data"] = json.load(f)

    # Load original broken config
    config_file = test_data_dir / "config.yaml"
    if config_file.exists():
        with open(config_file) as f:
            data["original_config"] = f.read()

    # Load original broken script
    script_file = test_data_dir / "process_records.py"
    if script_file.exists():
        with open(script_file) as f:
            data["original_script"] = f.read()

    return data


def ensure_directories(dirs: list[Path]) -> None:
    """Ensure all specified directories exist."""
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def create_submission_template(submissions_dir: Path) -> None:
    """Create a template directory for new model submissions."""
    template_dir = submissions_dir / "template"
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create template files
    files_to_create = [
        (
            "prompt_1_solution.py",
            "# Your refactored version of process_records.py\n"
            "# TODO: Implement your solution here\n",
        ),
        (
            "prompt_2_config_fixed.yaml",
            "# Your corrected version of config.yaml\n"
            "# TODO: Fix all YAML syntax and structure issues\n",
        ),
        (
            "prompt_2_config.json",
            "# JSON conversion of the corrected config\n"
            "# TODO: Convert YAML to JSON with proper data types\n",
        ),
        (
            "prompt_3_transform.py",
            "# Your transform_and_enrich_users function\n"
            "# TODO: Implement data transformation logic\n",
        ),
        (
            "prompt_4_api_sync.py",
            "# Your sync_users_to_crm function\n"
            "# TODO: Implement API synchronization with error handling\n",
        ),
    ]

    for filename, content in files_to_create:
        file_path = template_dir / filename
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(content)

    # Create README for the template
    readme_path = template_dir / "README.md"
    if not readme_path.exists():
        readme_content = """# Model Submission Template

Copy this template directory and rename it to your model name (e.g., `gpt4`,
`claude_sonnet_4`, `copilot`).

## Files to Complete

1. **prompt_1_solution.py** - Your refactored version of the original `process_records.py`
2. **prompt_2_config_fixed.yaml** - Corrected version of the broken `config.yaml`
3. **prompt_2_config.json** - JSON conversion of the corrected config
4. **prompt_3_transform.py** - Implementation of `transform_and_enrich_users` function
5. **prompt_4_api_sync.py** - Implementation of `sync_users_to_crm` function

## Testing Your Submission

After completing your files, run:
```bash
python run_benchmark.py --model your_model_name
```

## Scoring

Each prompt is worth 25 points (100 total):
- 60% or higher = PASS
- Below 60% = FAIL

Good luck!
"""
        with open(readme_path, "w") as f:
            f.write(readme_content)


def generate_comparison_chart(results: dict[str, Any], output_file: Path) -> None:
    """Generate a simple text-based comparison chart."""
    if "comparison" not in results or "ranking" not in results["comparison"]:
        return

    ranking = results["comparison"]["ranking"]
    if not ranking:
        return

    chart_content = []
    chart_content.append("AI CODE BENCHMARK - COMPARISON CHART")
    chart_content.append("=" * 50)
    chart_content.append("")

    # Overall ranking
    chart_content.append("OVERALL RANKING:")
    chart_content.append("-" * 20)
    for i, model in enumerate(ranking, 1):
        percentage = model["percentage"]
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        chart_content.append(f"{i:2d}. {model['model']:<20} {bar} {percentage:5.1f}%")

    chart_content.append("")

    # Prompt-specific performance
    if "prompt_performance" in results["comparison"]:
        chart_content.append("PROMPT-SPECIFIC PERFORMANCE:")
        chart_content.append("-" * 30)

        prompt_names = {
            "prompt_1": "Refactoring",
            "prompt_2": "YAML/JSON",
            "prompt_3": "Transformation",
            "prompt_4": "API Simulation",
        }

        for prompt_id, perf_data in results["comparison"]["prompt_performance"].items():
            prompt_name = prompt_names.get(prompt_id, prompt_id)
            chart_content.append(f"\n{prompt_name}:")
            chart_content.append(f"  Best Score: {perf_data['best_score']:.2f}/25")
            chart_content.append(f"  Average: {perf_data['avg_score']:.2f}/25")
            chart_content.append(f"  Pass Rate: {perf_data['pass_rate']}%")

    # Save chart
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(chart_content))


def validate_submission_structure(model_dir: Path) -> dict[str, bool]:
    """Validate that a model submission has the correct file structure."""
    required_files = [
        "prompt_1_solution.py",
        "prompt_2_config_fixed.yaml",
        "prompt_2_config.json",
        "prompt_3_transform.py",
        "prompt_4_api_sync.py",
    ]

    validation = {}
    for filename in required_files:
        file_path = model_dir / filename
        validation[filename] = file_path.exists() and file_path.stat().st_size > 0

    return validation


def get_model_statistics(results: dict[str, Any]) -> dict[str, Any]:
    """Extract key statistics from benchmark results."""
    if "models" not in results:
        return {}

    stats = {
        "total_models": len(results["models"]),
        "successful_runs": 0,
        "failed_runs": 0,
        "average_score": 0,
        "highest_score": 0,
        "lowest_score": 100,
        "prompt_stats": {},
    }

    valid_scores = []

    for _model_name, model_result in results["models"].items():
        if "error" in model_result:
            stats["failed_runs"] += 1
            continue

        stats["successful_runs"] += 1
        percentage = model_result.get("percentage", 0)
        valid_scores.append(percentage)

        if percentage > stats["highest_score"]:
            stats["highest_score"] = percentage
        if percentage < stats["lowest_score"]:
            stats["lowest_score"] = percentage

    if valid_scores:
        stats["average_score"] = round(sum(valid_scores) / len(valid_scores), 1)

    # Prompt-specific statistics
    for prompt_id in ["prompt_1", "prompt_2", "prompt_3", "prompt_4"]:
        prompt_scores = []
        prompt_passes = 0

        for model_result in results["models"].values():
            if "error" not in model_result and prompt_id in model_result.get("prompts", {}):
                prompt_result = model_result["prompts"][prompt_id]
                if "score" in prompt_result:
                    prompt_scores.append(prompt_result["score"])
                if prompt_result.get("passed", False):
                    prompt_passes += 1

        if prompt_scores:
            stats["prompt_stats"][prompt_id] = {
                "average_score": round(sum(prompt_scores) / len(prompt_scores), 1),
                "max_score": max(prompt_scores),
                "min_score": min(prompt_scores),
                "pass_rate": round(prompt_passes / len(prompt_scores) * 100, 1),
            }

    return stats
