# Quick Start Guide

Get AIBugBench running and test your AI model's code generation skills in 15 minutes.

## Before You Begin

**What You Need**:

- Python 3.8 or newer
- Git (for downloading the project)
- 15 minutes of your time

**What This Guide Does**:
This guide walks you through setting up AIBugBench, running the built-in example to verify everything works, then testing your own AI model's code responses. You'll benchmark how well AI models fix deliberately broken Python, YAML, and JSON files across 7 quality categories.

**Choose Your Platform**:

- Windows users: Look for "Windows (CMD)" or "Windows (PowerShell)" instructions
- Mac/Linux users: Look for "macOS/Linux (Bash)" instructions

## Part 1: Get Set Up (5 minutes)

### Step 1: Download the Project

**Windows (CMD)**:

```cmd
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
```

**Windows (PowerShell)**:

```powershell
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
```

**macOS/Linux (Bash)**:

```bash
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
```

### Step 2: Set Up Python Environment

**Windows (CMD)**:

```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell)**:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux (Bash)**:

```bash
python3 -m venv venv
source venv/bin/activate
```

**Troubleshooting**: If `python` doesn't work, try `python3` or `py`. If virtual environment activation fails, you may need to enable script execution in PowerShell with `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

### Step 3: Create Test Data and Install Dependencies

**All Platforms**:

```bash
python setup.py
pip install -r requirements.txt
```

**What This Does**: The `setup.py` creates deliberately broken files (Python scripts, YAML config, JSON data) that AI models must fix. It also creates `ai_prompt.txt` - a comprehensive "wake up" message to prime your AI for better benchmark performance. Without this step, there's nothing to benchmark!

**Troubleshooting**: If you get "ModuleNotFoundError" for yaml or requests, run:

```bash
pip install pyyaml requests
```

## Part 2: Verify Everything Works (2 minutes)

### Step 4: Test the Installation

Let's run the benchmark with the built-in example model to make sure everything works:

**All Platforms**:

```bash
python run_benchmark.py --model example_model
```

**Expected Output** (yours may vary slightly):

Testing model: example_model
==================================================

Testing Refactoring & Analysis...
   PASSED - Score: 23.17/25

Testing YAML/JSON Correction...
   PASSED - Score: 25.00/25

Testing Data Transformation...
   PASSED - Score: 22.00/25

Testing API Simulation...
   PASSED - Score: 18.00/25

Final Score: 88.17/200 (44.1%)

```

**What This Means**:

- **PASSED**: The AI's code submission worked correctly
- **Score**: Points earned out of 25 possible per challenge
- **Final Score**: Total across all 4 challenges (out of 100, not 200 - ignore the display bug)
- **44.1%**: This example model performs moderately well

**Troubleshooting**:

- If you see "FAILED" scores, that's normal for some models
- If you get "FileNotFoundError", make sure you ran `python setup.py`
- If you get import errors, double-check your virtual environment is activated

## Part 3: Test Your AI Model (8 minutes)

### Step 5: Create Your Model Submission

First, create a folder for your AI model's code submissions:

**Windows (CMD)**:

```cmd
xcopy /E /I submissions\template submissions\my_model
```

**Windows (PowerShell)**:

```powershell
Copy-Item -Recurse submissions\template submissions\my_model
```

**macOS/Linux (Bash)**:

```bash
cp -r submissions/template submissions/my_model
```

**What This Does**: Creates a copy of the template folder with placeholder files that you'll replace with your AI's responses.

### Step 6: Get Your AI's Code Responses

Now you need to give your AI model the challenges and save their code responses. Here's how:

**💡 Start Here**: Begin by giving your AI the contents of `ai_prompt.txt` as the first message. This "wake up" prompt explains the benchmark format and scoring system, resulting in much better performance.

1. **Find the Challenge Prompts**: Look in the `prompts/` folder for these files:
   - `prompt_1_refactoring.md` - Fix a broken Python script
   - `prompt_2_yaml_json.md` - Fix broken YAML and JSON files
   - `prompt_3_transformation.md` - Transform user data correctly
   - `prompt_4_api_simulation.md` - Create secure API integration code

2. **Give Each Prompt to Your AI**: Copy the full text from each prompt file and paste it into your AI model (ChatGPT, Claude, Gemini, etc.).

3. **Save the AI's Python Code Responses**:
   - For Prompt 1: Save the AI's Python code as `submissions/my_model/prompt_1_solution.py`
   - For Prompt 2: Save the AI's Python code as `submissions/my_model/prompt_2_solution.py`
   - For Prompt 3: Save the AI's Python code as `submissions/my_model/prompt_3_solution.py`
   - For Prompt 4: Save the AI's Python code as `submissions/my_model/prompt_4_solution.py`

**Important**: Only save the Python code - not explanations or markdown formatting. The files should start with Python imports or function definitions.

### Step 7: Run Your Benchmark

**All Platforms**:

```bash
python run_benchmark.py --model my_model
```

**Expected Output** (will vary based on your AI's performance):

```
Testing model: my_model
==================================================

Testing Refactoring & Analysis...
   PASSED - Score: 15.32/25

Testing YAML/JSON Correction...
   FAILED - Score: 8.50/25

Testing Data Transformation...
   PASSED - Score: 19.25/25

Testing API Simulation...
   FAILED - Score: 12.75/25

Final Score: 55.82/200 (27.9%)
```

### Step 8: Understand Your Results

**Scoring Categories** (each challenge tests different aspects):

- **Syntax**: Does the code run without errors?
- **Structure**: Is the code well-organized?
- **Execution**: Does it solve the problem correctly?
- **Quality**: Is it readable and well-written?
- **Security**: Does it avoid security vulnerabilities?
- **Performance**: Is it reasonably efficient?
- **Maintainability**: Is it easy to modify and understand?

**Grade Scale**:

- 90-100: A (Excellent)
- 80-89: B (Good)
- 70-79: C (Satisfactory)
- 60-69: D (Needs Improvement)
- Below 60: F (Poor)

## Advanced: Test Multiple Models

Want to compare several AI models? Create separate folders for each:

**All Platforms**:

```bash
python run_benchmark.py --model gpt4
python run_benchmark.py --model claude
python run_benchmark.py --model gemini
```

Or test all models at once:

```bash
python run_benchmark.py
```

## Advanced: Automate the Process

If you want to automatically get AI responses via API instead of manual copy-paste:

### For OpenAI GPT Models

Create a file called `automate_openai.py`:

```python
import openai
import os
from pathlib import Path

# Set your API key
openai.api_key = "your-api-key-here"

# Load the prompt files
prompt_dir = Path("prompts")
submission_dir = Path("submissions/gpt4")
submission_dir.mkdir(exist_ok=True)

prompts = {
    "prompt_1_solution.py": "prompt_1_refactoring.md",
    "prompt_2_solution.py": "prompt_2_yaml_json.md", 
    "prompt_3_solution.py": "prompt_3_transformation.md",
    "prompt_4_solution.py": "prompt_4_api_simulation.md"
}

for solution_file, prompt_file in prompts.items():
    with open(prompt_dir / prompt_file, 'r') as f:
        prompt_text = f.read()
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=2000
    )
    
    # Extract just the Python code from the response
    code = response.choices[0].message.content
    
    with open(submission_dir / solution_file, 'w') as f:
        f.write(code)

print("Generated all AI responses. Run: python run_benchmark.py --model gpt4")
```

Then run: `python automate_openai.py`

### For Anthropic Claude

Replace the OpenAI section with:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key-here")

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt_text}]
)

code = response.content[0].text
```

## If Something Goes Wrong

### Common Issues

**"ModuleNotFoundError: No module named 'yaml'"**

```bash
pip install pyyaml
```

**"ModuleNotFoundError: No module named 'requests'"**

```bash
pip install requests
```

**"No such file or directory: test_data/..."**
Make sure you ran `python setup.py` to create the test files.

**"Permission denied" or script execution errors (Windows PowerShell)**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Virtual environment won't activate**

- Windows CMD: Use `venv\Scripts\activate.bat`
- Windows PowerShell: Use `venv\Scripts\Activate.ps1`
- macOS/Linux: Use `source venv/bin/activate`

**Unicode/encoding errors**
These are display issues that don't affect scoring. Your results are still valid.

**All scores are 0.00**
Check that your Python files contain actual code, not explanations or markdown formatting.

### Getting Help

1. **Check the Documentation**: Look in the `docs/` folder for detailed guides
2. **Review Your Files**: Make sure your Python files in `submissions/your_model/` contain valid Python code
3. **Test Step by Step**: Run each command individually to isolate problems
4. **Check Python Version**: Run `python --version` - you need Python 3.8 or newer

## Success

If everything worked, you now have:

- ✅ AIBugBench installed and working
- ✅ Baseline results from the example model
- ✅ Your AI model's performance scores
- ✅ Understanding of what the scores mean

**Next Steps**:

- Try different AI models and compare results
- Read the detailed documentation in `docs/` to understand the scoring system
- Check out `results/` folder for detailed analysis files
- Share your findings with the AI community!

For comprehensive details about the benchmark, scoring methodology, and advanced features, see the main README.md file.
