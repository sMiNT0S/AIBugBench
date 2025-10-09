# Scoring Methodology

## Overview

Seven categories, 25 points per prompt (100 total). Passing is 60% (15/25 per prompt).

- Security • Performance • Maintainability • Syntax • Structure • Execution • Quality
- Detailed feedback explains deductions and partial credit.

## Understanding Your Results

### Results File Structure

See [User Guide – Running Your First Benchmark](user-guide.md#running-your-first-benchmark) for the canonical results directory layout and file descriptions.

### Enhanced Feedback Format

- Traditional: `✅ Error handling (5/5)`
- Enhanced: `✅ Code Structure (3.0/3.0): ✓yaml_import, json_import, logging`
- Partial credit: `⚠️ Performance (1.9/2.0): ✓no_nested_loops ✗string_concat_in_loops`

### Grade Scale

| Percentage | Letter Grade | Description |
|------------|--------------|-------------|
| 90-100%    | A           | **Production Ready** - Code meets industry standards with comprehensive quality |
| 80-89%     | B           | **Good** - High quality code with minor improvements needed |
| 70-79%     | C           | **Satisfactory** - Functional code with some quality issues to address |
| 60-69%     | D           | **Minimal** - Meets basic requirements, significant improvements needed |
| 0-59%      | F           | **Fail** - Major issues, security risks, or non-functional code |

## Scoring Breakdown

### Prompt 1: Code Refactoring & Analysis (25 points)

Tests ability to refactor and improve existing Python code while maintaining functionality.

#### 1. Syntax Validation (5 points)

- **Valid Python Syntax (5 points)**: Code parses without syntax errors
- **Import Organization**: Proper import structure and organization

#### 2. Code Structure (3 points)

- **Required Imports (0.75 pts)**: yaml, json imports present
- **Error Handling (0.75 pts)**: try-except blocks implemented
- **Logging Integration (0.75 pts)**: Proper logging setup
- **Type Hints (0.75 pts)**: Function annotations added

#### 3. Execution Success (6 points)

- **Runtime Success (4 pts)**: Script executes without crashing
- **Correct Output (2 pts)**: Produces expected USA users filtering

#### 4. Code Quality (3 points)

- **No Global Variables (0.75 pts)**: Proper scope management
- **Modern Path Handling (0.75 pts)**: Uses pathlib instead of os.path
- **Main Guard (0.75 pts)**: Proper `if __name__ == "__main__"` structure
- **Context Managers (0.75 pts)**: Uses `with` statements for file operations

#### 5. Security Analysis (4 points)

- **No Security Vulnerabilities (4 points)**: Clean code with no detected security issues
  - SQL injection patterns detection
  - Hardcoded secrets/API keys detection
  - Path traversal vulnerability checks
  - Unsafe function usage (`eval()`, `exec()`, `shell=True`)
- **Partial Credit**: Graduated deductions for security issues found

#### 6. Performance Analysis (2 points)

- **Efficient Algorithms (2 points)**: No detected performance issues
  - O(n²) algorithm detection (nested loops over same data)
  - Inefficient patterns (string concatenation in loops, membership testing)
  - Memory usage patterns (full file reads, large structures in loops)
  - Algorithm efficiency (multiple sorts, unnecessary conversions)
- **Partial Credit**: Deductions based on performance issue severity

#### 7. Maintainability Analysis (2 points)

- **Good Maintainability (2 points)**: Code follows maintainability best practices
  - Function length analysis (functions >20 lines flagged)
  - Code duplication detection (repeated 3+ line blocks)
  - Variable naming quality (meaningful names, not single letters)
  - Complexity indicators (nested conditions, boolean complexity)
- **Partial Credit**: Deductions for maintainability issues

### Prompt 2: YAML/JSON Correction (25 points)

Tests ability to fix malformed configuration files and ensure cross-format consistency.

#### 1. Syntax Validation (4 points)

- **YAML Parsing (2 points)**: File loads with yaml.safe_load without errors
- **JSON Parsing (2 points)**: File loads with json.load without errors

#### 2. Code Structure (6 points)

- **Required Keys (3 points)**: All top-level sections preserved
- **Nested Shapes (2 points)**: Dictionary and list structures maintain correct types
- **Arrays vs Scalars (1 point)**: api_keys remains list, scalars remain scalars

#### 3. Execution Success (8 points)

- **Deep Equivalence (6 points)**: Perfect cross-format equivalence after type normalization
- **Partial Matches (2 points)**: Per-key equivalent values between YAML and JSON

#### 4. Code Quality (6 points)

- **YAML Indentation (2 points)**: Consistent 2-space indentation, no tabs
- **JSON Literals (2 points)**: Proper boolean/integer types, not strings
- **Formatting Style (1 point)**: Clean, readable format structure
- **No Duplication (1 point)**: Efficient data representation

#### 5. Security Analysis (1 point)

- **YAML Safety (1 point)**: No dangerous YAML constructs (!!python/, anchors, references)

#### 6-7. Performance & Maintainability (N/A)

- Not applicable for static configuration files

### Prompt 3: Data Transformation (25 points)

Tests ability to implement complex data transformation logic with business rules.

#### 1. Syntax Validation (3 points)

- **File Compilation (2 points)**: Python file imports and compiles without errors
- **Function Exists (1 point)**: transform_and_enrich_users function is present and loadable

#### 2. Code Structure (3 points)

- **Correct Signature (2 points)**: Exact function signature transform_and_enrich_users(user_list)
- **Basic Organization (1 point)**: Has return statement and iteration logic

#### 3. Execution Success (12 points) - **Major Focus**

- **Function Runs (2 points)**: Executes without crashing on test data
- **ID Standardization (2 points)**: All user IDs converted to integer type
- **Email Provider Extraction (2 points)**: Email domains correctly extracted and added
- **Age Normalization (2 points)**: String ages converted to integer type
- **Business Rules Validation (3 points)**: Account tiers calculated according to documented rules
- **Graceful Error Handling (1 point)**: Handles malformed records appropriately

#### 4. Code Quality (3 points)

- **Error Handling (1 point)**: Has try/except blocks for transformations
- **Type Conversions (1 point)**: Uses explicit type conversion functions
- **Readable Loops (1 point)**: Clear, readable iteration patterns

#### 5. Security Analysis (1 point)

- **Safe Constructs (1 point)**: No dangerous constructs (eval, exec, file operations)

#### 6. Performance Analysis (1 point)

- **Single Pass (1 point)**: Efficient single-pass processing without nested loops

#### 7. Maintainability Analysis (2 points)

- **Code Organization (2 points)**: Function length, complexity, and naming quality assessment

### Prompt 4: API Integration & Robustness (25 points)

Tests ability to implement secure and robust API integration with proper error handling.

#### 1. Syntax Validation (2 points)

- **File Compilation (1 point)**: Python file compiles and imports successfully
- **Function Exists (1 point)**: sync_users_to_crm function is present and loadable

#### 2. Code Structure (3 points)

- **Correct Signature (1 point)**: Exact signature sync_users_to_crm(user_data, api_token)
- **Request Structure (2 points)**: Proper HTTP POST formation with JSON payload and headers

#### 3. Execution Success (7 points) - **Behavioral Testing**

- **Success Handling (2 points)**: Returns job_id correctly on 200 response
- **400 Bad Request (1 point)**: Handles 400 status appropriately without crashing
- **401 Unauthorized (1 point)**: Handles 401 status appropriately without crashing
- **503 Service Unavailable (1 point)**: Handles 503 status appropriately without crashing
- **Connection Errors (1 point)**: Handles network connection failures gracefully
- **JSON Parsing (1 point)**: Correctly extracts data from API response JSON

#### 4. Code Quality (3 points)

- **Informative Errors (2 points)**: Clear error messages for different failure scenarios
- **Documentation (1 point)**: Function docstrings or type hints present

#### 5. Security Analysis (7 points) - **Highest Priority**

- **Bearer Authentication (3 points)**: Correct Bearer token in Authorization header
- **No Token Leakage (2 points)**: API token not exposed in URL or request body
- **Explicit Timeouts (2 points)**: Request timeout specified (prevents hanging)

#### 6. Performance Analysis (2 points)

- **Retry Resilience (2 points)**: Retry logic, backoff patterns, or session usage for network reliability

#### 7. Maintainability Analysis (1 point)

- **Code Organization (1 point)**: Clear structure with meaningful variable names

## Common Patterns and Issues

### Security Red Flags

- Use of `eval()` or `exec()`
- Hardcoded API keys or passwords
- SQL query string concatenation
- Missing input validation
- Path traversal vulnerabilities

### Performance Anti-patterns

- Nested loops over same data (O(n²) complexity)
- String concatenation in loops
- Loading entire files into memory unnecessarily
- Multiple sorting operations on same data
- Inefficient membership testing (list vs set)

### Maintainability Concerns

- Functions longer than 20 lines
- Repeated code blocks (3+ lines)
- Single-letter variable names
- Deeply nested conditions (>3 levels)
- Missing error handling

## Bonus Points and Advanced Features

Models can earn bonus recognition for:

- **Exceptional error handling**: Beyond required try-catch blocks
- **Clean, documented code**: Comprehensive comments and docstrings
- **Performance optimizations**: Efficient algorithms and data structures
- **Security best practices**: Proactive security measures
- **Advanced Python features**: Proper use of modern Python patterns

## Implementation Status

- **✅ Prompt 1**: Complete 7-category scoring system (5/3/6/3/4/2/2 = 25pts)
- **✅ Prompt 2**: Complete 7-category scoring system (4/6/8/6/1/0/0 = 25pts)
- **✅ Prompt 3**: Complete 7-category scoring system (3/3/12/3/1/1/2 = 25pts)
- **✅ Prompt 4**: Complete 7-category scoring system (2/3/7/3/7/2/1 = 25pts)
- **📊 Results**: Enhanced feedback across all prompts with Security, Performance, and Maintainability analysis

## Implicit & Advanced Scoring Signals

While prompts state the core functional goals, several evaluated dimensions are intentionally only partially explicit to preserve differentiation between baseline and advanced model capabilities. This section documents them so results feel transparent without turning them into rote checklist items.

### Core Expectations (Should Not Be Surprises)

These are security / correctness norms that affect scoring even if not always spelled out verbatim in each prompt:

- Explicit network timeouts for outbound HTTP calls (Prompt 4)
- No secret / token leakage outside Authorization headers (Prompt 4)
- Avoid dangerous constructs (eval/exec, hardcoded credentials, unsafe YAML loaders)
- Graceful partial failure handling (skip / continue rather than crash on a malformed record)
- Safe file / path handling and context managers where file I/O appears (Prompt 1)

### Advanced / Bonus Differentiators (Intentionally Implicit)

Higher‑capability models tend to infer these; they yield extra points but are not mandatory for baseline correctness:

- Retry / backoff or session reuse for transient API failures (Prompt 4 resilience)
- Efficient single‑pass transformations and avoiding avoidable O(n²) patterns (Prompt 3, general)
- Clear modular decomposition, meaningful naming, docstrings, and type hints beyond minimal function signature
- Structured, differentiated error messaging tied to specific status codes (Prompt 4)
- Use of context managers, pathlib, and modern Python idioms (Prompt 1 spillover)

### Flexible Acceptances

Scoring allows more than one “correct” representation:

- Prompt 4 success return: Either the raw `job_id` string or a structure containing it is accepted
- Partial credit on HTTP request assembly (POST + headers + JSON) even if one element is missing
- Partial credit on JSON parsing if structure is partly correct

### Partial Credit Patterns

Many categories award proportional points instead of binary pass/fail. Typical examples:

- Request structure (Prompt 4): Independent credit for method, payload shape, headers
- Performance & maintainability: Deductions accumulate per detected issue rather than zeroing the category

### Why Not Fully Enumerate Everything in Prompts?

Keeping some advanced signals implicit preserves stratification—stronger models surface better engineering patterns without being spoon‑fed. Documenting them here balances fairness with challenge: authors understand why points moved without converting advanced behaviors into mandatory boilerplate.

### How To Use This Section

If you lose points you didn’t anticipate, map the feedback line to a bucket above (Core vs Advanced). Treat Core misses as required fixes; treat Advanced misses as opportunities to differentiate.

## Next Steps

After reviewing your scores:

1. **Identify weak areas**: Focus on categories with lowest scores
2. **Review specific feedback**: Each failure includes detailed rationale
3. **Implement fixes**: Address security, performance, and maintainability issues
4. **Re-run benchmark**: Track improvement over iterations
5. **Compare models**: Use comparison charts to evaluate different approaches

For model development guidance, see the **[Developer Guide](developer-guide.md)**.
