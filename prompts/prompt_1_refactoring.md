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
