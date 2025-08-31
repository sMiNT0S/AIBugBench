# Reference Implementation: `example_model`

Canonical, production-quality solutions for the benchmark prompts. These files define the
expected structure, coding style, and behavior that all other (template or user) submissions
are measured against.

## What This Contains

- `prompt_1_solution.py` – Refactored processing logic (clean, logged, type-aware)
- `prompt_2_config_fixed.yaml` / `prompt_2_config.json` – Corrected configuration pair
- `prompt_3_transform.py` – Deterministic data transformation & enrichment
- `prompt_4_api_sync.py` – Robust API sync example (error/status handling)

## Guarantees

- Passes full lint & security scans (no blanket `# noqa`)
- Import-safe (no side effects at import time beyond definitions)
- Deterministic: no network calls except where explicitly simulated under guarded code
- Serves as the scoring and comparison baseline

## How To Run Against This Model

Run only this model:

```bash
python run_benchmark.py --model example_model
```

Run all discovered models (reference + any user submissions):

```bash
python run_benchmark.py
```

Compare multiple models (example against others):

```bash
python scripts/compare_benchmarks.py --models example_model your_model
```

## Relationship To Other Tiers

Templates live in `submissions/templates/` (starter copies). User/AI generated implementations
belong in `submissions/user_submissions/`. This directory is intentionally tracked and strictly
validated; user submissions are excluded from automated gating.

## See Also

- Developer guide (Tiered Submission System section)
- Scoring methodology: `docs/scoring-methodology.md`

Keep changes here minimal, intentional, and fully reviewed — this is the benchmark truth source.
