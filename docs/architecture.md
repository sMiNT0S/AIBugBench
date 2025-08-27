# Architecture

Technical overview of AIBugBench's design, components, and implementation patterns.

## System Overview

AIBugBench is a Python-based benchmarking framework designed to evaluate AI model code generation capabilities across multiple quality dimensions. The system uses a modular architecture with clear separation between test data generation, submission handling, validation logic, and scoring mechanisms.

### High-Level Architecture

┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│                  (CLI: run_benchmark.py)                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│                   (benchmark/runner.py)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼──────────┐  ┌─────▼─────────┐
│  Validation    │  │    Scoring         │  │   Utils       │
│  Engine        │  │    Engine          │  │   Layer       │
│ (validators.py)│  │  (scoring.py)      │  │  (utils.py)   │
└────────────────┘  └────────────────────┘  └───────────────┘
        │                     │                     │
┌───────▼─────────────────────▼─────────────────────▼─────────┐
│                      Data Layer                             │
│     (test_data/, submissions/, results/, prompts/)          │
└─────────────────────────────────────────────────────────────┘

## Component Design

### Core Components

#### 1. Setup System (`setup.py`)

Responsible for generating test data with intentional sabotage patterns:

```python
class SabotageGenerator:
    """Creates deliberately broken test files with specific bug patterns."""
    
    def generate_yaml_errors(self):
        # Mixed indentation, type confusion, invalid syntax
        
    def generate_python_bugs(self):
        # Logic errors, security vulnerabilities, inefficiencies
        
    def generate_json_issues(self):
        # Format errors, type mismatches, structural problems
```

**Key Features:**

- Reproducible sabotage patterns
- Platform-agnostic file generation
- AI context file creation (`ai_prompt.md`)

#### 2. Runner Module (`benchmark/runner.py`)

Orchestrates benchmark execution and result aggregation:

```python
class BenchmarkRunner:
    def __init__(self, model_name: str, results_dir: str = "results/"):
        self.model_name = model_name
        self.results_dir = Path(results_dir)
        self.validators = self._load_validators()
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all prompts and aggregate results."""
        
    def _handle_timeout(self, func, timeout: int):
        """Wrap validation functions with timeout protection."""
        
    def _save_results(self, results: Dict[str, Any]):
        """Persist results in multiple formats."""
```

**Responsibilities:**

- Model discovery and loading
- Test execution orchestration
- Timeout management
- Result persistence

#### 3. Validation Engine (`benchmark/validators.py`)

Implements prompt-specific validation logic:

```python
class PromptValidator:
    """Base class for prompt validation."""
    
    def validate_syntax(self, file_path: str) -> ValidationResult:
        """Check syntax validity."""
        
    def validate_execution(self, file_path: str) -> ValidationResult:
        """Test runtime behavior."""
        
    def analyze_security(self, code: str) -> SecurityAnalysis:
        """Detect security vulnerabilities."""
        
    def analyze_performance(self, code: str) -> PerformanceAnalysis:
        """Identify performance issues."""
        
    def analyze_maintainability(self, code: str) -> MaintainabilityAnalysis:
        """Assess code quality and maintainability."""
```

**Validation Categories:**

1. **Syntax Validation**: Parse checking, import verification
2. **Structure Validation**: Function signatures, required components
3. **Execution Testing**: Runtime behavior, output correctness
4. **Quality Assessment**: Code patterns, best practices
5. **Security Analysis**: Vulnerability detection, unsafe patterns
6. **Performance Analysis**: Algorithm efficiency, resource usage
7. **Maintainability Analysis**: Complexity, duplication, naming

#### 4. Scoring Engine (`benchmark/scoring.py`)

Implements the 7-category scoring system:

```python
class ScoringEngine:
    """Calculate scores based on validation results."""
    
    SCORING_WEIGHTS = {
        'prompt_1': {
            'syntax': 5,
            'structure': 3,
            'execution': 6,
            'quality': 3,
            'security': 4,
            'performance': 2,
            'maintainability': 2
        },
        # Additional prompt weights...
    }
    
    def calculate_score(self, validation_result: Dict) -> Score:
        """Apply weighted scoring to validation results."""
        
    def determine_grade(self, total_score: float) -> str:
        """Map numerical score to letter grade."""
```

**Scoring Distribution:**

- Prompt 1: 5/3/6/3/4/2/2 = 25 points
- Prompt 2: 4/6/8/6/1/0/0 = 25 points
- Prompt 3: 3/3/12/3/1/1/2 = 25 points
- Prompt 4: 2/3/7/3/7/2/1 = 25 points

#### 5. Utility Layer (`benchmark/utils.py`)

Common functionality and helper functions:

```python
class BenchmarkUtils:
    @staticmethod
    def safe_load_json(file_path: str) -> Optional[Dict]:
        """Load JSON with comprehensive error handling."""
        
    @staticmethod
    def safe_load_yaml(file_path: str) -> Optional[Dict]:
        """Load YAML safely without code execution."""
        
    @staticmethod
    def format_results(results: Dict) -> str:
        """Create human-readable result summaries."""
        
    @staticmethod
    def create_comparison_chart(results: List[Dict]) -> str:
        """Generate visual comparison charts."""
```

## Plugin Architecture

### Submission Structure

The tiered submission system supports multiple organizational patterns:
submissions/
├── reference_implementations/   # Verified reference solutions
│   └── example_model/
├── user_submissions/           # User-provided solutions
│   └── custom_model/
└── templates/                  # Starting templates
    └── template/

**Discovery Mechanism:**

1. Check `reference_implementations/` first
2. Fall back to `user_submissions/`
3. Finally check deprecated flat structure
4. Abort if ambiguous (model in multiple tiers)

### Adding Custom Validators

Extend validation for new prompt types:

```python
from benchmark.validators import BaseValidator

class CustomPromptValidator(BaseValidator):
    def validate(self, submission_path: str) -> ValidationResult:
        result = ValidationResult()
        
        # Custom validation logic
        result.add_check('custom_check', self.check_custom_requirement())
        
        return result
```

## Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/test_*_unit.py`)
   - Individual component testing
   - Mock external dependencies
   - Fast, isolated execution

2. **Integration Tests** (`tests/test_*_integration.py`)
   - Component interaction testing
   - Real file I/O operations
   - End-to-end workflows

3. **Security Tests** (`tests/test_security_*.py`)
   - Vulnerability scanning
   - Injection attack prevention
   - Safe parsing verification

4. **Performance Tests** (`tests/test_performance_*.py`)
   - Timeout enforcement
   - Memory usage monitoring
   - Algorithm efficiency validation

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=benchmark --cov-report=html

# Run specific category
pytest tests/test_*_unit.py

# Run with markers
pytest -m "not slow"
```

## Security Model

### Input Validation

All user inputs are validated before processing:

1. **File Path Validation**: Prevent directory traversal
2. **Code Execution Prevention**: No `eval()`, `exec()`, or `shell=True`
3. **YAML Safety**: Use `yaml.safe_load()` exclusively
4. **Timeout Protection**: Prevent infinite loops and DoS

### Sandboxing Strategy

```python
class SafeExecutor:
    """Execute user code in controlled environment."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
    def execute_with_timeout(self, func, *args, **kwargs):
        """Run function with timeout and resource limits."""
        
    def validate_imports(self, code: str) -> bool:
        """Check for dangerous import statements."""
        
    def sanitize_paths(self, path: str) -> str:
        """Prevent directory traversal attacks."""
```

### Vulnerability Detection

Security analysis patterns:

```python
SECURITY_PATTERNS = {
    'eval_exec': r'\b(eval|exec)\s*\(',
    'sql_injection': r'f["\'].*SELECT.*WHERE.*{.*}',
    'hardcoded_secrets': r'(password|api_key|token)\s*=\s*["\']',
    'path_traversal': r'\.\./|\.\.\\',
    'command_injection': r'subprocess.*shell\s*=\s*True'
}
```

## Performance Optimization

### Caching Strategy

Results and intermediate data are cached:

```python
class ResultCache:
    def __init__(self, cache_dir: Path = Path(".cache")):
        self.cache_dir = cache_dir
        
    def get_or_compute(self, key: str, compute_func):
        """Return cached result or compute and cache."""
        
    def invalidate(self, pattern: str = "*"):
        """Clear cache entries matching pattern."""
```

### Parallel Execution

Support for concurrent model testing:

```python
from concurrent.futures import ProcessPoolExecutor

def test_models_parallel(model_names: List[str]):
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(test_single_model, name)
            for name in model_names
        ]
        results = [f.result() for f in futures]
    return results
```

## Data Flow

### Benchmark Execution Flow

1. User invokes: python run_benchmark.py --model X
                            │
2. Load submission files from submissions/X/
                            │
3. For each prompt (1-4):
   a. Load test data
   b. Validate syntax
   c. Check structure
   d. Execute code
   e. Analyze quality/security/performance
   f. Calculate score
                            │
4. Aggregate scores across prompts
                            │
5. Generate grade and feedback
                            │
6. Save results to multiple formats:
   - JSON (latest_results.json)
   - Text summary (summary_report_*.txt)
   - Comparison chart (comparison_chart_*.txt)

### Error Handling Flow

Try operation
     │
     ├─> Success: Continue to next step
     │
     └─> Failure:
           │
           ├─> Recoverable: Log warning, apply partial score
           │
           └─> Critical: Log error, return zero score, continue to next prompt

## Configuration Management

### Configuration Hierarchy

1. **Default Configuration** (hardcoded in modules)
2. **Environment Variables** (override defaults)
3. **Command Line Arguments** (highest priority)

```python
class ConfigManager:
    def get_config(self) -> Config:
        config = self.load_defaults()
        config.update(self.load_environment())
        config.update(self.parse_arguments())
        return config
```

## Extensibility Points

### Adding New Prompts

1. Create prompt file in `prompts/`
2. Add validator in `benchmark/validators.py`
3. Update scoring weights in `benchmark/scoring.py`
4. Add tests in `tests/`

### Custom Output Formats

```python
class CustomFormatter(BaseFormatter):
    def format(self, results: Dict) -> str:
        """Convert results to custom format."""
        
# Register formatter
FORMATTERS['custom'] = CustomFormatter()
```

### Integration Points

- **CI/CD Integration**: Exit codes, quiet mode, JSON output
- **IDE Integration**: Structured error messages, file paths
- **Web Service**: REST API wrapper possible
- **Database Storage**: Results can be persisted to DB

## Maintenance Patterns

### Version Management

```python
__version__ = "0.8.0"

def check_compatibility(submission_version: str) -> bool:
    """Verify submission compatibility with benchmark version."""
```

### Deprecation Handling

```python
def deprecated(message: str):
    """Decorator for deprecated functionality."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

## Future Enhancements

### Planned Features

1. **Web Dashboard**: Interactive result visualization
2. **Model Comparison Matrix**: Advanced statistical analysis
3. **Custom Challenge Creator**: UI for adding new prompts
4. **Cloud Execution**: Distributed testing capability
5. **Real-time Monitoring**: Live progress tracking
6. **Advanced Analytics**: ML-based pattern detection

### Architecture Evolution

- Microservice decomposition for scalability
- Container-based execution for isolation
- Event-driven architecture for extensibility
- GraphQL API for flexible querying

## See Also

- **[Getting Started](getting-started.md)** - Setup and usage
- **[Developer Guide](developer-guide.md)** - Adding models
- **[API Reference](api-reference.md)** - Technical details
- **[Contributing](contributing.md)** - Development guidelines
