# AIBugBench

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sMiNT0S.github.io/AIBugBench/)
[![CI](https://github.com/sMiNT0S/AIBugBench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sMiNT0S/AIBugBench/actions/workflows/ci.yml)
[![Security Analysis](https://github.com/sMiNT0S/AIBugBench/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/sMiNT0S/AIBugBench/actions/workflows/security.yml)
[![Tiered Validation](https://github.com/sMiNT0S/AIBugBench/actions/workflows/tiered-validation.yml/badge.svg?branch=main)](https://github.com/sMiNT0S/AIBugBench/actions/workflows/tiered-validation.yml)
![Type Checking](https://img.shields.io/badge/mypy-strict--core%20clean-brightgreen)

## Welcome to AIBugBench - note; on the slight offchance this repo gains some attention when i'm away for vacation, repo is read only for now after silent public switch

So… you vibe coded a weekend project and shipped it. Bold move. Before you crown an LLM your new teammate, see how it behaves under **the same** set of tasks.

AIBugBench evaluates AI-generated code on four **prewritten prompts** and fixed test fixtures. You paste the model’s output, it runs **locally** in a sandbox, and you get a scorecard across seven quality dimensions. Comparable, repeatable, receipts—not vibes.

### What this is

- **Model behavior benchmark:** How different LLMs handle the *same* four curated prompts + deterministic fixtures under controlled conditions.
- **Regression detector:** Track model versions / prompt policies over time and catch “it used to work” moments (baseline vs new output diffs).
- **Safety lens:** Static + dynamic sandbox guardrails (dangerous imports, subprocess, network, filesystem). Runtime canaries verify those controls each run (they validate the sandbox, not the scoring logic).
- **Apples-to-apples:** Fixed prompts + fixed harness = comparable results across models and runs (scoring stable across versions).
- **Seven-dimension scorecard:** Correctness, safety, readability, efficiency, robustness, portability, maintainability.

### What this is *not*

- A scanner/tester for your whole codebase  
- A magic prompt tuner for your app  
- Proof your production is “secure”  
(It’s a benchmark. Use it to compare and monitor models, not to bless arbitrary code.)

### How It Works (TL;DR)

1. Pick your model(s) of choice, e.g. GPT5 Thinking 'vs' Opus 4.1, see how they compare over the same tasks.  
2. Run the **four provided prompts** after providing deliberately malformed/fussy test data.  
3. Paste the outputs into AIBugBench.  
4. It executes locally in a guarded sandbox and scores the results.  
5. You get a readable scorecard + artifacts for diffs and regressions.

Run it to choose saner defaults, catch regressions early, and keep your future “oops, API key” moments in the hypothetical.

## Quick Start (60 seconds)

```bash
git clone https://github.com/sMiNT0S/AIBugBench.git && cd AIBugBench
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
# Install pinned, hash‑verified runtime deps
pip install --require-hashes -r requirements.lock
# (Optional) developer tooling (hash‑verified)
pip install --require-hashes -r requirements-dev.lock
# If you just modified dev deps and need to refresh the lock:
# pip install -r requirements-dev.txt && python scripts/update_requirements_lock.py
python run_benchmark.py --model example_model
```

## Table of Contents

<!-- TOC_START -->

- [Welcome to AIBugBench](#welcome-to-aibugbench)
  - [What this is](#what-this-is)
  - [What this is *not*](#what-this-is-not)
  - [How It Works (TL;DR)](#how-it-works-tldr)
- [Quick Start (60 seconds)](#quick-start-60-seconds)
- [Security at a glance](#security-at-a-glance)
- [Navigation](#navigation)
- [Common Tasks](#common-tasks)
  - [Notes](#notes)
- [Resources](#resources)
- [Dependency Locks (pip-tools)](#dependency-locks-pip-tools)
  - [Developer Tooling Lock](#developer-tooling-lock)
- [Scope & Limitations](#scope--limitations)
- [Result Metadata & Privacy](#result-metadata--privacy)
- [Performance & Concurrency](#performance--concurrency)
- [Results Layout (v0.8.1+)](#results-layout-v081)
- [Badge Meanings & Local Reproduction](#badge-meanings--local-reproduction)
<!-- TOC_END -->

## Security at a glance

- Execution isolation via `SecureRunner` sandbox (temp working dir, cleanup on exit)
- Runtime guards: block **eval/exec/compile**, **subprocess**, **dangerous imports** (`ctypes`, `pickle`, `marshal`, etc.)
- Network egress blocked by default (socket overrides); explicit opt-in flags: `--allow-network` / `--unsafe`
- Filesystem mediation: guarded open/remove/copy + path validation (temp scope)
- Resource limits: POSIX rlimits (CPU / memory / file size); Windows Job Objects when pywin32 present (soft timeout-only fallback if unavailable)
- Environment scrubbing: sensitive pattern filtering + controlled rebuild (full whitelist hardening deferred)
- Dynamic canaries (CPU loop, network, subprocess, spawn, dynamic code, dangerous imports, filesystem) validate static heuristics each audit run
- Mandatory security audit (`scripts/security_audit.py`) integrated in CI; produces JSON artifact and pass/fail gating
- Explicit failure isolation: banner honesty check ensures claims match enforced controls
- Opt-out: `--unsafe` (loudly logged + reduces guardrails for comparative analysis only)

Full threat model & roadmap: see [`SAFETY.md`](SAFETY.md) and [`SECURITY.md`](SECURITY.md).

## Navigation

**First-Time Users:** [Getting Started Guide](docs/getting-started.md) - Setup and run your first benchmark  
**Regular Users:** [User Guide](docs/user-guide.md) - Run benchmarks and interpret results  
**Model Developers:** [Developer Guide](docs/developer-guide.md) - Add and test AI models  
**Contributors:** [Architecture](docs/architecture.md) & [Contributing](CONTRIBUTING.md) - Understand and extend the codebase  

## Common Tasks

| Task | Command / Action |
|------|------------------|
| Fast test run | `pytest -q` |
| Full coverage run | `pwsh scripts/test_with_coverage.ps1` |
| Type checking (strict core) | `mypy benchmark validation run_benchmark.py --no-error-summary` |
| Lint & format check | `ruff check . && ruff format --check .` |
| Security audit (local) | `python scripts/security_audit.py --json` |
| Dependency lock update | `python scripts/update_requirements_lock.py` |
| Rebuild clean venv (Windows) | `Remove-Item -Recurse -Force venv; python -m venv venv; ./venv/Scripts/Activate.ps1` |
| Install deps (prod) | `pip install --require-hashes -r requirements.lock` |
| Install dev tooling | `pip install --require-hashes -r requirements-dev.lock` |
| Add model (example) | Copy `submissions/reference_implementations/example_model` → new folder & adapt |
| Pre-commit hooks | `pip install pre-commit && pre-commit install` (uses `.pre-commit-config.yaml`) |

### Notes

- Coverage thresholds enforced in CI; local full run is optional unless changing scoring / sandbox.
- Use the lock file for reproducible installs; `requirements.txt` lists only direct top-level deps.

## Resources

**Documentation:** [Full documentation site](https://sMiNT0S.github.io/AIBugBench/)  
**Troubleshooting:** [Common issues and solutions](docs/troubleshooting.md)  
**Scoring:** [Detailed scoring methodology](docs/scoring-methodology.md)  
**API Reference:** [CLI and Python API](docs/api-reference.md)  
**Validation Tools:** See `validation/README.md` for internal doc/security/audit utilities (advanced)  
**Submissions Guide:** See `submissions/README.md` for model folder layout & workflow (developer)  
**Template Usage:** See `submissions/templates/template/README.md` for per‑prompt file replacement instructions  
**Doc Command Validator:** See `scripts/README.md` for `validate_docs.py` usage & CI integration  

---

**Requirements:** Python 3.13+ • pyyaml>=6.0 • requests>=2.25.0 | **License:** [MIT](LICENSE)

## Dependency Locks (pip-tools)

Locked runtime deps live in `requirements.lock` (hashes enforced in PR security workflow). Developer tooling (linters, type checkers, test utilities, security scanners) is separately pinned in `requirements-dev.lock` to decouple supply‑chain drift from runtime evaluation.

Update flow:

1. Edit `requirements.txt` (minimal, top-level direct deps only).
2. Regenerate lock (same Python major/minor):

   ```bash
   pip install "pip-tools>=7.5.0"
   python -m piptools compile --generate-hashes -o requirements.lock requirements.txt
   ```

3. Install with verification: `pip install --require-hashes -r requirements.lock`
4. Commit both files together.

CI enforcement: the `lock-verification` job recompiles when `requirements.txt` changes and fails if `requirements.lock` is out of sync.

### Developer Tooling Lock

Flow mirrors the runtime lock but sources `requirements-dev.txt`:

1. Edit `requirements-dev.txt` (add/remove tools — keep only necessary dev/test/security utilities).
2. Rebuild lock (same interpreter version):

   ```bash
   pip install "pip-tools>=7.5.0"
   python -m piptools compile --generate-hashes -o requirements-dev.lock requirements-dev.txt
   ```

3. Install with hashes: `pip install --require-hashes -r requirements-dev.lock`
4. Commit both `requirements-dev.txt` and `requirements-dev.lock` together.

Rationale:

- Keeps transient tooling bumps from invalidating benchmark reproducibility
- Allows security scanners / linters to update independently of runtime dependency graph
- Hardened installs (hashes) even for local CI parity.

## Scope & Limitations

Current release scope (0.x beta):

Implemented:

- Deterministic scoring & comparison output (timestamped results directories)
- Sandbox enforcement (process isolation helpers, filesystem guard, dynamic canaries)
- Resource limits (POSIX rlimits; Windows Job Objects when pywin32 available)
- Dynamic code / subprocess / dangerous import blocking
- Python-level network egress blocking (socket denial unless `--allow-network`)
- Strict environment whitelist (minimal allow-list rebuild of env)
- Hash-pinned dependency supply-chain integrity
- Security + dependency audit workflows

Deferred (tracked in ROADMAP):

- Container / namespace isolation (bwrap / nsjail / docker) for defense-in-depth
- OS / kernel-level network isolation (firewall / namespaces) beyond Python socket guards
- SBOM + artifact signing
- Automated PR-tier sandbox fuzz stress harness
- Optional Semgrep ruleset integration
- Public CodeQL adoption (post public repo / GHAS availability)

Out of Scope (near-term):

- Multi-language model execution
- GPU / accelerator resource accounting
- Distributed execution orchestration

## Result Metadata & Privacy

Benchmark results embed minimal provenance metadata to aid reproducibility:

- spec_version: Benchmark scoring spec revision
- git_commit: Short commit hash of the repository state (local only)
- python_version: Interpreter version used to run the benchmark
- platform: OS / release / architecture string
- timestamp_utc: UTC run time (RFC 3339, Z suffix)
- dependency_fingerprint: First 16 hex chars of SHA256 of `requirements.txt` (non-reversible drift indicator)

No personal data is collected or transmitted; data is written only to local `results/` JSON & text files. If you publish results, you may reveal commit hashes or platform details.

Opt-out:

- CLI flag: `--no-metadata` (retains only `spec_version`)
- Environment variable: `AIBUGBENCH_DISABLE_METADATA=1`

Either mechanism suppresses git/platform/timestamp/dependency fingerprint fields. Use when sharing results from private repositories or sensitive environments.

## Performance & Concurrency

Run multiple models concurrently with the thread pool executor:

```bash
python run_benchmark.py --workers 4
```

Set `--workers` to the number of concurrent model evaluations you want (1 = sequential, default). The output remains deterministic per model; ordering of completion messages may vary.

## Results Layout (v0.8.1+)

Each run now writes to a timestamped directory preserving history:

```text
results/
 latest_results.json                # Backward-compatible pointer to most recent run
 20250827_143215/                   # Run-specific directory (YYYYMMDD_HHMMSS)
  latest_results.json              # Full JSON (models + comparison + _metadata)
  detailed/
   detailed_results.json          # Stable path for tooling
   summary_report_20250827_143215.txt
  comparison_charts/
   comparison_chart.txt           # ASCII comparison bars
```

Key advantages: atomic writes (no partial files), historical retention, dynamic prompt support (new prompts auto appear in comparison data).

## Badge Meanings & Local Reproduction

| Badge | Meaning | How to Reproduce Locally |
|-------|---------|--------------------------|
| CI | Lint (ruff) + tests (pytest) pass | `pytest -q` then `ruff check .` |
| Test Coverage | Coverage job in `ci.yml` meets threshold (>=62% default) | `pwsh scripts/test_with_coverage.ps1` |
| Security Audit | Fast static/config audit (`security-audit.yml`) passes | (auto in workflow) |
| Security Analysis | Full security suite (`security.yml`: bandit, secrets, pins) passes | `bandit -r . -ll` (plus internal scripts) |
| Tiered Validation | Structural & doc validators succeed | (workflow: `tiered-validation.yml`) |
| Type Checking | Core modules mypy-clean under strict-core profile | `mypy benchmark run_benchmark.py` |
