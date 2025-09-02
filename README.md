# AIBugBench

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sMiNT0S.github.io/AIBugBench/)

## Welcome to AIBugBench

So... you decided to vibe-code a weekend project, and now your personal API key is public. How tragic. Next time, run it here first.

AIBugBench is a comprehensive benchmark for testing AI-generated code across 7 quality categories. Because trusting AI with your codebase should come with receipts.

### What This Does

- **Benchmark AI Models:** Test how well LLMs write secure, correct, and maintainable code
- **Catch Security Issues:** Find API key leaks, SQL injections, and other oopsies before production
- **Regression Testing:** Ensure your fine-tuned model didn't forget how to code
- **Compare Models:** Side-by-side scoring to pick the least dangerous option
- **Validate Improvements:** Prove your prompt engineering actually works

## Quick Start (60 seconds)

```bash
git clone https://github.com/sMiNT0S/AIBugBench.git && cd AIBugBench
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt && python setup.py
python run_benchmark.py --model example_model
```

## Navigation

**First-Time Users:** [Getting Started Guide](docs/getting-started.md) - Setup and run your first benchmark  
**Regular Users:** [User Guide](docs/user-guide.md) - Run benchmarks and interpret results  
**Model Developers:** [Developer Guide](docs/developer-guide.md) - Add and test AI models  
**Contributors:** [Architecture](docs/architecture.md) & [Contributing](CONTRIBUTING.md) - Understand and extend the codebase  

## FAQ

**How do I run tests quickly?**  
`python -m pytest -q` (fast logic run, no coverage)

**How do I get full coverage locally?**  
`pwsh scripts/test_with_coverage.ps1` (erases old data, runs with thresholds)

**Why was coverage removed from default pytest.ini?**  
To avoid branch/statement mixing errors and speed up iteration; CI & the coverage script enforce thresholds.

**How do I rebuild a clean environment?**  
`Remove-Item -Recurse -Force venv; python -m venv venv; ./venv/Scripts/Activate.ps1; pip install -r requirements.txt -r requirements-dev.txt`

**How do I prevent accidental empty files?**  
Copy `scripts/pre_commit_template.sh` to `.git/hooks/pre-commit` and make it executable.

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

**Requirements:** Python 3.10+ • pyyaml>=6.0 • requests>=2.25.0 | **License:** [MIT](LICENSE)

## Scope & Limitations

This beta focuses on deterministic scoring accuracy and reproducible results. It does NOT sandbox untrusted submission code yet—run only trusted code. Advanced isolation, fuzz stress, and provenance (SBOM/signing) are deferred and tracked in the roadmap.

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
