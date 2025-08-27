# AIBugBench Troubleshooting Guide

> For AI/LLM generated code that is tested and produces errors, also consult the "Troubleshooting Guide" section inside the [Sabotage Notes](sabotage-notes.md) for hazard-specific remediation patterns.

This guide covers common issues encountered when working with AIBugBench and provides step-by-step solutions.

## Common Issues and Solutions

### Tiered Structure Errors (New Layout)

This section covers the three primary error/failure modes introduced with the enforced tiered submissions layout.

| Scenario | Symptom / Message | Meaning | Action |
|----------|-------------------|---------|--------|
| Missing submissions dir | `ERROR: Submissions directory 'submissions' not found!` (summary line absent) | Root submissions directory isn't present | Run `python setup.py` or create `submissions/` then re-run |
| Empty tiered structure | `Discovered models: reference=0 user=0 templates=OK` followed later by `No models found in submissions directory` | Layout exists but no models present | Copy template to new model: `cp -r submissions/templates/template submissions/user_submissions/my_model` then implement files |
| Template missing | `Discovered models: reference=X user=Y templates=MISSING` | Required `submissions/templates/template/` not found | Recreate template: `python -c "from benchmark.utils import create_submission_template; import pathlib; create_submission_template(pathlib.Path('submissions'))"` |
| Legacy layout detected | Process aborts with SystemExit: message starts `Legacy submissions layout detected (e.g. submissions/example_model).` | Old flat layout present without new tiers (no fallback) | Migrate: create `reference_implementations/`, `templates/template/`, `user_submissions/`; move old `example_model/` into `reference_implementations/` |

Quick Migration Commands (Unix-like shells):

```bash
mkdir -p submissions/{reference_implementations,templates,user_submissions}
mv submissions/example_model submissions/reference_implementations/
mkdir -p submissions/templates/template
python - <<'PY'
from benchmark.utils import create_submission_template; from pathlib import Path; create_submission_template(Path('submissions'))
PY
```

PowerShell equivalent:

```powershell
New-Item -ItemType Directory -Force submissions/reference_implementations,submissions/templates/template,submissions/user_submissions | Out-Null
Move-Item submissions/example_model submissions/reference_implementations/ -Force
python - <<'PY'
from benchmark.utils import create_submission_template; from pathlib import Path; create_submission_template(Path('submissions'))
PY
```

Verification:

```bash
python run_benchmark.py --submissions-dir submissions --model example_model || true
```

Expected discovery line after migration (with at least example_model in reference implementations):

```text
Discovered models: reference=1 user=0 templates=OK
```

### 1. Benchmark Execution Failures

#### Issue: "No module named 'benchmark'"

**Symptoms:**

ModuleNotFoundError: No module named 'benchmark'

**Solution:**

```bash
# Ensure you're in the project root
cd AIBugBench
# Verify the benchmark directory exists
ls -la benchmark/
# Re-run with proper Python path
python run_benchmark.py --model example_model
```

**Command to verify fix:**

```bash
python -c "import benchmark; print('OK')"
```

#### Issue: "FileNotFoundError: test_data directory not found"

**Symptoms:**

FileNotFoundError: [Errno 2] No such file or directory: 'test_data/config.yaml'

**Solution:**

```bash
# Run setup to create test data
python setup.py
# Verify test data exists
ls -la test_data/
```

**Command to verify fix:**

```bash
python -c "import os; print('OK' if os.path.exists('test_data/config.yaml') else 'FAIL')"
```

### 2. Validation Tool Failures

#### Issue: "scripts/validate_docs.py fails with platform mismatch"

**Symptoms:**

Platform mismatch: macos_linux vs windows_cmd

**Solution:**

```bash
# Windows users should run with platform override
python scripts/validate_docs.py --platform windows_cmd --docs-only
# Or use PowerShell variant
python scripts/validate_docs.py --platform windows_powershell --docs-only
```

**Command to verify fix:**

```bash
python scripts/validate_docs.py --docs-only --verbose
```

#### Issue: "validate_security.py fails with exit code 127"

**Symptoms:**

Command failed with return code 127
bandit: command not found

**Solution:**

```bash
# Install dev dependencies
pip install -r requirements-dev.txt
# Verify bandit is installed
bandit --version
# Re-run security validation
python scripts/validate_security.py
```

**Command to verify fix:**

```bash
python scripts/validate_security.py --dry-run
```

### 3. Testing Issues

#### Issue: "pytest command not found"

**Symptoms:**

'pytest' is not recognized as an internal or external command

**Solution:**

```bash
# Install pytest via pip
pip install pytest pytest-cov
# Or install dev dependencies
pip install -r requirements-dev.txt
# Re-run tests
pytest tests/ -v
```

**Command to verify fix:**

```bash
pytest --version
```

#### Issue: "Tests fail with import errors"

**Symptoms:**

ImportError: cannot import name 'validators' from 'benchmark'

**Solution:**

```bash
# Ensure you're in project root
cd AIBugBench
# Add project to Python path and run
PYTHONPATH=. pytest tests/ -v
# Or use the Python module flag
python -m pytest tests/ -v
```

**Command to verify fix:**

```bash
python -c "from benchmark import validators; print('OK')"
```

### 4. Submission Issues

#### Issue: "Model submission not recognized"

**Symptoms:**

Error: Model directory 'my_model' not found (reference_implementations/ or user_submissions/)

**Solution:**

```bash
# List available models by tier
ls -la submissions/reference_implementations/ || true
ls -la submissions/user_submissions/ || true
# Create new model from template (user tier)
cp -r submissions/templates/template submissions/user_submissions/my_model
# Verify structure
ls -la submissions/user_submissions/my_model/
```

**Command to verify fix:**

```bash
python run_benchmark.py --model my_model --dry-run
```

#### Issue: "Missing required solution files"

**Symptoms:**

Missing required file: prompt_1_solution.py

**Solution:**

```bash
# Check what files are missing
ls -la submissions/my_model/
# Copy missing files from template
cp submissions/template/prompt_1_solution.py submissions/my_model/
# Verify all required files exist
python scripts/validate_submission.py my_model
```

### 5. Environment Setup Issues

#### Issue: "Virtual environment activation fails"

**Symptoms:**

```bash
# Windows
'venv\Scripts\activate' is not recognized...

# macOS/Linux  
bash: venv/bin/activate: No such file or directory
```

**Solution:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate

# Verify activation
pip list
```

**Command to verify fix:**

```bash
python -c "import sys; print('Virtual env:', hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))"
```

#### Issue: "pip install fails with permission errors"

**Symptoms:**

ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied

**Solution:**

```bash
# Use user installation
pip install --user -r requirements.txt
# Or fix virtual environment
python -m venv venv --clear
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 6. Log File Analysis

#### Common Log Locations

- **Test logs**: `reports/session/YYYYMMDD_HHMMSS/pytest.log`
- **Validation logs**: `reports/session/YYYYMMDD_HHMMSS/ruff_check.log`
- **Security logs**: `reports/session/YYYYMMDD_HHMMSS/bandit.log`
- **Benchmark results**: `results/latest_results.json`

#### Analyzing Failed Runs

```bash
# Check latest test results
cat reports/session/$(ls -t reports/session/ | head -1)/pytest.log | grep ERROR

# Check validation issues
cat reports/session/$(ls -t reports/session/ | head -1)/ruff_check.log | tail -20

# Check security issues
cat reports/session/$(ls -t reports/session/ | head -1)/bandit.log | grep -A5 -B5 "HIGH\|MEDIUM"
```

### 7. Performance Issues

#### Issue: "Validation takes too long"

**Symptoms:**

- validate_docs.py hangs for minutes
- High CPU usage during validation

**Solution:**

```bash
# Skip sandbox creation for faster validation
python scripts/validate_docs.py --no-sandbox-safe --docs-only
# Skip network commands
python scripts/validate_docs.py --skip-network
# Use verbose mode to see progress
python scripts/validate_docs.py --verbose
```

#### Issue: "Benchmark runs out of memory"

**Symptoms:**

MemoryError: Unable to allocate array

**Solution:**

```bash
# Run with smaller batch sizes
python run_benchmark.py --model example_model --timeout 30
# Clear any cached results
rm -rf results/cache/
# Monitor memory usage
python run_benchmark.py --model example_model --verbose
```

## Validation Commands Reference

### Quick Health Check

```bash
# Run all validators in safe mode
python scripts/validate_docs.py --docs-only
python scripts/validate_security.py --dry-run
python -m pytest tests/ --tb=short
```

### Full Validation Suite

```bash
# Documentation validation
python scripts/validate_docs.py --verbose --no-sandbox-safe

# Security validation  
python scripts/validate_security.py

# Code quality validation
python -m ruff check .
python -m mypy benchmark/

# Test validation with coverage
python -m pytest tests/ --cov=benchmark --cov-report=html
```

### Debug Mode Commands

```bash
# Enable maximum verbosity
python run_benchmark.py --model example_model --verbose --debug

# Validate specific documentation file
python scripts/validate_docs.py --docs-only --verbose --project-root .

# Run single test with full output
python -m pytest tests/test_validators.py::test_specific_function -v -s
```

## Emergency Recovery

### Complete Environment Reset

```bash
# Remove virtual environment
rm -rf venv/

# Clean cached files
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Recreate environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python setup.py
```

### Restore Default Test Data

```bash
# Backup current test data
mv test_data test_data_backup_$(date +%Y%m%d_%H%M%S)

# Regenerate clean test data
python setup.py

# Verify generation
ls -la test_data/
python -c "import yaml; print(yaml.safe_load(open('test_data/config.yaml')))"
```

## Getting Additional Help

### Enable Debug Logging

```bash
export PYTHONPATH=.
export DEBUG=1
python run_benchmark.py --model example_model --verbose 2>&1 | tee debug.log
```

### Generate Detailed Reports

```bash
# Full system report (enhanced audit)
python validation/repo_audit_enhanced.py --path . --json audit_report.json > system_report.txt

# Validation report with output file
python scripts/validate_docs.py --output validation_report.txt

# Test report with coverage
python -m pytest tests/ --cov=benchmark --cov-report=html --html=test_report.html
```

### Contact and Resources

- Check recent commits in git log for related fixes
- Review CHANGELOG.md for known issues and their resolutions
- Examine `docs/logging/` for session-specific debugging info

## Platform-Specific Notes

### Windows

- Use PowerShell for better command compatibility
- Path separators: use `\` or double `\\` in strings
- Virtual env activation: `venv\Scripts\activate.bat`

### macOS/Linux

- Virtual env activation: `source venv/bin/activate`
- May need to install python3-dev for some packages
- Use `python3` explicitly if `python` points to Python 2

### Cross-Platform

- Use `Path()` objects in Python for path handling
- Always use forward slashes in documentation examples
- Test commands on target platform before documenting
