# Prompt 2 legacy analysis fixture

Captured from the legacy monolithic validator (`benchmark.validators.validate_prompt_2_yaml_json`)
using the reference model `submissions/reference_implementations/example_model`.

Regeneration steps (requires a revision where the monolith still exists):

```powershell
python scripts/capture_prompt2_legacy_fixture.py
```

The script loads `LEGACY_validators.py`, executes the monolithic Prompt 2 validator, and writes
the raw legacy output (score, detailed scoring, tests_passed) to this fixture. The golden test
compares the modular validator's score, per-category breakdown, and derived `tests_passed` flags
to ensure behavioural parity. Do **not** regenerate this fixture with the refactored
`Prompt2Validator`; its purpose is to preserve the legacy baseline for regression checks.
