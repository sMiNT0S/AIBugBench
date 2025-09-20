---
title: Documentation Validation Tools
description: Deep usage guide for validate_docs.py including command classification, execution safety, and CI integration.
search:
  boost: 0.6
---
## Documentation Validation Tools

> Consolidated reference docs live in [`docs/developer-guide.md`](../docs/developer-guide.md) and [`docs/architecture.md`](../docs/architecture.md). This README provides deep usage details for validation helper scripts (primarily `validate_docs.py`).

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

### Platform Attribution (neutral bucket)

Fenced code blocks labeled as bash/sh/shell are attributed to the macOS/Linux platform for parsing.
However, many such commands are OS-neutral (for example: `python`, `pip`, `pytest`, `uv`, `git`).
To avoid skewing the platform breakdown, the validator separates these into a pseudo platform named
"neutral" and reduces the macOS/Linux count by that neutral subset. This split is reflected in both
the console summary and the JSON output under `platform_counts`.

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

AIBugBench Documentation Validator
Project root: C:\Users\username\AIBugBench
Platform: Windows

Scanning documentation files for commands...
Found 142 commands across 7 files

Command breakdown:
Platforms:
  windows_cmd: 42
  windows_powershell: 41
  macos_linux: 59
Types:
  network: 9
  safe: 76
  sandbox: 57

Validating commands...
(Skipping destructive commands for safety)

### AIBugBench Documentation Validation Report (Sample)

#### SUMMARY

Total Commands:     142
Successful:         128
Failed:             8
Skipped:            6
Success Rate:       90.1%

#### PLATFORM BREAKDOWN

windows_cmd             42 commands
windows_powershell      0 commands (platform mismatch)
neutral                 18 commands
macos_linux             41 commands

#### COMMAND TYPE BREAKDOWN

safe                    76 commands
sandbox                 57 commands
network                 9 commands

#### FAILED COMMANDS

File: README.md
Line: 85
Command: xcopy /E /I submissions\template submissions\your_model_name
Platform: windows_cmd
Error: Command failed with return code 1: Invalid path

#### SKIPPED COMMANDS

Reason: Platform mismatch: windows_powershell vs windows_cmd (41 commands)
Reason: Required tool not available: git (9 commands)

#### RECOMMENDATIONS

• Review and fix failed commands in documentation
• Ensure all documented commands work as expected
• Successfully validated commands can be trusted

Validation completed at: 2025-08-19 23:56:15

```text

### Integration with CI/CD

The validation script returns appropriate exit codes for integration with automated workflows:

- **Exit 0**: All commands passed validation
- **Exit 1**: One or more commands failed validation

Example GitHub Actions workflow:

```yaml
name: Validate Documentation
on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Validate documentation commands
      run: python scripts/validate_docs.py --verbose --output validation-${{ matrix.os }}.txt --json --json-file validation-${{ matrix.os }}.json
    
    - name: Upload validation report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: validation-reports
        path: validation-*.txt
```

### Customization

#### Adding New Documentation Files

To validate commands in additional documentation files, modify the `doc_files` list in the `DocumentationValidator` class:

```python
self.doc_files = [
    "README.md",
    "QUICKSTART.md",
    "EXAMPLE_SUBMISSION.md",
    "docs/adding_models.md",
    "docs/interpreting_results.md",
    "docs/scoring_rubric.md",
  "submissions/templates/template/README.md",
    "your_new_file.md",  # Add your file here
]
```

#### Adding New Command Patterns

To recognize additional command block formats, extend the `command_patterns` dictionary:

```python
self.command_patterns = {
    Platform.WINDOWS_CMD: [
        (r'```cmd\s*\n(.*?)\n```', re.DOTALL),
        (r'```batch\s*\n(.*?)\n```', re.DOTALL),
        (r'```your_format\s*\n(.*?)\n```', re.DOTALL),  # Add new format
    ],
    # ... other platforms
}
```

#### Custom Safety Classifications

To modify how commands are classified for safety, edit the patterns in the `_classify_command` method:

```python
# Add new destructive patterns
destructive_patterns = [
    r'\brm\s+-rf\s+/',
    r'\bdel\s+/s\s+/q',
    r'\byour_dangerous_command\s+',  # Add new pattern
]
```

### Troubleshooting

#### Common Issues

#### **"No commands found in documentation files"**

- Check that documentation files exist in the expected locations
- Verify command blocks use the correct markdown format (```cmd,```bash, etc.)

#### **"Required tool not available: python"**

- Ensure Python is installed and available in the system PATH
- Try specifying the full path to Python in your documentation

#### **"Command failed with return code 1"**

- Check that file paths in commands are correct
- Ensure required files and directories exist
- Verify commands work when run manually

#### **High number of skipped commands**

- This is normal on single-platform systems (Windows commands skip on Linux, etc.)
- Use `--verbose` to see detailed skip reasons

#### Debug Mode

For detailed debugging information:

```bash
python scripts/validate_docs.py --verbose --docs-only
```

This will show:

- Exactly which commands were extracted from each file
- Why specific commands were skipped or failed
- Detailed execution logs for troubleshooting

## Other Utility Scripts

### yaml_ducttape.ps1

A PowerShell script that scans the repository for yamllint errors and warnings, then applies safe automatic fixes.

**Features:**

- Scans entire repository for YAML formatting issues
- Applies safe fixes automatically (indentation, spacing, line endings)
- Lists optional fixes that require manual review
- Preserves file content and structure integrity

**Usage:**

```powershell
./yaml_ducttape.ps1
```

### update_requirements_lock.py

Utility script that detects differences between requirements files and their locked versions.

**Features:**

- Compares `requirements.txt` vs `requirements.lock`
- Compares `requirements-dev.txt` vs `requirements-dev.lock`
- Reports version mismatches and missing dependencies
- Helps maintain dependency synchronization

**Usage:**

```bash
python scripts/update_requirements_lock.py
```

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
