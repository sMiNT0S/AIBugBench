---
title: Submissions (Maintainer Notes)
description: Maintainer-focused notes on tiered submission discovery and expectations. User-facing instructions live in Getting Started and Developer Guide.
search:
	boost: 0.8
---

## Audience

Maintainers. For user-facing guidance, see:

- [Getting Started](../getting-started.md)
- [Developer Guide](../developer-guide.md)
- Template README: `submissions/templates/template/README.md`

## Tiered Submission Layout (Reference)

submissions/
├── reference_implementations/   # Verified reference solutions
├── user_submissions/            # User-provided solutions
└── templates/                   # Starting templates
    └── template/

## Discovery Rules

1. Prefer `reference_implementations/` over `user_submissions/` when both contain the same model name (abort on ambiguity).
2. `templates/` is never executed; it seeds new user submissions only.
3. Legacy flat layout is unsupported; validators abort with a clear message and migration guidance.

## Maintainer Notes

- Ensure required filenames remain stable (prompt_1_solution.py, prompt_2_config_fixed.yaml/json, prompt_3_transform.py, prompt_4_api_sync.py).
- If discovery logic changes, update the migration messages and Developer Guide concurrently.
- Keep example/reference models minimal and deterministic; no network or import-time side effects.
