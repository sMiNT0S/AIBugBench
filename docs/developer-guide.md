# Developer Guide

Complete guide for adding and testing AI models in AIBugBench.

## Quick Start

1. **Copy the template**:

   **Windows CMD:**

   ```cmd
   xcopy /E /I submissions\template submissions\your_model_name
   ```

   **Windows PowerShell:**

   ```powershell
   Copy-Item -Recurse submissions\template submissions\your_model_name
   ```

   **macOS/Linux Bash:**

   ```bash
   cp -r submissions/template submissions/your_model_name
   ```

2. Present prompts to your AI model
3. Save the AI's code responses in the appropriate files
4. Run the benchmark:

   ```bash
   python run_benchmark.py --model your_model_name
   ```

## Detailed Process

### Step 1: Prepare Your Model Environment

Ensure you have access to the AI model you want to test:

- ChatGPT (GPT-4, GPT-3.5, etc.)
- Claude (Opus, Sonnet, Haiku)
- GitHub Copilot
- Local models (Llama, Mistral, etc.)
- Custom fine-tuned models

**Example model names**: `gpt4_turbo`, `claude_opus_3`, `copilot_2024`, `llama_70b`

### Step 2: Prime Your AI Model

For best results, provide context to your AI model by using the `ai_prompt.md` file generated during setup:

```bash
# This file is created by setup.py
cat ai_prompt.md
```

This comprehensive context file includes:

- The broken test data files that need fixing
- Clear instructions about the benchmark requirements
- Examples of expected output formats

Copy-paste the entire contents of `ai_prompt.md` into your AI conversation before presenting any prompts.

### Step 3: Present Each Prompt

#### Prompt 1: Code Refactoring

1. Open `prompts/prompt_1_refactoring.md`
2. Copy the entire prompt text to your AI model
3. Save the AI's Python code response as `submissions/your_model_name/prompt_1_solution.py`

**Expected Output Structure:**

```python
#!/usr/bin/env python3
"""
Refactored process_records.py with modern Python practices.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any

def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_user_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load user data from JSON file with error handling."""
    try:
        with file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logging.error(f"Error loading {file_path}: {e}")
        return []

def filter_usa_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter users by USA country."""
    return [
        user for user in users 
        if isinstance(user, dict) and user.get('country', '').upper() == 'USA'
    ]

def main() -> None:
    """Main execution function."""
    logger = setup_logging()
    data_file = Path('user_data.json')
    
    if not data_file.exists():
        logger.error(f"Data file {data_file} not found")
        return
    
    users = load_user_data(data_file)
    usa_users = filter_usa_users(users)
    logger.info(f"Found {len(usa_users)} USA users out of {len(users)} total")
    
    for user in usa_users:
        print(f"USA User: {user.get('name', 'Unknown')} - {user.get('email', 'No email')}")

if __name__ == "__main__":
    main()
```

#### Prompt 2: YAML/JSON Correction

1. Open `prompts/prompt_2_yaml_json.md`
2. Present the prompt to your AI model
3. Save the corrected YAML as `prompt_2_config_fixed.yaml`
4. Save the JSON conversion as `prompt_2_config.json`

**Expected YAML Structure (prompt_2_config_fixed.yaml):**

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

**Expected JSON Structure (prompt_2_config.json):**

```json
{
  "use_legacy_paths": true,
  "paths": {
    "data_source": "/srv/data/production/users.json",
    "legacy_data_source": "./user_data.json",
    "log_file": "/var/log/processor.log"
  },
  "validation_rules": {
    "min_age": 18,
    "max_age": 120,
    "required_fields": ["name", "email", "country"]
  },
  "processing_options": {
    "batch_size": 100,
    "timeout_seconds": 30,
    "retry_attempts": 3
  },
  "api_keys": ["primary_key", "secondary_key", "backup_key"],
  "feature_flags": {
    "enable_logging": true,
    "strict_validation": false,
    "debug_mode": false
  }
}
```

#### Prompt 3: Data Transformation (Deterministic & Import-Safe)

1. Open `prompts/prompt_3_transformation.md`
2. Present the prompt to your AI model
3. Save the response as `prompt_3_transform.py`

**Key Requirements (now explicit for fairness):**

- Provide exactly one Python file (no packages) that defines `transform_and_enrich_users(user_list)`
- No side effects at import time (the benchmark imports the module)
- Deterministic: no randomness, no network, no external writes
- Transformations per user:
  - Coerce `id` to int when possible
  - Add `contact.email_provider` = domain after `@` if email present
  - Normalize `stats.age` to int when possible
  - Add `account_tier` using rules: Gold (>100 posts AND >300 comments), else Silver (>50 posts), else Bronze
  - Gracefully skip only the failing sub-step for malformed/missing data (never raise)
- Return a list the same length as the input
- Optional main guard demo allowed; ignored by scoring

#### Prompt 4: API Integration

1. Open `prompts/prompt_4_api_simulation.md`
2. Present the prompt to your AI model
3. Save the API function as `prompt_4_api_sync.py`

**Key Requirements:**

- Function must be named exactly: `sync_users_to_crm`
- Must handle various HTTP status codes (200, 400, 401, 503)
- Must include Bearer authentication and timeout settings

### Step 4: Validate Your Submission

Check that all files exist and have content:

```bash
# List all files
ls -la submissions/your_model_name/

# Quick syntax validation
python -m py_compile submissions/your_model_name/prompt_1_solution.py
python -c "import yaml; yaml.safe_load(open('submissions/your_model_name/prompt_2_config_fixed.yaml'))"
python -c "import json; json.load(open('submissions/your_model_name/prompt_2_config.json'))"
```

### Step 5: Run the Benchmark

```bash
python run_benchmark.py --model your_model_name
```

## Expected Results

Testing model: your_model_name

Testing Refactoring & Analysis...
  PASSED - Score: 23.50/25 (94.0%)

Testing YAML/JSON Correction...
  PASSED - Score: 25.00/25 (100.0%)

Testing Data Transformation...
  PASSED - Score: 24.75/25 (99.0%)

Testing API Simulation...
  PASSED - Score: 21.00/25 (84.0%)

Final Score: 94.25/100 (94.3%) - Grade: A

Results saved to: results/latest_results.json

## Tips for Best Results

### For AI Model Interaction

- **Be Specific**: Ask for complete, working code
- **Mention Requirements**: Remind the AI about function names and error handling requirements
- **Request Testing**: Ask the AI to consider edge cases and provide robust error handling
- **Complete Code Only**: Save exactly what the AI provides, including all imports and functions
- **Proper Indentation**: Maintain Python 4-space indentation standard

### Understanding Sabotage Patterns

The test data includes intentional bugs and issues. See **[Sabotage Documentation](sabotage-notes.md)** for details on:

- Syntax errors in YAML/JSON
- Logic bugs in Python code
- Security vulnerabilities
- Performance anti-patterns

## Common Issues and Solutions

### Missing Function Names

- **Issue**: Function not named exactly as required
- **Solution**: Double-check function names match prompt requirements exactly
  - Prompt 3: `transform_and_enrich_users`
  - Prompt 4: `sync_users_to_crm`

### Import Errors

- **Issue**: Missing required imports
- **Solution**: Ensure all necessary imports are included at top of files

### File Format Issues

- **Issue**: YAML syntax errors, invalid JSON
- **Solution**:
  - YAML: Use 2-space indentation, no tabs
  - JSON: Use proper boolean values (`true` not `"true"`)

### Incomplete Error Handling

- **Issue**: Code crashes on edge cases
- **Solution**: Emphasize robust error handling in your prompts

### Low Security Scores

- **Issue**: Security vulnerabilities detected
- **Solution**: Avoid:
  - `eval()` or `exec()`
  - Hardcoded API keys
  - Missing input validation
  - `shell=True` in subprocess

### Poor Performance Scores

- **Issue**: Inefficient algorithms detected
- **Solution**: Avoid:
  - Nested loops over same data (O(n²))
  - String concatenation in loops
  - Multiple sorting operations
  - Loading entire files unnecessarily

## Advanced Usage

### Repository Audit & Quality Gate

Run the consolidated repository audit before submitting significant changes:

```bash
python validation/repo_audit_enhanced.py --path . --json audit_report.json
```

Strict mode with minimum score threshold (fails repo health check below 85):

```bash
python validation/repo_audit_enhanced.py --path . --strict --min-score 85
```

JSON-only output (no console summary):

```bash
python validation/repo_audit_enhanced.py --path . --json audit_report.json --quiet
```

Recommended pre-PR checklist addition:

- [ ] Lint: `ruff check .`
- [ ] Tests: `pytest -q`
- [ ] Audit score ≥ 85 and no Critical findings

Audit scoring factors: structure completeness, security config presence, placeholder leakage, duplicated legacy files, ignored artifact hygiene, and documentation alignment.

### Testing Variations

Test different versions or prompting strategies:
submissions/gpt4_version1/
submissions/gpt4_version2/
submissions/gpt4_with_examples/
submissions/gpt4_with_context/

### Batch Testing

Test all models at once:

```bash
python run_benchmark.py
```

This tests all models in the `submissions/` directory.

### Comparing Models

Compare results between models:

```bash
python scripts/compare_benchmarks.py --models gpt4 claude_opus llama_70b
```

### Custom Validation

For additional validation beyond the benchmark:

```bash
python scripts/validate_docs.py
python scripts/validate_security.py
```

## Contributing

### Sharing Results

Consider contributing your results:

1. Fork the repository
2. Add your model results to `results/community/`
3. Update documentation with insights
4. Submit a pull request

### Adding New Prompts

To add custom challenges:

1. Create new prompt file in `prompts/`
2. Add validation logic in `benchmark/validators.py`
3. Update scoring rubric in `benchmark/scoring.py`
4. Document in scoring methodology

## Next Steps

- **Review detailed scores**: Check `results/summary_report_TIMESTAMP.txt`
- **Analyze weak areas**: Focus on categories with lowest scores
- **Iterate and improve**: Refine prompting strategies
- **Compare models**: Use comparison charts to evaluate different approaches

📊 **[Scoring Methodology](scoring-methodology.md)** | 🔧 **[Troubleshooting](troubleshooting.md)** | 🐛 **[Sabotage Notes](sabotage-notes.md)**
