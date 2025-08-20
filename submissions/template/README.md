# Model Submission Template

Copy this template directory and rename it to your model name (e.g., `gpt4`, `claude_sonnet_4`, `copilot`).

## Files to Complete

1. **prompt_1_solution.py** - Your refactored version of the original `process_records.py`
2. **prompt_2_config_fixed.yaml** - Corrected version of the broken `config.yaml`
3. **prompt_2_config.json** - JSON conversion of the corrected config
4. **prompt_3_transform.py** - Implementation of `transform_and_enrich_users` function
5. **prompt_4_api_sync.py** - Implementation of `sync_users_to_crm` function

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
