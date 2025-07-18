# Adding New AI Models to the Benchmark

## Quick Start

1. Copy the template: `cp -r submissions/template submissions/your_model_name`
2. Present prompts to your AI model
3. Save responses in the appropriate files
4. Run: `python run_benchmark.py --model your_model_name`

## Detailed Process

### Step 1: Prepare Your Model Environment

Ensure you have access to the AI model you want to test. This could be:

- ChatGPT (GPT-4, GPT-3.5, etc.)
- Claude (Opus, Sonnet, Haiku)
- GitHub Copilot
- Local models (Llama, Mistral, etc.)
- Custom fine-tuned models

### Step 2: Set Up Submission Directory

```bash
# Create directory for your model
cp -r submissions/template submissions/your_model_name

# Example names:
# gpt4_turbo, claude_opus_3, copilot_2024, llama_70b

### Step 3: Present Context to AI Model

Before giving any prompts, provide the AI model with these context files:
Always include these files in your conversation:

test_data/config.yaml - The broken configuration file
test_data/process_records.py - The poorly written Python script
test_data/user_data.json - Sample user data

Copy-paste the exact file contents into your AI conversation before starting the prompts.
Step 4: Present Each Prompt
Prompt 1: Code Refactoring

Open prompts/prompt_1_refactoring.md
Copy the entire prompt text to your AI model
Save the AI's response as submissions/your_model_name/prompt_1_solution.py

Prompt 2: YAML/JSON Correction

Open prompts/prompt_2_yaml_json.md
Present the prompt to your AI model
Save the corrected YAML as prompt_2_config_fixed.yaml
Save the JSON conversion as prompt_2_config.json

Prompt 3: Data Transformation

Open prompts/prompt_3_transformation.md
Present the prompt to your AI model
Save the transform function as prompt_3_transform.py

Prompt 4: API Simulation

Open prompts/prompt_4_api_simulation.md
Present the prompt to your AI model
Save the API function as prompt_4_api_sync.py

Step 5: Validate Your Submission
Check that all files exist and have content:
ls -la submissions/your_model_name/
# Should show 5 files with reasonable file sizes

Step 6: Run the Benchmark
python run_benchmark.py --model your_model_name

Tips for Best Results
For the AI Model Interaction:

Be Specific: Ask for complete, working code
Mention Requirements: Remind the AI about function names, error handling requirements
Request Testing: Ask the AI to consider edge cases

Common Issues and Solutions:
Missing Function Names

Issue: Function not named exactly as required
Solution: Double-check function names match prompt requirements exactly

Import Errors

Issue: Missing required imports
Solution: Ensure all necessary imports are included at top of files

File Format Issues

Issue: YAML syntax errors, invalid JSON
Solution: Ask AI to validate the output format before submitting

Incomplete Error Handling

Issue: Code crashes on edge cases
Solution: Emphasize robust error handling in your prompts

Advanced Usage
Testing Variations
You can test different versions of the same model:
submissions/gpt4_version1/
submissions/gpt4_version2/  
submissions/gpt4_with_examples/

Custom Prompts
To add your own prompts:

Create new prompt file in prompts/
Add validation logic in benchmark/validators.py
Update scoring rubric in benchmark/scoring.py

Batch Testing
Test multiple models at once:
python run_benchmark.py  # Tests all models in submissions/

Contributing Results
Consider sharing your results:

Fork the repository
Add your model results
Submit a pull request with your findings
Help improve the benchmark tool!
