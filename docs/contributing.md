# Contributing

This guide explains how to set up development, run checks, and contribute changes.

## Development Setup

### Prerequisites

- Python 3.13+
- Git
- Code editor with EditorConfig support recommended

### Initial Setup

1. **Clone and create environment:**

   ```bash
   git clone https://github.com/sMiNT0S/AIBugBench.git
   cd AIBugBench
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   # Runtime dependencies
   pip install --require-hashes -r requirements.lock

   # Development tooling
   pip install --require-hashes -r requirements-dev.lock
   ```

3. **Install pre-commit hooks:**

   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Generate test data:**

   ```bash
   python scripts/bootstrap_repo.py
   ```

## Running Tests and Linting

Quick validation before committing:

```bash
# Fast test run
pytest -q

# Linting
ruff check .
ruff format --check .

# Type checking (strict core modules)
mypy benchmark validation run_benchmark.py --no-error-summary
```

## Development Command Reference

Quick reference for common development and maintenance tasks:

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
| Pre-commit hooks | `pip install pre-commit && pre-commit install` |

**Notes:**

- Coverage thresholds are enforced in CI; local full runs are optional unless changing scoring or sandbox logic.
- Always use lock files for reproducible installs; `requirements.txt` lists only direct top-level dependencies.

## Development Workflow

1. **Create feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following coding standards below

3. **Run validation:**

   ```bash
   pytest -q
   ruff check .
   mypy benchmark validation run_benchmark.py
   ```

4. **Commit changes:**

   ```bash
   git add .
   git commit -m "feat: descriptive message"
   ```

5. **Push and create PR:**

   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

- Follow PEP 8 style (enforced by Ruff)
- Use type hints for public APIs
- Write docstrings for modules, classes, and functions
- Keep functions focused and under 20 lines when possible
- Add tests for new functionality
- Update documentation for user-facing changes

## Dependency Management Policy

### Overview

Locked runtime dependencies live in `requirements.lock` (hashes enforced in PR security workflow). Developer tooling (linters, type checkers, test utilities, security scanners) is separately pinned in `requirements-dev.lock` to decouple supply-chain drift from runtime evaluation.

**Weekly Automation**: A scheduled workflow (`scheduled-dep-refresh.yml`) recompiles both locks every Monday (UTC) and opens/updates a PR if changes occur. This keeps security patches visible while preserving review control.

### Policy (Early Project Phase)

- **Direct runtime dependencies** are hard-pinned (exact versions) in BOTH `pyproject.toml` and `requirements.txt` for maximum reproducibility
- **Transitive graph** is captured with hashes in `requirements.lock` (single source of truth for `--require-hashes` installations)
- `requirements.txt` intentionally remains minimal (only direct deps) to reduce merge noise and aid review
- **Addition/removal** of a direct dependency requires: update `pyproject.toml`, update `requirements.txt`, regenerate `requirements.lock`, and update CHANGELOG
- **Ranges** will be reconsidered only after first external adopter milestone (avoids untested drift)

**Rationale**: Benchmarks and performance regression tests rely on environmental determinism (timings, resource usage). Pin churn is explicit and auditable; accidental minor version bumps cannot silently alter scoring baselines.

### Runtime Dependencies Update Flow

1. Edit `requirements.txt` (minimal, top-level direct deps only)
2. Regenerate lock (same Python major/minor):

   ```bash
   pip install "pip-tools>=7.5.0"
   python -m piptools compile --generate-hashes -o requirements.lock requirements.txt
   ```

3. Install with verification: `pip install --require-hashes -r requirements.lock`
4. Commit both files together
5. Update CHANGELOG with dependency change rationale

**CI Enforcement**: The `lock-verification` job recompiles when `requirements.txt` changes and fails if `requirements.lock` is out of sync.

### Developer Tooling Dependencies

Flow mirrors the runtime lock but sources `requirements-dev.txt`:

1. Edit `requirements-dev.txt` (add/remove tools — keep only necessary dev/test/security utilities)
2. Rebuild lock (same interpreter version):

   ```bash
   pip install "pip-tools>=7.5.0"
   python -m piptools compile --generate-hashes -o requirements-dev.lock requirements-dev.txt
   ```

3. Install with hashes: `pip install --require-hashes -r requirements-dev.lock`
4. Commit both `requirements-dev.txt` and `requirements-dev.lock` together

**Rationale**: Keeps transient tooling bumps from invalidating benchmark reproducibility. Allows security scanners/linters to update independently of runtime dependency graph. Hardened installs (hashes) even for local CI parity.

## Issue Reporting

When reporting issues, please include:

- AIBugBench version (commit hash or release tag)
- Python version
- Operating system
- Steps to reproduce
- Expected vs. actual behavior
- Relevant error messages or logs

Use GitHub's issue templates when available.

## Pull Request Guidelines

- Keep PRs focused on a single concern
- Update tests for functionality changes
- Update documentation for user-facing changes
- Ensure CI passes before requesting review
- Reference related issues in PR description
- Follow conventional commit format in PR title

## Adding New Prompts

To contribute new benchmark challenges:

1. Create prompt file in `prompts/` directory
2. Add validation logic in `benchmark/validators.py`
3. Update scoring weights in `benchmark/scoring.py`
4. Add tests in `tests/`
5. Document in `docs/scoring-methodology.md`

See existing prompts for structure and style.

## Documentation Contributions

Documentation is built with MkDocs Material. To preview locally:

```bash
pip install -r requirements-dev.lock
mkdocs serve
```

Visit `http://127.0.0.1:8000` to preview changes.

## Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors. Please review [Code of Conduct](code-of-conduct.md) before participating.

## License

By contributing to AIBugBench, you agree that your contributions will be licensed under the Apache-2.0 License.

## Getting Help

- Check existing [GitHub issues](https://github.com/sMiNT0S/AIBugBench/issues)
- Review [documentation](https://sMiNT0S.github.io/AIBugBench/)
- Ask questions in GitHub Discussions (if enabled)

## Recognition

Contributors are recognized in:

- Git commit history
- Release notes (for significant contributions)
- Project README (for major features)

Thank you for helping make AIBugBench better!
