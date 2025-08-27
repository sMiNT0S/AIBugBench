# Prompt 3: Deterministic Single-File Transformer (Import-Safe)

Provide ONE Python file (`prompt_3_transform.py`) that defines the required transformation function and (optionally) a demo block. The benchmark will import your module and call the function directly; stdout from the demo block is ignored for scoring.

## Fairness note

* Deterministic: No randomness, no network/file writes.
* Import-safe: No side effects (no prints / top-level execution) on import.
* UTF-8 / UTF-8-SIG: Input JSON may include a BOM; no need to support comments or trailing commas.
* Stdlib only: No third-party dependencies.

## Required Function

Define exactly:

```python
def transform_and_enrich_users(user_list):
    ...
```

It must return a list the same length as the input (the benchmark supplies a Python list in memory).

### Per-Record Requirements

1. IDs to int where coercible (leave as-is if conversion fails gracefully).
2. Add contact.email_provider: domain portion after '@' if `contact.email` present and parseable.
3. Account tier rules:
   * Gold: total_posts > 100 AND total_comments > 300
   * Silver: total_posts > 50 (when Gold not met)
   * Else Bronze
4. stats.age -> int where coercible (leave untouched if not parsable).
5. Graceful handling: Skip only the failing sub-transform; never raise for missing keys / malformed records.

### Error Handling

Avoid crashing. Optionally emit warnings to stderr in the demo block (not required).

## Optional Demo Block (Human Run Only)

Under a main guard you may load `user_data.json`, invoke the function, and print minified JSON. This does not affect scoring.

### Standard Loader Template (Optional – You May Use Verbatim)

```python
import json, sys
from pathlib import Path

__all__ = ["transform_and_enrich_users"]

def transform_and_enrich_users(user_list):
    # Implement: IDs->int, email_provider, account_tier, stats.age->int, graceful skips
    return user_list

if __name__ == "__main__":
    with open(Path("user_data.json"), "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    result = transform_and_enrich_users(data)
    json.dump(result, sys.stdout, separators=(",", ":"))
```

## What NOT To Do

* No network / API calls
* No global prints at import
* No mutation of global state outside the function (other than pure helpers)

## Scoring Alignment (Informational)

The benchmark checks: function existence & signature, ID standardization, email provider extraction, age normalization, account tier correctness, graceful handling of a malformed record, and basic quality/maintainability heuristics. This prompt simply makes those expectations explicit.

Deliver exactly one file; do not zip or split into packages.
