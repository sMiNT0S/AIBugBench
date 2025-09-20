# Getting Started

Get AIBugBench running and test your AI model's code generation skills in 15 minutes.

## Before You Begin

**Prerequisites:**

- Python 3.13+
- Git
- 15 minutes

**What This Does:** Tests AI models on 4 coding challenges (refactoring, format conversion, data transformation, API integration) with comprehensive 7-category quality assessment including security, performance, and maintainability analysis.

## Step 1: Clone and Set Up Environment

**Windows CMD:**

```cmd
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python -m venv venv
venv\Scripts\activate
```

**Windows PowerShell:**

```powershell
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux Bash:**

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
pip install -r requirements.txt
```

**What This Creates:** Deliberately broken Python scripts, YAML config, and JSON data that AI models must fix (sabotage fixtures). Also creates `ai_prompt.md` - a comprehensive context file to give your AI for better benchmark performance.

💡 **Sabotage Fixtures:** The test data uses specific sabotage mechanisms to create realistic debugging scenarios. See **[Sabotage Documentation](sabotage-notes.md)** for details on how these challenges are designed.

## Step 3: Verify Installation

Test with the built-in example model:

**All Platforms:**

```bash
python run_benchmark.py --model example_model
```

**Expected Output:** Scores around 92.17/100 (A grade). If you see "FAILED" results or errors, check that Python 3.13+ is active and all dependencies installed.

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

📋 **[Detailed Developer Guide](developer-guide.md)**

**Windows CMD:**

```cmd
xcopy /E /I submissions\templates\template submissions\user_submissions\your_model_name
```

**Windows PowerShell:**

```powershell
Copy-Item -Recurse submissions\templates\template submissions\user_submissions\your_model_name
```

**macOS/Linux Bash:**

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

**Important:** Save only the Python/YAML/JSON code, not explanations or markdown formatting.

## Step 6: Run Benchmark and Review Results

**All Platforms:**

```bash
python run_benchmark.py --model your_model_name
```

**Results Location (v0.8.1+):**

- `results/latest_results.json` – Most recent run (pointer)
- `results/<RUN_TS>/latest_results.json` – Full run JSON (stable within timestamped folder)
- `results/<RUN_TS>/detailed/summary_report_<RUN_TS>.txt` – Human-readable analysis
- `results/<RUN_TS>/comparison_charts/comparison_chart.txt` – Visual progress bars

Historical runs accumulate; each benchmark invocation creates a new `<RUN_TS>` directory.

**Grade Scale:**

- A (90%+) Production Ready
- B (80%+) Good
- C (70%+) Satisfactory
- D (60%+) Minimal
- F (<60%) Failing

📊 **[Understanding Your Results](scoring-methodology.md)**

## Advanced: Automate the Process

**Note:** The automation script `scripts/automate_models.py` is currently **DEPRECATED** and operates in **offline-only mode**. No live API calls are supported.

**Recommended Approach:** Follow the manual workflow in Steps 4-5 above for reliable results.

## Troubleshooting

**Common Issues:**

- **"No module named 'yaml'":** Run `pip install pyyaml requests`
- **"Permission denied" (Windows PowerShell):** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **"FileNotFoundError: test_data":** Ensure you ran `python scripts/bootstrap_repo.py`
- **All scores are 0.00:** Check that your files contain actual code, not explanations
- **Virtual environment issues:** Try `python3` instead of `python`, or `py` on Windows

🔧 **[Comprehensive Troubleshooting Guide](troubleshooting.md)** - Includes Tiered Structure Errors taxonomy and detailed solutions.

## What You've Accomplished

✅ AIBugBench installed and verified  
✅ Your AI model benchmarked across 4 challenges  
✅ Comprehensive quality assessment including security and performance analysis  
✅ Detailed results saved for analysis and comparison  

## Next Steps

- Try different AI models
- Explore detailed documentation
- Contribute new challenges to the benchmark

📖 **[Full Documentation](index.md)** | 👨‍💻 **[Developer Guide](developer-guide.md)** | 📊 **[Scoring Details](scoring-methodology.md)**
