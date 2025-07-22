# Quick Start Guide - RealityCheckBench 🚀

Follow these steps to get the benchmark running in under 5 minutes!

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Repository name: `RealityCheckBench` (or your preferred name)
3. Description: "Benchmark tool for evaluating AI code generation capabilities"
4. Choose: Public or Private
5. Initialize with README: **No** (we'll add our own)
6. Click "Create repository"

## Step 2: Clone and Set Up Locally

```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/RealityCheckBench.git
cd RealityCheckBench

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

## Step 3: Add Project Files

1. Create the main files in your project root:
   - `run_benchmark.py` (copy from provided artifact)
   - `setup.py` (copy from provided artifact)
   - `README.md` (copy from provided artifact)

2. Create the `benchmark` directory and add:
   - `benchmark/__init__.py` (copy from provided artifact)
   - `benchmark/utils.py` (copy from provided **fixed** version)
   - `benchmark/validators.py` (copy from provided artifact)
   - `benchmark/scoring.py` (copy from provided artifact)

## Step 4: Run Setup

```bash
# Run the setup script to create directories and test data
python setup.py

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Test the Installation

```bash
# Create a test submission
# On Windows (PowerShell/CMD):
xcopy /E /I submissions\template submissions\test_model
# On macOS/Linux:
cp -r submissions/template submissions/test_model

# Run the benchmark (it will fail, but should run)
python run_benchmark.py --model test_model
```

You should see output like:

```
🚀 Testing model: test_model
==================================================

📝 Testing Refactoring & Analysis...
   ❌ FAILED - Score: 0/25

📝 Testing YAML/JSON Correction...
   ❌ FAILED - Score: 0/25

📝 Testing Data Transformation...
   ❌ FAILED - Score: 0/25

📝 Testing API Simulation...
   ❌ FAILED - Score: 0/25

🎯 Final Score: 0/100 (0.0%)
```

## Step 6: Add Real Model Submissions

### Option A: Manual Testing

1. Copy the template:

   ```bash
   # On Windows (PowerShell/CMD):
   xcopy /E /I submissions\template submissions\gpt4
   # On macOS/Linux:
   cp -r submissions/template submissions/gpt4
   ```

2. Manually add GPT-4's solutions to each file
3. Run: `python run_benchmark.py --model gpt4`

### Option B: Automated Testing

Create a script to automatically get AI responses and save them:

```python
# example_automate.py
import os
import openai  # or other AI SDK

def get_ai_solution(prompt, model="gpt-4"):
    # Your API call here
    pass

# Load prompts and get solutions
prompts = {
    "prompt_1": "Analyze the provided Python script...",
    "prompt_2": "The original process_records.py script will fail...",
    # etc.
}

# Save solutions to appropriate files
```

## Step 7: Run Full Benchmark

```bash
# Test all models in submissions directory
python run_benchmark.py

# View results
cat results/latest_results.json
cat results/summary_report_*.txt
```

## Step 8: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Initial commit: AI Code Benchmark tool"

# Push to GitHub
git push origin main
```

## 🎯 Complete File Checklist

Ensure you have all these files:

```
□ run_benchmark.py
□ setup.py
□ requirements.txt
□ README.md
□ benchmark/__init__.py
□ benchmark/utils.py (FIXED version)
□ benchmark/validators.py
□ benchmark/scoring.py
□ test_data/process_records.py
□ test_data/config.yaml
□ test_data/user_data.json
□ submissions/template/* (5 files)
□ results/ (empty directory)
```

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'yaml'"

```bash
pip install pyyaml
```

### "ModuleNotFoundError: No module named 'requests'"

```bash
pip install requests
```

### IndentationError in utils.py

Make sure you're using the **fixed** version of utils.py provided in the artifacts.

### Can't find test_data files

Run `python setup.py` to create all necessary files and directories.

## 🎉 Success

Once everything is working:

1. Add model submissions to test
2. Run benchmarks
3. Compare results
4. Share your findings!

For more details, see the main README.md file.
