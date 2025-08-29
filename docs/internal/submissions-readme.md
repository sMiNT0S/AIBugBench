---
title: Model Submission Workflow
description: Detailed workflow for preparing AI model prompt solutions, directory layout, and benchmarking your submission in AIBugBench.
search:
	boost: 0.8
---

## How to Submit AI Model Results

> Quick-start model submission instructions appear in [`docs/getting-started.md`](../getting-started.md) and developer workflow details in [`docs/developer-guide.md`](../developer-guide.md). This README expands on the directory layout and per‑prompt expectations.

This directory contains AI model submissions for benchmarking. Each model gets its own subdirectory with standardized file names.

## Submission Structure

Each model submission should follow this structure:

submissions/your_model_name/
├── prompt_1_solution.py          # Refactored process_records.py
├── prompt_2_config_fixed.yaml    # Corrected config.yaml
├── prompt_2_config.json          # JSON version of corrected config
├── prompt_3_transform.py         # transform_and_enrich_users function
└── prompt_4_api_sync.py          # sync_users_to_crm function

## Step-by-Step Guide

### 1. Prepare your environment

- Copy the `template/` directory: `cp -r template/ your_model_name/`
- Have the test data files ready from `test_data/`

### 2. Present each prompt

Give your AI model the exact prompts from the `prompts/` directory along with the test data files.

### 3. Save responses

Save each AI response in the corresponding file:

- **Prompt 1 response** → `prompt_1_solution.py`
- **Prompt 2 YAML fix** → `prompt_2_config_fixed.yaml`  
- **Prompt 2 JSON conversion** → `prompt_2_config.json`
- **Prompt 3 function** → `prompt_3_transform.py`
- **Prompt 4 API function** → `prompt_4_api_sync.py`

### 4. Test your submission

```bash
python run_benchmark.py --model your_model_name
```

## Example models

Check out the `example_model/` directory to see what a complete submission looks like.

## Tips for best results

1. **Include complete code** - Make sure functions are complete and can be imported
2. **Follow exact naming** - Function names must match exactly (e.g., `transform_and_enrich_users`)
3. **Test locally first** - Try running the code yourself before submitting
4. **Include error handling** - The benchmark rewards robust code

## Common issues

- **Import errors**: Make sure all required imports are included
- **Function not found**: Check function names match exactly
- **File format errors**: YAML and JSON must be valid syntax

Need help? Check the documentation in `docs/` or open an issue!

---

...existing code...
