# API Reference
<!-- markdownlint-disable MD046 -->
> Live, importable modules from the repo. Build step sets `PYTHONPATH` so this works without a wheel.

!!! tip "Reading order"
    Start with the **Module map** to see what's where. Then skim the snippets and CLI.
    The **Full reference** at the bottom is collapsed by default.

## Module map

- `benchmark.scoring` — Scoring engine and helpers; `BenchmarkScorer`, `calculate_grade`, comparison helpers.
- `benchmark.validators` — Prompt validators and analyzers (security, performance, maintainability).
- `benchmark.secure_runner` — Sandboxed execution utilities. `SecureRunner` provides sandbox context and guarded execution.
- `benchmark.utils` — Utilities for test data loading, directory setup, comparisons, and model stats.
- `benchmark.types` — TypedDict schemas describing prompt results and overall output structures.

---

### Selected snippets

**Strict sandbox environment (minimal, readable extract):**

```python
def _prepare_environment(self, sandbox_dir: Path) -> None:
    os.environ.clear()
    home_dir = sandbox_dir / "home"
    tmp_dir = sandbox_dir / "temp"
    home_dir.mkdir(exist_ok=True)
    tmp_dir.mkdir(exist_ok=True)

    base_env = {
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),  # Windows
        "TEMP": str(tmp_dir),
        "TMP": str(tmp_dir),
        "TMPDIR": str(tmp_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "AIBUGBENCH_SANDBOX_ROOT": str(sandbox_dir.resolve()),
        "AIBUGBENCH_ALLOW_NETWORK": "1" if self.allow_network else "0",
    }
    for key in ["PATH","SystemRoot","WINDIR","COMSPEC",
                "NUMBER_OF_PROCESSORS","PROCESSOR_ARCHITECTURE","LANG","LC_ALL"]:
        val = self._original_env.get(key)
        if val:
            base_env[key] = val
    os.environ.update(base_env)
```

**Run a Python entry inside the sandbox (ensures guards via `sitecustomize.py`):**

```python
def run_python_sandboxed(self, args: list[str], *, timeout: int = 10,
                         cwd: Path | None = None, memory_mb: int = 512):
    cmd = [sys.executable, "-B", *args]    # -B keeps .pyc off; still loads sitecustomize
    env = os.environ.copy()                 # inherit sandbox env
    if cwd:
        # ensure sandbox folder (with sitecustomize.py) is on import path
        env["PYTHONPATH"] = str(cwd) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    # platform-specific resource limits applied here...
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=timeout, check=False)
```

---

---

## Snippets from the runner

### Robust Unicode-safe printing

```python
def safe_print(self, message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        ascii_message = message.encode("ascii", "ignore").decode("ascii")
        print(ascii_message)
    except Exception as e:
        with contextlib.suppress(Exception):
            print(f"Print error: {e!s}")
```

### Detailed scoring formatting (compact, two-line display)

```python
def format_detailed_score(self, detailed_scoring: dict[str, Any]) -> str:
    lines, categories = [], []
    order = ["syntax","structure","execution","quality","security","performance","maintainability"]
    for cat in order:
        if cat in detailed_scoring:
            s = detailed_scoring[cat]
            categories.append(f"{cat.title()}: {s.get('earned',0):.1f}/{s.get('max',0):.1f}")
    mid = len(categories) // 2
    if categories:
        lines.append(f"     └─ {', '.join(categories[:mid])}")
        if len(categories) > mid:
            lines.append(f"        {', '.join(categories[mid:])}")
    return "\n".join(lines)
```

### Atomic result write (tmp file swap)

```python
def _atomic_write_json(self, path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
```

---

## Recipes

## Execute an existing script inside a sandbox

```python
from benchmark.secure_runner import SecureRunner
from pathlib import Path

runner = SecureRunner(model_name="example_model", allow_network=False)
with runner.sandbox() as root:
    result = runner.run_python_sandboxed(
        ["-m", "module_to_run", "--flag"],
        cwd=Path(root),
        timeout=10,
        memory_mb=512,
    )
    print(result.stdout)
```

## Parse CLI args without running the benchmark

```python
from run_benchmark import parse_args
args = parse_args(["--model","example_model","--mem","768","--quiet"])
assert args.model == "example_model" and args.mem == 768 and args.quiet
```

## CLI Reference

## Usage

```bash
python run_benchmark.py [--model NAME | --all-models] [--workers N]
                        [--submissions-dir DIR] [--results-dir DIR]
                        [--mem {256,384,512,768,1024}]
                        [--unsafe] [--allow-network] [--trusted-model]
                        [--no-metadata] [-q|--quiet]
```

## Arguments

| Flag | Type / Values | Default | Description |
|-----:|:--------------|:--------|:------------|
| `--model` | string | — | Test a single model by name. |
| `--all-models` | flag | `false` | Test all discovered models (if supported in your runner). |
| `--workers` | int | `1` | Number of concurrent workers when testing multiple models. |
| `--submissions-dir` | path | `submissions` | Root directory containing model submissions. |
| `--results-dir` | path | `results` | Directory where results, summaries and charts are written. |
| `--mem` | one of `256,384,512,768,1024` | `512` | Memory limit (MB) for sandboxed execution. |
| `--unsafe` | flag | `false` | Disable sandbox/resource isolation. Dangerous; for trusted runs only. |
| `--allow-network` | flag | `false` | Allow network access during execution. |
| `--trusted-model` | flag | `false` | Suppress unsafe-mode confirmation (use in CI for trusted submissions). |
| `--no-metadata` | flag | `false` | Skip environment/git/dependency metadata collection. |
| `-q, --quiet` | flag | `false` | Suppress non-essential output. |

## Examples

```bash
# Single model, default sandbox & limits
python run_benchmark.py --model example_model

# All models with 4 workers, custom results dir
python run_benchmark.py --all-models --workers 4 --results-dir out/results

# CI-like trusted run with network allowed and larger RAM cap
python run_benchmark.py --model gpt4 --unsafe --trusted-model --allow-network --mem 1024 -q
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIBUGBENCH_RESULTS_DIR` | `results/` | Override default results directory |
| `AIBUGBENCH_TIMEOUT` | `30` | Default operation timeout |
| `AIBUGBENCH_DEBUG` | `false` | Enable debug logging |
| `PYTHONPATH` | - | Include benchmark modules in path |

### Programmatic usage (high level)

```python
from run_benchmark import AICodeBenchmark

bench = AICodeBenchmark(submissions_dir="submissions", results_dir="results")
result = bench.run_single_model("example_model")
print(result["overall_score"], result["percentage"])
```

### Representative output: (terminal, .json, results)

## Terminal output + security banner

??? details "Example terminal output (multi-model run)"
    ```text
    > python run_benchmark.py
    ╔══════════════════════════════════════╗
    ║      AIBugBench Security Status      ║
    ╠══════════════════════════════════════╣
    ║Sandboxing:     ENABLED               ║
    ║Network:        BLOCKED               ║
    ║Subprocess:     BLOCKED               ║
    ║Filesystem:     CONFINED              ║
    ║Env Clean:      CLEANED               ║
    ║ResourceLimits: ENFORCED              ║
    ║Trusted Model:  YES                   ║
    ╚══════════════════════════════════════╝
    Discovered models: reference=1 user=0 templates=OK
    🔍 Discovered 1 model(s): example_model

    Testing model: example_model
    ==================================================

    📝 Testing Refactoring & Analysis...
       ✅ PASSED - Score: 23.17/25
         └─ Syntax: 5.0/5.0, Structure: 2.4/3.0, Execution: 6.0/6.0
            Quality: 3.0/3.0, Security: 4.0/4.0, Performance: 1.9/2.0, Maintainability: 0.9/2.0

    📝 Testing YAML/JSON Correction...
       ✅ PASSED - Score: 25.00/25
         └─ Syntax: 4.0/4.0, Structure: 6.0/6.0, Execution: 8.0/8.0
            Quality: 6.0/6.0, Security: 1.0/1.0, Performance: 0.0/0.0, Maintainability: 0.0/0.0

    📝 Testing Data Transformation...
    2025-09-30 02:19:47,031 - transform_module - WARNING - User 103: Email is null, cannot extract provider
    2025-09-30 02:19:47,031 - transform_module - WARNING - User 999: Missing or invalid 'contact' field
    2025-09-30 02:19:47,032 - transform_module - WARNING - User 999: Missing or invalid 'stats' field
    2025-09-30 02:19:47,032 - transform_module - INFO - Successfully transformed 6 users
        ✅ PASSED - Score: 22.00/25
         └─ Syntax: 3.0/3.0, Structure: 3.0/3.0, Execution: 12.0/12.0
            Quality: 3.0/3.0, Security: 0.0/1.0, Performance: 1.0/1.0, Maintainability: 0.0/2.0

    📝 Testing API Simulation...
    2025-09-30 02:19:47,072 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,072 - api_module - INFO - Successfully synced users. Job ID: abc123
    ✅ Sync successful! Job ID: abc123
    2025-09-30 02:19:47,072 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,072 - api_module - WARNING - Unexpected success status code: 400
    ⚠️  Warning: Unexpected response status 400
    2025-09-30 02:19:47,072 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,073 - api_module - WARNING - Unexpected success status code: 401
    ⚠️  Warning: Unexpected response status 401
    2025-09-30 02:19:47,073 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,073 - api_module - WARNING - Unexpected success status code: 503
    ⚠️  Warning: Unexpected response status 503
    2025-09-30 02:19:47,073 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,073 - api_module - ERROR - Network connection error: Network error
    ❌ Network Error: Unable to connect to CRM system
       Please check your internet connection and try again
    2025-09-30 02:19:47,073 - api_module - INFO - Attempting to sync 1 users to CRM system
    2025-09-30 02:19:47,073 - api_module - INFO - Successfully synced users. Job ID: test123
    ✅ Sync successful! Job ID: test123
       ✅ PASSED - Score: 22.00/25
         └─ Syntax: 2.0/2.0, Structure: 3.0/3.0, Execution: 7.0/7.0
            Quality: 3.0/3.0, Security: 6.0/7.0, Performance: 0.0/2.0, Maintainability: 1.0/1.0

    🎯 Final Score: 92.17/100 (92.2%)
    📄 Summary report: results\20250930_021946\detailed\summary_report_20250930_021946.txt
    📊 Comparison chart: results\20250930_021946\comparison_charts\comparison_chart.txt

    🎉 Benchmark completed! Tested 1 model(s)

    🏆 Top Performers:
      1. example_model: 92.2%
      2. (n/a)

    📁 Detailed results have been saved to:
      • results/latest_results.json - Complete data with detailed scoring
      • results/detailed/summary_report_*.txt - Summary with enhanced feedback
      • results/comparison_charts/comparison_chart_*.txt - Visual comparison with progress bars

    For complete scoring breakdowns and analysis, check these files in the /results directory.
    ```

## JSON results file

??? details "Detailed JSON results file (results/latest_results.json)"
    ```json
    {% include-markdown "../results/latest_results.json" %}
    ```

## Comparison Chart Format

```text
Model Comparison:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

model_1         [████████████████████████████████████████████░░░░] 94.3%
model_2         [███████████████████████████████████████████░░░░░] 91.8%
model_3         [████████████████████████████████████░░░░░░░░░░░░] 76.5%
example_model   [██████████████████████████████████████████████░░] 92.2%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Configuration Files

### Test Data Configuration

Configuration files are generated by `scripts/bootstrap_repo.py` and located in `test_data/`:

- `config.yaml` - Deliberately broken YAML configuration (multi-document)
- `user_data.json` - Sample user data for transformation
- `process_records.py` - Python script requiring refactoring

### Loading configuration snippets (collapsed)

??? details "Safe YAML loading"
    ```python
    import yaml

    # Load multi-document YAML safely
    with open('test_data/config.yaml', 'r') as f:
        docs = list(yaml.safe_load_all(f))
        # Merge documents (last document wins)
        config = {}
        for doc in docs:
            if doc:
                config.update(doc)
    ```

??? details "Configuration structure"
    ```yaml
    use_legacy_paths: true
    paths:
      data_source: /srv/data/production/users.json
      legacy_data_source: ./user_data.json
      log_file: /var/log/processor.log
    validation_rules:
      min_age: 18
      max_age: 120
      required_fields:
        - name
        - email
        - country
    processing_options:
      batch_size: 100
      timeout_seconds: 30
      retry_attempts: 3
    api_keys:
      - primary_key
      - secondary_key
      - backup_key
    feature_flags:
      enable_logging: true
      strict_validation: false
      debug_mode: false
    ```

### Validation functions (collapsed)

??? details "Prompt 1 (Code Refactoring), 2 (YAML/JSON Correction), 3 (Data Transformation), 4 (API Integration)"

    #### Prompt 1: Code Refactoring

    ```python
    def validate_prompt1_refactoring(solution_path: str) -> dict:
        """
        Validate refactored Python code.
        
        Returns:
            dict: {
                'score': float,
                'max_score': 25,
                'passed': bool,
                'details': {
                    'syntax': bool,
                    'execution': bool,
                    'security': list,
                    'performance': list,
                    'maintainability': list
                }
            }
        """
    ```

    #### Prompt 2: YAML/JSON Correction

    ```python
    def validate_prompt2_yaml_json(yaml_path: str, json_path: str) -> dict:
        """
        Validate corrected YAML and JSON files.
        
        Returns:
            dict: {
                'score': float,
                'max_score': 25,
                'passed': bool,
                'details': {
                    'yaml_valid': bool,
                    'json_valid': bool,
                    'equivalence': bool,
                    'structure': dict
                }
            }
        }
    """
    ```

    #### Prompt 3: Data Transformation

    ```python
    def validate_prompt3_transformation(transform_path: str) -> dict:
        """
        Validate data transformation function.
        
        Returns:
            dict: {
                'score': float,
                'max_score': 25,
                'passed': bool,
                'details': {
                    'function_exists': bool,
                    'signature_correct': bool,
                    'transformations': dict,
                    'business_rules': bool
                }
            }
        """
    ```

    #### Prompt 4: API Integration

    ```python
    def validate_prompt4_api_integration(api_path: str) -> dict:
        """
        Validate API integration function.
        
        Returns:
            dict: {
                'score': float,
                'max_score': 25,
                'passed': bool,
                'details': {
                    'function_exists': bool,
                    'authentication': bool,
                    'error_handling': dict,
                    'security': dict
                }
            }
        """
    ```

## Error Handling

### Common Exit Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 0 | Success | - |
| 1 | General error | Check error message |
| 2 | Missing model | Verify model name and directory |
| 3 | Validation failure | Review submission files |
| 4 | Timeout exceeded | Increase timeout or optimize code |
| 5 | File not found | Ensure all required files exist |

## Platform-Specific Notes

### Windows

- Use `python` or `py` command
- Paths use backslashes or forward slashes
- PowerShell may require execution policy adjustment

### macOS/Linux

- Use `python3` command
- Ensure proper file permissions
- May need to use `sudo` for certain operations

### Docker

- Mount submissions directory as volume
- Set environment variables in container
- Use non-root user for security

## Python API

### Core Modules

#### benchmark.runner

Main benchmark execution module.

```python
from benchmark.runner import BenchmarkRunner

# Initialize runner
runner = BenchmarkRunner(
    model_name="gpt4",
    results_dir="results/",
    timeout=30
)

# Run all tests
results = runner.run_all_tests()

# Run specific test
prompt1_result = runner.run_test("prompt_1_refactoring")
```

#### benchmark.validators

Validation logic for each prompt.

```python
from benchmark.validators import (
    validate_prompt1_refactoring,
    validate_prompt2_yaml_json,
    validate_prompt3_transformation,
    validate_prompt4_api_integration
)

# Validate refactored code
result = validate_prompt1_refactoring(
    solution_path="submissions/model/prompt_1_solution.py"
)
print(f"Score: {result['score']}/{result['max_score']}")
```

#### benchmark.scoring

Scoring engine with 7-category assessment.

```python
from benchmark.scoring import calculate_score, get_grade

# Calculate total score
results = {
    'prompt_1': {'score': 23.5, 'max_score': 25},
    'prompt_2': {'score': 25.0, 'max_score': 25},
    'prompt_3': {'score': 24.5, 'max_score': 25},
    'prompt_4': {'score': 21.0, 'max_score': 25}
}

total_score = calculate_score(results)
grade = get_grade(total_score)
print(f"Total: {total_score}/100 - Grade: {grade}")
```

#### benchmark.utils

Utility functions for file operations and formatting.

```python
from benchmark.utils import (
    safe_load_json,
    safe_load_yaml,
    format_results,
    create_comparison_chart
)

# Safe file loading with error handling
data = safe_load_json("user_data.json")
config = safe_load_yaml("config.yaml")

# Format results for display
formatted = format_results(results)
print(formatted)

# Create comparison chart
chart = create_comparison_chart(results)
print(chart)
```

## Full API reference (collapsed)

??? details "benchmark.scoring"
    ::: benchmark.scoring
        options:
          members:
            - BenchmarkScorer
            - calculate_grade
            - generate_feedback_summary
            - generate_improvement_suggestions
            - compare_models
            - generate_badge
          filters:
            - "!^_"
          show_symbol_type_heading: true
          separate_signature: true

??? details "benchmark.validators"
    ::: benchmark.validators
        options:
          filters:
            - "!^_"
          show_symbol_type_heading: true
          separate_signature: true

??? details "benchmark.secure_runner"
    ::: benchmark.secure_runner.SecureRunner
        options:
          members:
            - sandbox
            - run_with_limits
            - run_python_sandboxed
          filters:
            - "!^_"
          show_symbol_type_heading: true
          separate_signature: true

??? example "Sandbox snippet"
    ```python
    def safe_print(msg: str) -> None:
        ...
    ```

??? details "benchmark.utils"
    ::: benchmark.utils
        options:
          filters:
            - "!^_"
          show_symbol_type_heading: true
          separate_signature: true

??? details "benchmark.types"
    ::: benchmark.types
        options:
          show_symbol_type_heading: true
          separate_signature: true

## See Also

- **[Getting Started](getting-started.md)** - Initial setup and quick start
- **[Developer Guide](developer-guide.md)** - Adding and testing models
- **[Scoring Methodology](scoring-methodology.md)** - Understanding scores
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
