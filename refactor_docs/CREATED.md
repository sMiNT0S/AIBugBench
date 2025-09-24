# Phase-0 and Phase-1 Files Created

This document is generated automatically by the scaffold script.  It lists
all brand-new files added in Phase 0 and confirms that the new package is
importable.

```
aibugbench/
  __init__.py
  io/__init__.py
  io/fs.py
  io/paths.py
  config/__init__.py
  config/env.py
  config/artifacts.py
  orchestration/__init__.py
  orchestration/runner.py
  run_benchmark.py
  validation/__init__.py
  validation/base.py
  validation/adapters/__init__.py
  validation/adapters/legacy_validator.py

 tests/
  conftest.py (pre-existing)
  fixtures/golden_summary.json
  test_cli_snapshot.py
  test_artifact_precedence.py
  test_fs_helpers.py
  test_validation_contract.py
  test_runner_contract.py
```

## Importability check

```
python - <<'PY'
import importlib, json, sys
mods = [
    "aibugbench",
    "aibugbench.io.fs",
    "aibugbench.io.paths",
    "aibugbench.config.artifacts",
    "aibugbench.orchestration.runner",
    "aibugbench.validation.base",
    "aibugbench.validation.adapters.legacy_validator",
]
print(json.dumps({m: bool(importlib.import_module(m)) for m in mods}, indent=2))
PY
```

## Run seam tests only

```
pytest -q tests/test_cli_snapshot.py \
       tests/test_artifact_precedence.py \
       tests/test_fs_helpers.py \
       tests/test_validation_contract.py \
       tests/test_runner_contract.py
```
