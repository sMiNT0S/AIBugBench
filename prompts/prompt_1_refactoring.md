# Benchmark Prompts

## Present these prompts to the AI one by one, after providing/uploading the context of the three test files (config.yaml, process_records.py, user_data.json)

Prompt 1: Code Understanding and Refactoring 🧐

## Fairness note

• Expect non-strict inputs (minor format deviations, mixed encodings, platform-specific paths).
• Normalize types and handle missing/variant fields gracefully.  
• Avoid network access; keep solutions deterministic and testable.

Analyze the provided Python script, process_records.py.

Identify Problems: List and explain at least five distinct problems with the script. Cover issues related to style (PEP 8), efficiency, error handling, and logical correctness.

Refactor the Code: Provide a complete, refactored version of the script. The new script should be modular, efficient, robust (e.g., handle potential FileNotFoundError or KeyError), and adhere to modern Python best practices. Consider scalability for larger datasets and maintainable code structure.

## Evaluation Interface Contract (for benchmarking)

To ensure your refactored script can be executed and scored deterministically by the benchmark, keep this IO/CLI contract:

- Invocation: The script must accept a positional configuration path argument.
  - Example: `python process_records.py <config.yaml>`
  - If omitted, default to `config.yaml` in the working directory.
- Data selection: Treat `use_legacy_paths` as a top‑level boolean in the YAML; when `true`, prefer `paths.legacy_data_source` (commonly `./user_data.json`). Be tolerant of string booleans ("true"/"false").
- Output: Print to stdout a JSON array of processed records. You may precede it with a line like `Processed Records:`; the JSON must still be parseable from stdout.

These requirements keep the evaluation consistent while leaving implementation details (structure, helpers, logging to stderr, etc.) up to you.
