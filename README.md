# AIBugBench

[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sMiNT0S.github.io/AIBugBench/)
[![CI](https://github.com/sMiNT0S/AIBugBench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sMiNT0S/AIBugBench/actions/workflows/ci.yml)
[![codecov trend](https://codecov.io/github/smint0s/aibugbench/graph/badge.svg?token=0G9SHU4AZ7)](https://codecov.io/github/smint0s/aibugbench)
![safety](https://img.shields.io/endpoint?url=https://smint0s.github.io/AIBugBench/badges/safety.json)

📚 **[Complete Documentation](https://sMiNT0S.github.io/AIBugBench/)** | [Getting Started](https://sMiNT0S.github.io/AIBugBench/getting-started/) | [Security](https://sMiNT0S.github.io/AIBugBench/security/)

---

## What is AIBugBench?

Compare AI models on the **same four tasks**. Score across **seven dimensions**. Local, sandboxed, deterministic. No vibes—just receipts.

Perfect for choosing between models, catching regressions, and understanding how LLMs handle messy code under controlled conditions.

**What you get:**

- Fixed prompts + deterministic fixtures = comparable results across models and runs
- Seven-dimension scorecard: correctness, safety, readability, efficiency, robustness, portability, maintainability
- Sandboxed local execution (no cloud dependencies, no network calls by default)
- Results you can diff, track, and reproduce

**Not included:**

- Whole-codebase scanning (it's a benchmark, not a production tool)
- Magic prompt tuning for your app
- Security blessing for arbitrary code

Use AIBugBench to compare models and monitor behavior over time, not to validate production systems.

---

## Quick Start (60 seconds)

![Quick start demo (clone → venv → install → benchmark → results)](media/quickstart.gif)

### Prerequisites

- Python 3.13+
- Git

### Installation & First Run

**Windows PowerShell:**

```powershell
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.lock
python run_benchmark.py --model example_model
```

**macOS/Linux Bash:**

```bash
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.lock
python run_benchmark.py --model example_model
```

Expected result: ~90/100 (A grade) in under a minute.

![Benchmark run and scorecard summary](media/summary.png)

---

## Prompt 2 Format Analyzers

- Prompt 2 now runs on the modular validator stack introduced in Phase 3, reusing the shared format analyzers (YAML, JSON, structure, cross-format, quality) and schema-v1 scoring helpers. The new `Prompt2Validator` emits the same check IDs and scoring breakdowns as the legacy implementation but is easier to test and extend.
- A legacy golden snapshot (`tests/fixtures/prompt2/legacy_analysis.json`) guards parity: contract tests compare the new validator against the original monolithic analysis to ensure no regressions slip in.
- Need to bisect or roll back? Set `USE_LEGACY_PROMPT2=true` before invoking `run_benchmark.py` and the factory will route Prompt 2 back through the archived adapter. Example (PowerShell): ``$env:USE_LEGACY_PROMPT2="true"; python run_benchmark.py --model example_model``. Unset or clear the variable to return to the modular path.

---

## Documentation

📚 **[Complete Documentation](https://sMiNT0S.github.io/AIBugBench/)** - Full guides, API reference, and examples

**Quick Links:**

- 🚀 [Getting Started](https://sMiNT0S.github.io/AIBugBench/getting-started/) - Setup and first benchmark
- 📖 [User Guide](https://sMiNT0S.github.io/AIBugBench/user-guide/) - Running benchmarks and interpreting results
- 👨‍💻 [Developer Guide](https://sMiNT0S.github.io/AIBugBench/developer-guide/) - Adding and testing AI models
- 🔒 [Security](https://sMiNT0S.github.io/AIBugBench/security/) - Sandbox architecture and threat model
- 🏗️ [Architecture](https://sMiNT0S.github.io/AIBugBench/architecture/) - Technical design and components
- 📊 [Scoring Methodology](https://sMiNT0S.github.io/AIBugBench/scoring-methodology/) - How models are evaluated
- 🔧 [Troubleshooting](https://sMiNT0S.github.io/AIBugBench/troubleshooting/) - Common issues and solutions
- 🤝 [Contributing](https://sMiNT0S.github.io/AIBugBench/contributing/) - Development and contribution guide

---

## Requirements & License

**Requirements:** Python 3.13+ • pyyaml>=6.0 • requests>=2.25.0
**License:** [Apache-2.0](LICENSE)
