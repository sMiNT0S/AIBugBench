# AIBugBench

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sMiNT0S.github.io/AIBugBench/)

Comprehensive AI code generation benchmark with 7-category quality assessment.

## Quick Start (60 seconds)

```bash
git clone https://github.com/sMiNT0S/AIBugBench.git && cd AIBugBench
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt && python setup.py
python run_benchmark.py --model example_model
```

## Navigation

**🚀 First-Time Users:** [Getting Started Guide](docs/getting-started.md) - Setup and run your first benchmark  
**📊 Regular Users:** [User Guide](docs/user-guide.md) - Run benchmarks and interpret results  
**👨‍💻 Model Developers:** [Developer Guide](docs/developer-guide.md) - Add and test AI models  
**🏗️ Contributors:** [Architecture](docs/architecture.md) & [Contributing](CONTRIBUTING.md) - Understand and extend the codebase  

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

**📖 Documentation:** [Full documentation site](https://sMiNT0S.github.io/AIBugBench/)  
**🔧 Troubleshooting:** [Common issues and solutions](docs/troubleshooting.md)  
**📈 Scoring:** [Detailed scoring methodology](docs/scoring-methodology.md)  
**🔍 API Reference:** [CLI and Python API](docs/api-reference.md)  
**🧪 Validation Tools:** See `validation/README.md` for internal doc/security/audit utilities (advanced)  
**📤 Submissions Guide:** See `submissions/README.md` for model folder layout & workflow (developer)  
**📦 Template Usage:** See `submissions/template/README.md` for per‑prompt file replacement instructions  
**🛠️ Doc Command Validator:** See `scripts/README.md` for `validate_docs.py` usage & CI integration  

---

**Requirements:** Python 3.10+ • pyyaml>=6.0 • requests>=2.25.0 | **License:** [MIT](LICENSE)
