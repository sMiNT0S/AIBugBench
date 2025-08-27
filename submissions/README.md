---
title: Model Submission Workflow
description: Detailed workflow for preparing AI model prompt solutions, directory layout, and benchmarking your submission in AIBugBench.
search:
  boost: 0.8
---

## How to Submit AI Model Results

> Quick-start model submission instructions appear in [`docs/getting-started.md`](../docs/getting-started.md) and developer workflow details in [`docs/developer-guide.md`](../docs/developer-guide.md). This README expands on the directory layout and per‑prompt expectations.

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

## prompts/prompt_1_refactoring.md

## Prompt 1: Code Understanding and Refactoring

## Instructions for AI model

Analyze the provided Python script `process_records.py`.

### Task 1: Identify problems

List and explain at least five distinct problems with the script. Cover issues related to:

- Style (PEP 8 compliance)
- Efficiency
- Error handling
- Logical correctness

### Task 2: Refactor the code  

Provide a complete, refactored version of the script. The new script should be:

- Modular and well-organized
- Efficient and performant
- Robust (handle potential FileNotFoundError, KeyError, etc.)
- Adherent to modern Python best practices

### Context files

You will also have access to:

- `config.yaml` - Configuration file (has issues)
- `user_data.json` - Sample data for testing

### Expected output

A complete Python script that can be executed and produces the same functional output as the original, but with significantly improved code quality.

---

## prompts/prompt_2_yaml_json.md

## Prompt 2: Error Explanation and Multi-Format Conversion

## Instructions for AI model

The original `process_records.py` script will fail when trying to load `config.yaml`.

### Task 1: Explain the errors

Pinpoint the exact lines and reasons why the `yaml.load()` call will raise errors based on the content of `config.yaml`. Be specific about:

- Indentation issues
- Structural problems  
- Type inconsistencies

### Task 2: Correct the YAML

Provide a fully corrected version of `config.yaml` that resolves all parsing issues while preserving the intended data structure.

### Task 3: Convert to JSON

Convert the corrected YAML content into a properly formatted JSON object. Ensure all data types (booleans, numbers, strings) are represented correctly in the JSON output.

### Context files

- `config.yaml` - The broken configuration file
- `process_records.py` - Shows how the config is used

### Expected outputs

1. **Fixed YAML file** - Valid syntax, proper indentation, correct types
2. **JSON conversion** - Equivalent data structure with proper JSON types

---

## prompts/prompt_3_transformation.md

## Prompt 3: Large File Reasoning and Bulk Transformation

## Instructions for AI model

Using knowledge from the previous prompts, write a new data transformation function.

### Task: Create transform function

Write a Python function called `transform_and_enrich_users(user_list)` that takes the list of user dictionaries from `user_data.json` and performs these operations:

#### 1. Standardize IDs

Ensure every user `id` is an integer.

#### 2. Graceful error handling  

The function must not crash. If a user record is missing a required key for an operation (e.g., `contact` or `email`), skip that specific transformation for that user and log a warning if possible.

#### 3. Enrich data

Add a new key `email_provider` to the `contact` dictionary. The value should be the domain part of the email address (e.g., for `jane.d@example.com`, the provider is `example.com`).

#### 4. Complex conditional logic

Add a new top-level key `account_tier` with this logic:

- If `total_posts > 100` AND `total_comments > 300`: tier is "Gold"
- If `total_posts > 50`: tier is "Silver"  
- Otherwise: tier is "Bronze"

#### 5. Type correction

Ensure the `age` value in the `stats` dictionary is always an integer.

### Context files

- `user_data.json` - The data to transform
- Previous solutions for context

### Expected output

A complete Python function that returns the list of fully transformed and enriched user records, with robust error handling.

---

## prompts/prompt_4_api_simulation.md

## Prompt 4: API Interaction Simulation

## Instructions for AI model

The business wants to synchronize processed user data with an external CRM system via REST API.

### Task: Create API sync function

Write a complete, standalone Python function `sync_users_to_crm(user_data, api_token)` that simulates this process.

#### Requirements

**Target Endpoint**: `https://api.crm-system.com/v2/users/sync`

**HTTP Method**: POST

**Headers**:

- `Content-Type: application/json`
- `Authorization: Bearer <api_token>`

**Payload**: JSON object with single key `users` containing the user records list

**Error Handling**: Use the `requests` library with comprehensive handling for:

- Network problems (`requests.exceptions.ConnectionError`)
- HTTP status codes:
  - `401 Unauthorized` (invalid token)
  - `400 Bad Request` (bad data)  
  - `503 Service Unavailable`
  - Generic handling for other 4xx/5xx errors
- Print informative error messages for each case

**Success Case**: If successful (status 200/202), parse JSON response and return the `job_id` value.

### Expected output

A production-ready function with robust error handling that could be used in a real application.
