# User Guide

Comprehensive guide for running benchmarks and understanding AIBugBench results.

## Running Your First Benchmark

### Basic Workflow

1. **Setup** (one-time):

   ```bash
   python setup.py
   pip install -r requirements.txt
   ```

2. **Test example model**:

   ```bash
   python run_benchmark.py --model example_model
   ```

3. **Review results** (v0.8.1+ layout):

- Check console output for immediate feedback
- Open `results/latest_results.json` (pointer to most recent)
- Inspect `results/<RUN_TS>/latest_results.json` for full run data
- Review `results/<RUN_TS>/detailed/summary_report_<RUN_TS>.txt` for analysis

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
- **Key Skills**: Python best practices, logging, type hints

#### Challenge 2: Configuration Repair (25 points)

- **Goal**: Fix broken YAML/JSON files
- **Focus**: Format validation, cross-format consistency
- **Key Skills**: YAML/JSON syntax, data structure preservation

#### Challenge 3: Data Transformation (25 points)

- **Goal**: Implement business logic for data processing
- **Focus**: Correct transformations, edge case handling
- **Key Skills**: Data manipulation, business rule implementation

#### Challenge 4: API Integration (25 points)

- **Goal**: Create robust API client with error handling
- **Focus**: Security, authentication, resilience
- **Key Skills**: HTTP requests, error handling, security

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

| Grade | Score Range | What It Means |
|-------|------------|---------------|
| **A** | 90-100% | Production-ready code with excellent quality |
| **B** | 80-89% | Good code with minor issues to address |
| **C** | 70-79% | Functional but needs improvement |
| **D** | 60-69% | Minimal passing, significant issues |
| **F** | 0-59% | Critical failures, not production-ready |

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

### Running Comparisons & Concurrency

Run all discovered models sequentially (default):

```bash
python run_benchmark.py
```

Enable concurrent evaluation (thread pool):

```bash
python run_benchmark.py --workers 4
```

Run only specific model:

```bash
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

## Common Patterns in Results

### High Performers (90%+)

- Comprehensive error handling
- Modern Python idioms
- Security-conscious coding
- Efficient algorithms
- Clear code organization

### Medium Performers (70-89%)

- Basic functionality works
- Some error handling present
- Minor security issues
- Occasional inefficiencies
- Room for refactoring

### Low Performers (<70%)

- Missing core functionality
- Poor error handling
- Security vulnerabilities
- Inefficient algorithms
- Code quality issues

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

### Custom Test Configurations

Override default settings:

```bash
# Extended timeout for complex models
python run_benchmark.py --model complex_model --timeout 60

# Verbose output for debugging
python run_benchmark.py --model debug_model --verbose

# Custom results directory
python run_benchmark.py --model test --results-dir custom_results/
```

### Automating Benchmark Runs

Create a batch testing script:

```bash
#!/bin/bash
models=("gpt4" "claude" "llama")
for model in "${models[@]}"; do
    echo "Testing $model..."
    python run_benchmark.py --model $model --quiet
    sleep 2
done
```

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
- name: Run AIBugBench
  run: |
    python setup.py
    python run_benchmark.py --model ${{ matrix.model }} --quiet
    
- name: Check Score Threshold
  run: |
    score=$(jq '.total_score' results/latest_results.json)
    if (( $(echo "$score < 70" | bc -l) )); then
      echo "Score below threshold: $score"
      exit 1
    fi
```

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
- **[Developer Guide](developer-guide.md)** - Adding models
- **[Scoring Methodology](scoring-methodology.md)** - Score details
- **[API Reference](api-reference.md)** - Technical reference
