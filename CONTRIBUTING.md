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

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install ruff pytest
   ```

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

## Coding Standards

- **Python Style**: Follow PEP 8, enforced by Ruff
- **Line Length**: 100 characters maximum
- **Imports**: One import per line, sorted alphabetically
- **Documentation**: Add docstrings for public functions and classes
- **Testing**: Write tests for new features and bug fixes

## Issue Reporting

- Use the provided issue templates
- Search existing issues before creating new ones
- Provide clear reproduction steps for bugs
- Include relevant system information (Python version, OS, etc.)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## Questions?

Feel free to open an issue for questions about contributing or contact the maintainer at <175650907+sMiNT0S@users.noreply.github.com>.
