---
title: Documentation Validation Tools
description: Deep usage guide for validate_docs.py including command classification, execution safety, and CI integration.
search:
	boost: 0.6
---

## Documentation Validation Tools

> Consolidated reference docs live in [`docs/developer-guide.md`](../developer-guide.md) and [`docs/architecture.md`](../architecture.md). This README provides deep usage details for validation helper scripts (primarily `validate_docs.py`).

This directory contains tools for validating the accuracy and cross-platform compatibility of documentation in the AIBugBench project.

## validate_docs.py

A comprehensive validation script that automatically tests all documented commands across the AIBugBench project to ensure they work correctly on different platforms.

### Features

- **Automatic Command Detection**: Scans all documentation files for command blocks
- **Platform-Specific Execution**: Runs commands appropriate for the current platform (Windows CMD, PowerShell, macOS/Linux)
- **Safety First**: Classifies commands by safety level and skips destructive operations
- **Sandboxed Execution**: Runs potentially file-modifying commands in isolated temporary directories
- **Output Validation**: Compares actual command output with documented expected results
- **Comprehensive Reporting**: Generates detailed reports with success/failure breakdown
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

### Command Classification

Commands are automatically classified into these safety levels:

- **SAFE**: Read-only commands (ls, dir, echo, python --version)
- **SANDBOX**: File-modifying commands that can be safely isolated (mkdir, cp, python scripts/bootstrap_repo.py)
- **NETWORK**: Commands that access network resources (git clone, curl, wget)
- **DESTRUCTIVE**: Potentially dangerous commands (rm -rf, format, shutdown) - skipped by default

### Usage

#### Basic Usage

**List documentation commands (no execution):**

```bash
python scripts/validate_docs.py --list
```

**Scan only (alias legacy flag names):**

```bash
python scripts/validate_docs.py --docs-only
python scripts/validate_docs.py --dry-run
```

**Validate all safe commands:**

```bash
python scripts/validate_docs.py
```

**Run with detailed output:**

```bash
python scripts/validate_docs.py --verbose
```

#### Advanced Options

**Include potentially destructive commands (use with extreme caution):**

```bash
python scripts/validate_docs.py --no-skip-destructive
```

**Save validation report to file:**

```bash
python scripts/validate_docs.py --output validation_report.txt
```

**Specify custom project root:**

```bash
python scripts/validate_docs.py --project-root /path/to/aibugbench
```

**Emit JSON summary (machine readable):**

```bash
python scripts/validate_docs.py --json --output report.txt --json-file report.json
```

#### Command Line Options

- `--verbose, -v`: Enable detailed logging output
- `--list`: List commands (caps at 50 for brevity) without execution
- `--docs-only`: Only scan for commands, don't execute them
- `--dry-run`: Alias for `--docs-only` (kept for familiarity)
- `--skip-destructive`: Skip potentially destructive commands (default: True)
- `--no-skip-destructive`: Run destructive commands (use with caution)
- `--output, -o`: Save validation report to specified file
- `--project-root`: Specify project root directory (auto-detected by default)
- `--json`: Emit JSON summary to stdout
- `--json-file`: Write JSON summary to a file (implies `--json`)

### Example Output

...existing code...

### Security Considerations

### Incremental Refactor Note

Core parsing logic is being migrated into an importable package under `validation/` (`validation.docs_core`). The script remains a thin CLI wrapper and will shrink over time as execution/reporting are modularized. External usage should import from `validation` for unit tests instead of invoking the script directly.

The validation script includes several safety measures:

1. **Destructive Command Detection**: Automatically identifies and skips dangerous commands
2. **Sandboxed Execution**: File-modifying commands run in temporary, isolated directories
3. **Timeout Protection**: Commands are terminated after 30 seconds to prevent hangs
4. **Path Validation**: Prevents execution outside of safe directories
5. **Tool Requirements**: Verifies required tools are available before execution

**Important**: Never run the validation script with `--no-skip-destructive` on production systems or systems containing important data. Always test in isolated environments first.
