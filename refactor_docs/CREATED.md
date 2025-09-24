# Phase-0 and Phase-1 Files Created; Phase-2 Reports from line 62 onwards

This document is generated automatically by the scaffold script.  It lists
all brand-new files added in Phase 0 and confirms that the new package is
importable.

## Phase-0 and Phase-1

```text
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

```python
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

```bash
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

## Phase 2.5 Completion Report

> Approach

- Extended BenchmarkRunner to surface concurrency/retry configuration and added resumable checkpoint support per ADR.
- Implemented run_many workflow with locking, backoff, jitter, and telemetry hooks, reusing atomic writes for idempotence.
- Added targeted tests covering checkpoint skips, retry/backoff behaviour, and exhausted retry budgets alongside updated contract checks, then ran focused pytest suite.

  Result

- Introduced RunStatus, RunResult, RetriableError, and a configurable run_many pipeline with retry/backoff, checkpointing, and locking in aibugbench/orchestration/
  runner.py:32,174,295,516, keeping run_once deterministic and checkpoint-aware.
- Updated the runner contract test to account for checkpoint writes in tests/test_runner_contract.py:64-75.
- Added resilience tests for skip/resume, deterministic backoff, and exhausted retries in tests/test_runner_resilience.py:27-168.

  Next

- Optional: integrate CLI wiring for run_many once Phase 3 validators land, ensuring concurrency env knobs are documented.

  CHECKLIST

- added functions/classes: RunStatus, RunResult, RetriableError, BenchmarkRunner.run_many, BenchmarkRunner._execute_with_retries, BenchmarkRunner._compute_backoff
- pytest: pytest tests/test_cli_snapshot.py tests/test_runner_contract.py tests/test_runner_writes_atomically.py tests/test_runner_resilience.py

## PHASE 3 (IN PROGRESS)

### Phase 3.A — Design memo only

```markdown
> Approach

  - Review Phase 3.A requirements and prior runner/validator contracts.
  - Summarize schema, scoring, legacy-mapping, analyzers, error taxonomy, and test plan in Markdown.
  - Present memo plus required checklist, then issue the mandated pause signal.

  Result

  # PHASE3A Design Memo

  ## 1 · Validator Contracts (Preserve)

  - Validator.analyze(run_dir: str) -> dict[str, object] returns a JSON-serialisable analysis payload; no side effects beyond local artifacts produced through runner-provided FS helpers.
  - Validator.score(analysis: dict[str, object]) -> float consumes exactly the dict emitted by analyze and returns a float in [0.0, 1.0].
  - Runner/CLI behaviour—including CLI flags, exit codes, and the SUMMARY: JSON line—remains unchanged; only analysis internals evolve.

  ## 2 · Analysis Schema v1

  - Top-level keys: checks, stats, artifacts, with optional namespaced extras allowed (prefixed, e.g. legacy_*).
  - checks: list of dicts each containing
      - id: str ({domain}.{slug}, e.g. sec.aws_key_found).
      - ok: bool (True when the check passes).
      - severity: Literal["info","warn","error"] (closed enum).
      - message: str (human-readable, ≤160 chars, ASCII-safe).
  - stats: dict[str, int | float]; numeric metrics only, deterministic units; no nested dicts.
  - artifacts: dict[str, str]; keys are stable identifiers (e.g. report, evidence), values are POSIX-style relative paths under the prompt’s artifact directory.

  ## 3 · Scoring Rule

  - Baseline pass-rate:

    total = len(checks) or 1
    passed = sum(1 for c in checks if c["ok"])
    score = clamp(passed / total, 0.0, 1.0)
  - No weighting in Phase 3.A; rounding (if needed) deferred to presentation layer (runner keeps raw float).

  ## 4 · Legacy → v1 Mapping

  - analysis["issues"] (legacy list of findings) → normalised into checks with id = issue["name"], ok = not issue["failed"], severity from legacy severity/level, message = issue["detail"].
  - analysis["metrics"] / analysis["stats"] → copied into stats (coerce numerics, drop non-numeric values).
  - analysis["artifact_paths"] / analysis["artifacts"] → relocated to artifacts with paths rewritten relative to the prompt’s artifact root.
  - Legacy booleans such as analysis["passed"] → re-derived from pass-rate (score == 1.0); stored under optional legacy_passed if consumers still need it.
  - Free-form notes (analysis["notes"], analysis["warnings"]) → map to checks entries (severity="warn"/"info") to avoid extra top-level keys.

  ## 5 · Prompt 1 Analyzer Plan

  - aibugbench.validation.analyzers.security.run(run_dir: str) -> tuple[list[dict], dict[str, int]]
    Inputs: prompt run directory. Outputs: security checks (credential regex hits, policy config presence) and stats (files scanned, matches). Pure filesystem reads.
  - ...maintainability.run(run_dir: str) -> tuple[list[dict], dict[str, int | float]]
    Inputs: run directory. Outputs: lint-style checks (line length, file count thresholds) and stats (python_file_count, avg_line_length).
  - ...performance.run(run_dir: str) -> tuple[list[dict], dict[str, int | float]]
    Inputs: run directory. Outputs: performance-signal checks (asset size caps, resource hints) and stats (total_bytes, largest_file_bytes).
  - Prompt1Validator.analyze merges analyzer outputs, flattens checks, merges stats with namespace-safe prefixes if collisions, and populates artifacts when analyzers emit report files
  (e.g. security findings JSON via runner FS).

  ## 6 · Error Taxonomy Usage

  - SchemaError: raised when is_valid_analysis_v1(analysis) returns (False, errors) or when analyzers emit incompatible types (e.g. non-serialisable data); runner treats as non-retriable
  failure.
  - RetriableError: raised by analyzers/validator when encountering transient conditions (temporary IO failure, sandbox race); runner retry/backoff handles it per existing Phase 2.5 logic.
  - Other exceptions are propagated and logged as non-retriable (runner marks status failed).

  ## 7 · Test Plan

  - tests/test_validator_p1_contract.py: instantiate Prompt1Validator, assert schema validity (checks fields present, severities legal), score bounds, monotonicity when flipping ok.
  - tests/test_validator_p1_golden.py: snapshot stable projections (sorted check tuples, stats dict, rounded score) against curated fixture repo.
  - tests/test_validator_errors.py: verify invalid schema triggers SchemaError; simulate transient analyzer failure raising RetriableError and ensure runner retries when integrated.
  - tests/test_validator_factory.py: assert factory.make_validator("p1", env) returns Prompt1Validator, unknown prompt falls back to LegacyValidatorAdapter.
  - Existing runner contract/resilience tests continue to cover integration; extend as needed to assert SchemaError propagates without retry.

  CHECKLIST

  - Locked validator contracts (analyze/score) + CLI invariants.
  - Defined canonical schema keys and severity enum.
  - Selected pass-rate scoring and legacy field normalisation strategy.
  - Identified Prompt 1 analyzers, inputs/outputs, and error taxonomy triggers.
  - Committed test matrix covering contract, golden, factory, and error paths.
  ```

Next
Await CONTINUE 3.B instruction.

PAUSE: PHASE 3.A COMPLETE

=========================================================

## Phase 3.B — Scaffolding drop (skeleton code only)

> Approach

- Scaffolded validation subpackages (analyzers, impl) with typed placeholders per Phase 3.B.
- Added error taxonomy, schema constants, factory stub, and analyzer/validator skeletons that raise NotImplementedError.
- Introduced strict xfail tests covering analyzers and Prompt 1 validator to keep CI stable pending implementation.

  Result
  CHECKLIST

- aibugbench/validation/analyzers/init.py
- aibugbench/validation/analyzers/security.py
- aibugbench/validation/analyzers/maintainability.py
- aibugbench/validation/analyzers/performance.py
- aibugbench/validation/impl/init.py
- aibugbench/validation/impl/prompt1.py
- aibugbench/validation/errors.py
- aibugbench/validation/factory.py
- aibugbench/validation/schema.py
- tests/test_validator_phase3_skeleton.py
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests
    PAUSE: PHASE 3.B COMPLETE
