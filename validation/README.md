---
title: Validation Package Internals
description: Internal modules supporting documentation validation, security checks, and repository audits in AIBugBench.
search:
    boost: 0.4
---

## Validation Package

**Internal validation utilities for AIBugBench quality assurance and compliance.**

> Overview documentation lives in the consolidated site under [`docs/architecture.md`](../docs/architecture.md) and [`docs/developer-guide.md`](../docs/developer-guide.md). This README focuses on the internal APIs surfaced by the validation package.

The `validation/` package contains refactored core validation logic extracted from legacy scripts in `scripts/` to enable unit testing and modular imports. CLI wrappers remain in `scripts/` for backwards compatibility.

## Architecture
<!-- markdownlint-disable MD050 -->
validation/
├── __init__.py          # Package exports and public API
├── docs_core.py         # Documentation validation primitives
├── security_core.py     # Security validation helpers
└── repo_audit_enhanced.py  # Enhanced repository audit implementation
<!-- markdownlint-enable MD050 -->
## Core Modules

### `docs_core.py`

**Purpose**: Lightweight parser for extracting and classifying commands from documentation files.

**Key Components**:

- `DocumentationValidator`: Command extraction and classification engine
- `Platform` enum: Windows CMD, PowerShell, macOS/Linux support
- `CommandType` enum: SAFE, SANDBOX, DESTRUCTIVE, NETWORK classification
- `Command` dataclass: Structured command representation

**Usage**:

```python
from validation.docs_core import DocumentationValidator, Platform

validator = DocumentationValidator(Path("."))
commands = validator.extract_commands_from_text(markdown_content, file_path)
```

**Pattern Recognition**:

- Multi-platform code block detection (`bash`, `cmd`, `powershell`, etc.)
- Command continuation handling (backslash support)
- Comment filtering and descriptive text exclusion
- Tool-based pattern matching (python, git, pytest, etc.)

### `security_core.py`

**Purpose**: Security validation functions for compliance and vulnerability scanning.

**Available Checks**:

- `check_security_files()`: Validates security configuration file presence
- `run_ruff_security_check()`: Executes Ruff security linting (S-class rules)
- `run_safety_check()`: Dependency vulnerability scanning via Safety
- `check_git_history_safety()`: Git commit message secret scanning
- `validate_test_data_safety()`: Test data API key pattern detection

**Integration Example**:

```python
from validation.security_core import SECURITY_CHECKS

for check_name, check_func in SECURITY_CHECKS.items():
    passed, issues = check_func()
    print(f"{check_name}: {'PASS' if passed else 'FAIL'} ({issues} issues)")
```

**Security Patterns**:

Conservative, high‑signal secret regexes (OpenAI, AWS, Anthropic, etc.) are centrally maintained in `validation.security_core.SECRET_PATTERNS`. This avoids stale copies in docs and reduces false positives. See the source for authoritative patterns and rationale. The README intentionally omits full regex listings to encourage a single source of truth.

### `repo_audit_enhanced.py`

**Purpose**: Comprehensive repository audit implementation (single source of truth).

**Notes**:

- Former root-level script removed pre-0.8.0-beta; invoke via `python -m validation.repo_audit_enhanced` or direct path.
- Provides scoring, secret scanning, static heuristics, CI inspection, and structured JSON output.

## CLI Integration

### Documentation Validation

```bash
# Full validation with JSON output
python scripts/validate_docs.py --json

# Platform-specific testing
python scripts/validate_docs.py --platform windows_cmd

# Network-safe validation
python scripts/validate_docs.py --skip-destructive --no-network
```

**Command Categories**:

- **SAFE**: Standard commands (python, git status, ls)
- **SANDBOX**: Isolated test commands (pytest, setup operations)
- **DESTRUCTIVE**: File modification commands (mkdir, rm, edit)
- **NETWORK**: External dependency commands (pip install, curl)

### Repository Audit

```bash
# Complete repository assessment
python validation/repo_audit_enhanced.py --json audit_report.json

# Strict mode with threshold enforcement
python validation/repo_audit_enhanced.py --strict --min-score 85
```

## AIBugBench Integration

### Quality Assurance Workflow

The validation package supports AIBugBench's comprehensive quality pipeline:

1. **Documentation Integrity**: Ensures all documented commands execute correctly
2. **Security Compliance**: Validates multi-layer security scanning setup
3. **Repository Readiness**: Assesses production-ready state (91/100 A-grade target)

### Testing Integration

```python
# Unit test support
from validation.docs_core import DocumentationValidator
from validation.security_core import validate_test_data_safety

# Test command extraction
validator = DocumentationValidator(project_root)
commands = validator.extract_commands_from_text(test_content, test_file)

# Test security validation
safe, incidents = validate_test_data_safety()
assert safe, f"Security incidents detected: {incidents}"
```

### Development Workflow

- **Pre-commit**: Security checks prevent credential commits
- **CI/CD**: Automated validation in GitHub Actions
- **Release**: Comprehensive audit before version tagging

## Configuration

### Environment Variables

- `AIBB_TIMEOUT=25`: External tool timeout in seconds

### Security File Requirements

The security validator expects these files for full compliance:

- `.github/dependabot.yml`
- `.github/workflows/security.yml`
- `.github/codeql/codeql-config.yml`
- `.trufflehogignore`
- `.semgrepignore`
- `.safety-project.ini`
- `.github/secret-patterns.yml`

## Migration Status

**Current State**: Incremental refactor from monolithic scripts to modular package.

**Legacy Compatibility**: CLI scripts maintain full backwards compatibility during transition.

**Future State**: Complete validation logic migration to enable:

- Comprehensive unit test coverage
- Modular validation component reuse
- Enhanced error reporting and debugging
- Plugin-based validation extension

---

For CLI usage examples and full validation workflow documentation, see `scripts/README.md` and the main project documentation.
