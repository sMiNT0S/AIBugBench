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

```bash
python run_benchmark.py --model your_model_name
```

## Scoring

Each prompt is worth 25 points (100 total):

- 60% or higher = PASS
- Below 60% = FAIL

Good luck!
