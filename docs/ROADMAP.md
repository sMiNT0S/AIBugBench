# Roadmap

Status: Beta (v0.8.0 spec_version)

## Near-Term (Stabilization)

- Execution sandbox (basic restricted subprocess wrapper; enforce time/resource limits)
- Introduce unified run_cmd helper wrapping subprocess.run (allow‑listed binaries, enforced timeouts, consistent logging); then annotate existing imports with rationale to silence low‑severity Bandit noise instead of broad skips
- Coverage gating in CI (existing script integration)
- Results metadata completeness (already inject spec_version, commit, env)

### Type Hygiene (Incremental Mypy Tightening)

Tracked from first stricter mypy run (Stage 1). Aim: reduce lenient config over stages.

Action buckets:

- Missing returns / unreachable code:
  - scripts/validate_security.py: add explicit return
  - benchmark/validators.py: resolve unreachable blocks (lines ~239, 377) & prune dead code
  - scripts/validate_docs.py: unreachable at ~437
  - validation/repo_audit_enhanced.py: unreachable at ~464
- Library stub installation:
  - Install: types-requests, types-PyYAML (or add minimal inline Protocols if avoiding deps)
- Over‑broad Any propagation:
  - Remove unused type: ignore comments (validation/repo_audit_enhanced.py lines 45,49,157; scripts/validate_docs.py line 43; tests/test_runner.py line 325)
  - Replace return Any with concrete types in repo_audit_enhanced.py (function returning dict[str, Any]) and example_model prompts
- Mis-typed sentinel objects causing attr-defined errors ("object" has no attribute append/get):
  - benchmark/validators.py: multiple list-like accumulators initialized as object -> initialize as list[str] / list[Any]
  - scripts/validate_docs.py: attributes .get on generic object -> refine types for command metadata dicts
  - validation/repo_audit_enhanced.py: .append/.update targets -> correct initial types
- Argument type mismatches:
  - run_benchmark.py: datetime.UTC vs Python version compatibility (fallback to timezone.utc for <3.11)
  - ScoringDetail.add_check call: ensure correct (str, bool, float) argument types
  - UnicodeEncodeError construction in tests (argument order/types)
- Return contract corrections:
  - prompt_4_api_sync.py: ensure declared return type matches code paths
  - prompt_3_transform.py / prompt_1_solution.py (example_model) return specific collection types
- Config evolution plan:
  - Stage 2: enable strict_optional & remove allow_untyped_globals
  - Stage 3: drop allow_untyped_defs; prune disable_error_code list further
  - Stage 4: evaluate full `strict = true`

Success Metrics:

- Stub installs reduce import-untyped errors to zero
- attr-defined errors < 5 within two passes
- No unreachable code errors
- Unused ignores trend to 0

Optional Tooling:

- Add `mypy --warn-unused-ignores --warn-redundant-casts` to CI once attr-defined clean.

## Deferred (Implement When Adoption Justifies)

- Fuzz & mutation tests for docs/yaml parsers
- Concurrency / load stress harness
- SBOM + provenance attestation (CycloneDX, optional signing)
- Statistical variance runs (repeat benchmark N times -> stability metrics)
- Performance regression thresholds (wall clock + memory)
- Plugin / extension API formalization

## Long-Term

- Sandboxed multi-language execution adapters
- Distributed run orchestrator
- Cached artifact layer & incremental scoring
- Attestation + supply chain SLSA level improvements

## Principles

- Prioritize scoring correctness over peripheral tooling
- Ship minimal safe defaults; document limitations clearly
- Add complexity only when it directly improves benchmark fidelity or user clarity
