# Model Submission Template

Copy this template directory and rename it to your model name (e.g., `gpt4`, `claude_sonnet_4`, `copilot`).

## How to Use This Template

**IMPORTANT**: Each template file should be **completely replaced** with your AI's full solution. Do NOT try to fill in the template structure - replace everything with your AI's complete code/data.

### Files to Replace with AI Solutions

1. **prompt_1_solution.py** - Replace entire file with your AI's complete refactored version of `process_records.py`
2. **prompt_2_config_fixed.yaml** - Replace entire file with your AI's corrected YAML version of `config.yaml`
3. **prompt_2_config.json** - Replace entire file with your AI's complete JSON conversion of the corrected config
4. **prompt_3_transform.py** - Replace entire file with your AI's complete implementation of `transform_and_enrich_users` function
5. **prompt_4_api_sync.py** - Replace entire file with your AI's complete implementation of `sync_users_to_crm` function

### Workflow

1. **Copy template**: Create your model directory
2. **Get AI solutions**: Ask your AI to solve each prompt completely  
3. **Copy-paste replace**: Replace each template file entirely with AI's solution
4. **Test**: Run the benchmark to see your scores

## Testing Your Submission

After completing your files, run:

**All Platforms:**
```bash
python run_benchmark.py --model your_model_name
```

## Scoring

Each prompt uses a comprehensive **7-category scoring system** (25 points total):

- **Syntax**: Code compilation and basic structure
- **Structure**: Organization, imports, and function design
- **Execution**: Runtime behavior and correctness
- **Quality**: Code style, patterns, and best practices
- **Security**: Vulnerability detection and safe coding practices
- **Performance**: Algorithm efficiency and optimization analysis
- **Maintainability**: Code complexity and long-term maintenance

**Grading threshold**:
- 60% or higher (15+ points per prompt) = PASS
- Below 60% = FAIL

**Enhanced feedback**: The benchmark provides detailed category-specific feedback showing exactly which aspects passed or failed, with specific rationale for improvement.

> **📖 For detailed scoring rubrics, see `/docs/scoring_rubric.md`**

Good luck!
