# Contributing to AIBugBench

Thank you for your interest in contributing to AIBugBench! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.13+
- Git

### Local Development

1. **Clone the repository** (when public):

   ```bash
   git clone https://github.com/sMiNT0S/AIBugBench.git
   cd AIBugBench
   ```

2. **Set up virtual environment**:

   ```bash
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # Unix/Linux/macOS
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies (hash-verified)**:

   ```bash
   pip install --upgrade pip
   # Install runtime dependencies (direct pins; prefer lock for reproducibility)
   pip install --require-hashes -r requirements.lock
   # (Optional) install dev tooling (linters, test utilities, security scanners)
   pip install --require-hashes -r requirements-dev.lock
   ```

4. **Set up pre-commit hooks (recommended)**:

   ```bash
   pip install pre-commit
   pre-commit install
   ```

   This will run automated checks (linting, type checking, smoke tests) before each commit.

### Running Tests and Linting

Before submitting any changes, ensure your code passes all checks:

```bash
# Run linting
ruff check .

# Run tests
pytest -q

# Run repository audit (enhanced)
python validation/repo_audit_enhanced.py --path . --json audit_report.json
```

### Development Workflow

The project uses extensive CI automation and pre-commit hooks:

- **Pre-commit hooks**: Run linting, type checking, and smoke tests before commits
- **CI Pipeline**: Comprehensive validation including security scans, multi-platform tests, and coverage analysis
- **Dependency locks**: Hash-verified requirements for reproducible builds

If pre-commit hooks are installed, they will automatically:

- Run Ruff for code formatting and linting
- Execute MyPy type checking on core modules
- Run Bandit security analysis
- Validate YAML formatting
- Execute smoke tests to ensure basic functionality
- Check requirements.lock / requirements-dev.lock sync (drift fails commit)

## Pull Request Process

1. **Fork the repository** and create a feature branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** and linting is clean
6. **Submit a pull request** with a clear description of changes

### PR Requirements

- [ ] Tests pass (`pytest -q`)
- [ ] Linting passes (`ruff check .`)
- [ ] Repository audit passes
- [ ] Clear commit messages
- [ ] Updated documentation (if applicable)

## Coding Standards & Dependency Policy

- **Python Style**: Follow PEP 8, enforced by Ruff
- **Line Length**: 100 characters maximum
- **Imports**: One import per line, sorted (Ruff governs ordering)
- **Documentation**: Add docstrings for public functions and classes
- **Testing**: Write tests for new features and bug fixes
- **Dependency Policy**:
      - Direct runtime deps are hard-pinned in `pyproject.toml` / `requirements.txt` and lock hashed in `requirements.lock`.
      - Dev/tooling deps live in `requirements-dev.txt` with hashed lock in `requirements-dev.lock`.
      - When adding/removing a direct runtime dependency: update both manifests, regenerate lock (`python scripts/update_requirements_lock.py`), and add a CHANGELOG entry.
      - Do not broaden version ranges without prior discussion (determinism priority during early lifecycle).

## Issue Reporting

- Use the provided issue templates
- Search existing issues before creating new ones
- Provide clear reproduction steps for bugs
- Include relevant system information (Python version, OS, etc.)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## Questions?

Feel free to open an issue for questions about contributing or contact the maintainer at <175650907+sMiNT0S@users.noreply.github.com>.
