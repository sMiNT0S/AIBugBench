# Adding New AI Models to the Benchmark

## Quick Start

1. **Copy the template**:

   **Windows (CMD):**
   ```cmd
   xcopy /E /I submissions\template submissions\your_model_name
   ```

   **Windows (PowerShell):**
   ```powershell
   Copy-Item -Recurse submissions\template submissions\your_model_name
   ```

   **macOS/Linux (Bash):**
   ```bash
   cp -r submissions/template submissions/your_model_name
   ```

2. Present prompts to your AI model
3. Save the AI's code responses in the appropriate files
4. Run the benchmark:

   **All Platforms:**
   ```bash
   python run_benchmark.py --model your_model_name
   ```

## Detailed Process

### Step 1: Prepare Your Model Environment

Ensure you have access to the AI model you want to test. This could be:

- ChatGPT (GPT-4, GPT-3.5, etc.)
- Claude (Opus, Sonnet, Haiku)
- GitHub Copilot
- Local models (Llama, Mistral, etc.)
- Custom fine-tuned models

### Step 2: Set Up Submission Directory

**Windows (CMD):**
```cmd
xcopy /E /I submissions\template submissions\your_model_name
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse submissions\template submissions\your_model_name
```

**macOS/Linux (Bash):**
```bash
cp -r submissions/template submissions/your_model_name
```

**Example model names**: gpt4_turbo, claude_opus_3, copilot_2024, llama_70b

### Step 3: Present Context to AI Model

Before giving any prompts to your AI model, provide it with these context files:

- `test_data/config.yaml` - The broken configuration file that needs fixing
- `test_data/process_records.py` - The poorly written Python script that needs refactoring  
- `test_data/user_data.json` - Sample user data for transformation testing

**Important**: Copy-paste the exact file contents into your AI conversation before starting the prompts. This gives the AI the context it needs to understand what's broken and needs fixing.

### Step 4: Present Each Prompt

#### Prompt 1: Code Refactoring
1. Open `prompts/prompt_1_refactoring.md`
2. Copy the entire prompt text to your AI model
3. Save the AI's Python code response as `submissions/your_model_name/prompt_1_solution.py`

#### Prompt 2: YAML/JSON Correction
1. Open `prompts/prompt_2_yaml_json.md`
2. Present the prompt to your AI model
3. Save the corrected YAML as `prompt_2_config_fixed.yaml`
4. Save the JSON conversion as `prompt_2_config.json`

#### Prompt 3: Data Transformation
1. Open `prompts/prompt_3_transformation.md`
2. Present the prompt to your AI model
3. Save the transform function as `prompt_3_transform.py`

#### Prompt 4: API Integration
1. Open `prompts/prompt_4_api_simulation.md`
2. Present the prompt to your AI model
3. Save the API function as `prompt_4_api_sync.py`

### Step 5: Validate Your Submission

Check that all files exist and have content:

**Windows (CMD):**
```cmd
dir submissions\your_model_name
```

**Windows (PowerShell):**
```powershell
Get-ChildItem submissions\your_model_name
```

**macOS/Linux (Bash):**
```bash
ls -la submissions/your_model_name/
```

You should see 5 files with reasonable file sizes (not empty).

### Step 6: Run the Benchmark

**All Platforms:**
```bash
python run_benchmark.py --model your_model_name
```

## Tips for Best Results

### For AI Model Interaction

- **Be Specific**: Ask for complete, working code
- **Mention Requirements**: Remind the AI about function names and error handling requirements
- **Request Testing**: Ask the AI to consider edge cases and provide robust error handling

## Common Issues and Solutions

### Missing Function Names
- **Issue**: Function not named exactly as required
- **Solution**: Double-check function names match prompt requirements exactly

### Import Errors
- **Issue**: Missing required imports
- **Solution**: Ensure all necessary imports are included at top of files

### File Format Issues
- **Issue**: YAML syntax errors, invalid JSON
- **Solution**: Ask AI to validate the output format before submitting

### Incomplete Error Handling
- **Issue**: Code crashes on edge cases
- **Solution**: Emphasize robust error handling in your prompts

## Advanced Usage

### Testing Variations
You can test different versions of the same model:
- `submissions/gpt4_version1/`
- `submissions/gpt4_version2/`  
- `submissions/gpt4_with_examples/`

### Custom Prompts
To add your own prompts:
1. Create new prompt file in `prompts/`
2. Add validation logic in `benchmark/validators.py`
3. Update scoring rubric in `benchmark/scoring.py`

### Batch Testing
Test multiple models at once:

**All Platforms:**
```bash
python run_benchmark.py
```
This tests all models in the `submissions/` directory.

### Contributing Results
Consider sharing your results:
1. Fork the repository
2. Add your model results
3. Submit a pull request with your findings
4. Help improve the benchmark tool!
