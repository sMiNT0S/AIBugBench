# Getting Started

Get AIBugBench running and test a model fast.

## Before You Begin

**Prerequisites**

- Python 3.13+
- Git

You’ll run 4 fixed challenges (refactor, config repair, transform, API). Scoring covers 7 quality dimensions.

## Step 1: Clone and Set Up Environment

=== "Windows PowerShell"

    ```powershell
    git clone https://github.com/sMiNT0S/AIBugBench.git
    cd AIBugBench
    python -m venv venv
    venv\Scripts\Activate.ps1
    ```

=== "Windows CMD"

    ```cmd
    git clone https://github.com/sMiNT0S/AIBugBench.git
    cd AIBugBench
    python -m venv venv
    venv\Scripts\activate
    ```

=== "macOS/Linux"

    ```bash
    git clone https://github.com/sMiNT0S/AIBugBench.git
    cd AIBugBench
    python3 -m venv venv
    source venv/bin/activate
    ```

## Step 2: Create Test Data and Install Dependencies

**All Platforms:**

```bash
python scripts/bootstrap_repo.py
pip install -r requirements.lock
```

This creates deliberately broken test data (sabotage fixtures) and `ai_prompt.md` for AI context. See **[Sabotage Notes](sabotage-notes.md)** for details.

## Step 3: Verify Installation

Test with the built-in example model:

**All Platforms:**

```bash
python run_benchmark.py --model example_model
```

**Expected Output:** Scores around 90/100 (A grade). If you see "FAILED" results or errors, check that Python 3.13+ is active and all dependencies installed.

## Directory Overview

Core structure:

- `run_benchmark.py` - Orchestrates scoring
- `scripts/bootstrap_repo.py` - Generates sabotage fixtures and prompt file
- `benchmark/` - Validation and scoring engine
- `prompts/` - Challenge definitions
- `test_data/` - Deliberately broken inputs
- `submissions/` - Your model solutions
- `results/` - Saved JSON and text reports

## Step 4: Create Your AI Model Submission

=== "Windows PowerShell"

    ```powershell
    Copy-Item -Recurse submissions\templates\template submissions\user_submissions\your_model_name
    ```

=== "Windows CMD"

    ```cmd
    xcopy /E /I submissions\templates\template submissions\user_submissions\your_model_name
    ```

=== "macOS/Linux"

    ```bash
    cp -r submissions/templates/template submissions/user_submissions/your_model_name
    ```

## Step 5: Get AI Responses and Save Code

1. **Prime your AI** with the contents of `ai_prompt.md` for optimal results
2. **Give each prompt** from `prompts/` folder to your AI model:
   - `prompt_1_refactoring.md` → Save Python code as `prompt_1_solution.py`
   - `prompt_2_yaml_json.md` → Save YAML as `prompt_2_config_fixed.yaml` and JSON as `prompt_2_config.json`
   - `prompt_3_transformation.md` → Save Python code as `prompt_3_transform.py`
   - `prompt_4_api_simulation.md` → Save Python code as `prompt_4_api_sync.py`

Save only the Python/YAML/JSON code (no explanations or markdown).

## Step 6: Run Benchmark and Review Results

**All Platforms:**

```bash
python run_benchmark.py --model your_model_name
```

Results use timestamped directories. See the [User Guide](user-guide.md#running-your-first-benchmark) for the full layout.

Quick access:

- `results/latest_results.json` – Pointer to most recent run
- `results/<RUN_TS>/latest_results.json` – Full run JSON
- `results/<RUN_TS>/detailed/summary_report_<RUN_TS>.txt` – Human-readable analysis
- `results/<RUN_TS>/comparison_charts/comparison_chart.txt` – Visual progress bars

Historical runs accumulate; each benchmark invocation creates a new `<RUN_TS>` directory.

See [Scoring Methodology – Grade Scale](scoring-methodology.md#grade-scale) for letter-grade thresholds.

📊 **[Understanding Your Results](scoring-methodology.md)**

## Troubleshooting

**Common Issues:**

- "No module named 'yaml'": `pip install pyyaml requests`
- Permission denied (PowerShell): `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- FileNotFoundError: test_data: `python scripts/bootstrap_repo.py`
- All scores are 0.00: files must contain code only (no markdown)
- Venv issues: try `python3` or `py` on Windows

🔧 **[Comprehensive Troubleshooting Guide](troubleshooting.md)** - Includes Tiered Structure Errors taxonomy and detailed solutions.

## Next Steps

- Try other models
- Read your results summary and dig into details
- See **[Scoring Methodology](scoring-methodology.md)**

## Quick Reference (Cheat Sheet)

```bash
# Create venv and install (pinned)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.lock
python scripts/bootstrap_repo.py

# Run an example model
python run_benchmark.py --model example_model

# Run your model
python run_benchmark.py --model your_model_name

# Results (quick look)
cat results/latest_results.json | jq '.summary'
```
