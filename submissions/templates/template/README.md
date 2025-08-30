---
title: Model Submission Template
description: Instructions for replacing template prompt files with full AI-generated solutions for benchmarking.
search:
    boost: 0.5
---

## Model Submission Template (Canonical Location)

This is the canonical template location at `submissions/templates/template/`.
Legacy single-level paths are not supported; the project standardizes solely on this tiered path.

> For broader context on submission workflows see [`docs/developer-guide.md`](../../../../docs/developer-guide.md) and scoring in [`docs/scoring-methodology.md`](../../../../docs/scoring-methodology.md). This README only describes how to replace each prompt file.

Copy this template directory and rename it to your model name (e.g., `gpt4`, `claude_sonnet_4`, `copilot`).

## How to Use This Template

Each template file should be completely replaced with your AI's full solution. Do NOT append inside the placeholder, overwrite the file.

### Files to Replace with AI Solutions

1. `prompt_1_solution.py` – Full refactored version of `process_records.py`
2. `prompt_2_config_fixed.yaml` – Corrected YAML version of `config.yaml`
3. `prompt_2_config.json` – JSON conversion of the corrected config
4. `prompt_3_transform.py` – Implementation of `transform_and_enrich_users`
5. `prompt_4_api_sync.py` – Implementation of `sync_users_to_crm`

### Workflow

1. Copy template: create `submissions/user_submissions/your_model_name/`
2. Get AI solutions: have your AI solve each prompt fully
3. Replace files: overwrite each template file entirely
4. Test: run the benchmark to view scores

## Testing Your Submission

```bash
python run_benchmark.py --model your_model_name
```

## Scoring

Each prompt uses a comprehensive 7‑category scoring system (25 points total): Syntax, Structure, Execution, Quality, Security, Performance, Maintainability.

Passing threshold: 60% (15+ points per prompt).

The benchmark outputs detailed category feedback with rationale for improvements.

> See [`docs/scoring-methodology.md`](../../../../docs/scoring-methodology.md) for the full rubric.

Good luck!
