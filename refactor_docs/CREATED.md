# Phase-0 and Phase-1 Files Created; Phase-2 In Progress - see bottom of this doc

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

=========================================================

## Phase-2A Completion Report

  Goal

> Approach

- Implemented BenchmarkRunner with injected validator/env/fs, artifact resolution via choose_artifact_path, and atomic write handling for non–dry runs.
- Rewired CLI to build the runner dependencies, delegate execution, and keep the SUMMARY line compatible with existing snapshots.
- Validated the updated CLI flow with the snapshot test.

  Result

- aibugbench/orchestration/runner.py#L26 now provides a concrete BenchmarkRunner that supports dry-run short-circuiting, validator delegation, and atomic persistence of analysis/summary
  artifacts.
- aibugbench/run_benchmark.py#L19 instantiates the runner using LegacyValidatorAdapter, forwards CLI options (including --dry-run), and emits the unchanged SUMMARY payload while
  optionally listing created artifacts for real runs.
- Tests: pytest tests/test_cli_snapshot.py.

  Next

- Consider enabling the remaining Phase‑2 tests once the contract assertions are updated.

  CHECKLIST

- changed files: aibugbench/orchestration/runner.py; aibugbench/run_benchmark.py
- functions implemented: BenchmarkRunner.run_once; CLI main wiring
- pytest: pytest tests/test_cli_snapshot.py

## Phase 2B Completion Report

> Approach

- Replaced the contract xfail with a real assertion suite using stubbed validator/FS to capture runner effects.
- Added an integration-style atomic write check leveraging the shared filesystem helper.
- Ran the targeted runner test modules.

  Result

- tests/test_runner_contract.py:1 now instantiates BenchmarkRunner with injected doubles, asserting summary shape, score propagation, artifact paths, and recorded atomic-write calls.
- tests/test_runner_writes_atomically.py:1 exercises the runner against aibugbench.io.fs, verifying JSON artifacts exist and no .tmp remnants remain post-run.

  Next

- None; ready for further Phase 2 tasks.

  pytest command: pytest tests/test_runner_contract.py tests/test_runner_writes_atomically.py
  fixtures/mocks: uses pytest tmp_path; custom stubs defined inline.
