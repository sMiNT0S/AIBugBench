# User Guide

How to run benchmarks and read results.

## Running Your First Benchmark

### Basic Workflow

1. **Setup** (one-time): See [Getting Started](getting-started.md) for platform-specific installation and environment setup.

2. **Test example model**:

   ```bash
   python run_benchmark.py --model example_model
   ```

3. **Review results** (v0.8.1+ timestamped layout):

Each benchmark run writes to a timestamped directory preserving history:

```text
results/
  latest_results.json                # Pointer to most recent run (backward-compatible)
  20250827_143215/                   # Run-specific directory (YYYYMMDD_HHMMSS format)
    latest_results.json              # Full JSON (models + comparison + _metadata)
    detailed/
      detailed_results.json          # Stable path for tooling
      summary_report_20250827_143215.txt
    comparison_charts/
      comparison_chart.txt           # ASCII comparison bars
```

**Key advantages**:

- Atomic writes (no partial files)
- Historical retention (track model performance over time)
- Dynamic prompt support (new prompts automatically appear in comparison data)

Quick access:

- Check console output for immediate feedback
- Open `results/latest_results.json` (most recent run)
- Review `results/<RUN_TS>/detailed/summary_report_<RUN_TS>.txt` for human-readable analysis

## Understanding the Benchmark Process

### What Happens During a Benchmark Run

1. **Initialization**: Loads your model's submissions from `submissions/your_model/`
2. **Validation**: Each solution file is validated for syntax and structure
3. **Execution**: Solutions are run against test data to verify functionality
4. **Analysis**: Code is analyzed for security, performance, and maintainability
5. **Scoring**: Points awarded based on 7-category assessment
6. **Reporting**: Results saved in multiple formats for review

### The Four Challenges

#### Challenge 1: Code Refactoring (25 points)

- **Goal**: Modernize legacy Python code
- **Focus**: Clean code, error handling, security

#### Challenge 2: Configuration Repair (25 points)

- **Goal**: Fix broken YAML/JSON files
- **Focus**: Format validation, cross-format consistency

#### Challenge 3: Data Transformation (25 points)

- **Goal**: Implement business logic for data processing
- **Focus**: Correct transformations, edge case handling

#### Challenge 4: API Integration (25 points)

- **Goal**: Create robust API client with error handling
- **Focus**: Security, authentication, resilience

## Interpreting Your Results

### Console Output

During benchmark execution, you'll see:

Testing model: your_model_name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Testing Refactoring & Analysis...
  ✅ Syntax Validation (5.0/5.0)
  ✅ Code Structure (3.0/3.0)
  ✅ Execution Success (6.0/6.0)
  ⚠️ Code Quality (2.5/3.0)
  ✅ Security Analysis (4.0/4.0)
  ⚠️ Performance Analysis (1.5/2.0)
  ✅ Maintainability (2.0/2.0)
  PASSED - Score: 24.00/25 (96.0%)

**Symbol Meanings:**

- ✅ Full points earned
- ⚠️ Partial points earned
- ❌ No points earned

### Results Files

#### latest_results.json (root pointer)

Complete scoring data with detailed breakdowns:

- Individual category scores
- Specific issues detected
- Performance metrics
- Security vulnerabilities

#### detailed/summary_report_<RUN_TS>.txt

Human-readable analysis including:

- Score breakdown by category
- Specific feedback for improvements
- Comparison to benchmark standards
- Recommendations for fixes

#### comparison_charts/comparison_chart.txt

Visual representation of scores:

- Progress bars for each category
- Overall grade and percentage
- Quick visual assessment

### Understanding Grades

See [Scoring Methodology – Grade Scale](scoring-methodology.md#grade-scale) for the canonical letter-grade interpretation and thresholds.

## Result Metadata & Privacy

### What Information is Captured

Benchmark results embed minimal provenance metadata to aid reproducibility and debugging:

- **spec_version**: Benchmark scoring specification revision
- **git_commit**: Short commit hash of the repository state (local only, never transmitted)
- **python_version**: Interpreter version used to run the benchmark
- **platform**: Operating system, release, and architecture string
- **timestamp_utc**: UTC run time (RFC 3339 format with Z suffix)
- **dependency_fingerprint**: First 16 hex characters of SHA256 hash of `requirements.txt` (non-reversible drift indicator)

### Privacy Assurance

**No personal data is collected or transmitted**. All data is written only to local `results/` JSON and text files. If you publish results publicly, you may reveal commit hashes or platform details, but no identifying information is included by default.

### Opting Out

If you need to share results from private repositories or sensitive environments, you can suppress metadata collection:

**CLI Flag:**

```bash
python run_benchmark.py --model your_model --no-metadata
```

**Environment Variable:**

```bash
export AIBUGBENCH_DISABLE_METADATA=1
python run_benchmark.py --model your_model
```

Either mechanism retains only `spec_version` and suppresses git/platform/timestamp/dependency fingerprint fields.

## Best Practices for High Scores

### Security First

- Never use `eval()` or `exec()`
- Avoid hardcoded credentials
- Validate all inputs
- Use safe parsing methods (`yaml.safe_load`)
- Include proper authentication headers

### Performance Matters

- Avoid nested loops (O(n²) complexity)
- Use efficient data structures (sets for membership)
- Minimize file I/O operations
- Process data in single passes when possible

### Maintainable Code

- Keep functions under 20 lines
- Use descriptive variable names
- Add error handling for edge cases
- Include type hints and docstrings
- Avoid code duplication

### Proper Error Handling

- Use specific exception types
- Provide informative error messages
- Handle network failures gracefully
- Include retry logic for transient errors

## Comparing Multiple Models

Run all discovered models or a specific model. For concurrency and all CLI flags, see the [API Reference – CLI Reference](api-reference.md#cli-reference).

```bash
# All models (sequential)
python run_benchmark.py

# Single model
python run_benchmark.py --model your_model
```

### Analyzing Differences

Use the comparison script:

```bash
python scripts/compare_benchmarks.py --models gpt4 claude llama
```

This generates:

- Side-by-side score comparisons
- Strength/weakness analysis per model
- Statistical summaries
- Recommendations for model selection


## Troubleshooting Low Scores

### Syntax/Structure Issues

**Problem**: Files don't parse or load
**Solution**: Verify proper Python/YAML/JSON syntax

### Execution Failures

**Problem**: Code crashes during execution
**Solution**: Add error handling for edge cases

### Security Penalties

**Problem**: Dangerous patterns detected
**Solution**: Review security best practices, avoid unsafe functions

### Performance Deductions

**Problem**: Inefficient algorithms flagged
**Solution**: Optimize loops, use appropriate data structures

### Maintainability Concerns

**Problem**: Complex or duplicated code
**Solution**: Refactor for clarity, extract common functions

## Advanced Usage

For full CLI options (timeouts, verbosity, concurrency, output directories) and CI examples, see the [API Reference – CLI Reference](api-reference.md#cli-reference).

## Next Steps

After running benchmarks:

1. **Analyze weak areas**: Focus on lowest-scoring categories
2. **Review specific feedback**: Each issue includes improvement suggestions
3. **Iterate on solutions**: Address issues and re-test
4. **Compare approaches**: Try different prompting strategies
5. **Share insights**: Contribute findings to the community

## Getting Help

- **Documentation**: Review guides in `docs/` directory
- **Examples**: Study `submissions/example_model/` for reference
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
- **Contributing**: Check [Contributing Guidelines](contributing.md)

## See Also

- **[Getting Started](getting-started.md)** - Initial setup
- **[Scoring Methodology](scoring-methodology.md)** - Score details

## Glossary

- Benchmark Runner: Orchestrates submissions, validators, scoring, and writes outputs (entry: `run_benchmark.py`).
- Validator: Checks syntax, structure, execution; analyzes quality, security, performance, maintainability.
- SecureRunner (Sandbox): Confines filesystem, cleans env vars, enforces resource/time limits.
- Sabotage Fixtures: Intentionally broken inputs in `test_data/` representing real-world failure modes.
- Tiered Submissions: `submissions/` layout with `reference_implementations/`, `templates/template/`, `user_submissions/`.
- RUN_TS: Timestamped directory `YYYYMMDD_HHMMSS` under `results/` for detailed artifacts.
- latest_results.json: Root pointer to most recent run under `results/`.
- Grade Scale: Percentage→letter mapping in [Scoring Methodology](scoring-methodology.md#grade-scale).
- Determinism: Reproducible, offline-by-default runs with no import-time side effects.
