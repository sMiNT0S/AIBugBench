# AIBugBench 🤖

A comprehensive benchmarking tool for evaluating AI models' code generation, refactoring, and problem-solving capabilities. Test any AI model's programming skills across 4 distinct challenges!

## Requirements

```
pyyaml>=6.0
requests>=2.25.0
```

## 🚀 Quick Start

1. **Clone the repository**

   **Windows (CMD):**
   ```cmd
   git clone https://github.com/sMiNT0S/AIBugBench.git
   cd AIBugBench
   ```

   **Windows (PowerShell):**
   ```powershell
   git clone https://github.com/sMiNT0S/AIBugBench.git
   cd AIBugBench
   ```

   **macOS/Linux (Bash):**
   ```bash
   git clone https://github.com/sMiNT0S/AIBugBench.git
   cd AIBugBench
   ```

2. **Set up virtual environment (strongly recommended)**

   For consistent and fair benchmark results across all users, we **strongly recommend** using a virtual environment. This ensures:
   - All tests run with the same dependency versions
   - No interference from system-installed packages
   - Reproducible results regardless of your local Python setup
   - Prevention of package conflicts that could affect scoring

   **Windows (CMD):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

   **macOS/Linux (Bash):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   > **Note**: Always activate your virtual environment before running benchmarks to ensure fair and consistent results.

3. **Run setup and install dependencies**

   **All Platforms:**
   ```bash
   python setup.py
   pip install -r requirements.txt
   ```
   
   > **Why run setup.py?** It creates deliberately broken test files (`process_records.py`, `config.yaml`, `user_data.json`) that AI models must fix. Without this step, the benchmark has no test cases!

4. **Try the example model** (to verify setup)

   **All Platforms:**
   ```bash
   python run_benchmark.py --model example_model
   ```

5. **Add your own AI model code submissions**

   First, create a folder for your AI model's code responses:

   **Windows (CMD):**
   ```cmd
   xcopy /E /I submissions\template submissions\your_model_name
   ```

   **Windows (PowerShell):**
   ```powershell
   Copy-Item -Recurse submissions\template submissions\your_model_name
   ```

   **macOS/Linux (Bash):**
   ```bash
   cp -r submissions/template submissions/your_model_name
   ```

   Then add your AI's Python code responses to each prompt file in `submissions/your_model_name/` and run the benchmark:

   **All Platforms:**
   ```bash
   python run_benchmark.py --model your_model_name
   ```

   > **Quick tip**: See the "🎯 How to Add Your AI Model" section below for detailed instructions on creating submissions.

## 📋 What This Tool Tests

The benchmark consists of 4 progressively challenging prompts that test different AI capabilities:

### Prompt 1: Code Refactoring & Analysis (25 points)

- **Challenge**: Analyze and refactor a poorly written Python script
- **7-category assessment** (5/3/6/3/4/2/2): Balanced analysis across all code quality dimensions
  - **Syntax** (5pts): Python compilation and basic structure
  - **Structure** (3pts): Imports, error handling, logging, type hints
  - **Execution** (6pts): Runtime success and correct output
  - **Quality** (3pts): Code patterns, pathlib usage, context managers
  - **Security** (4pts): Vulnerability detection and safe coding practices
  - **Performance** (2pts): Algorithm efficiency and optimization analysis
  - **Maintainability** (2pts): Code complexity and long-term maintenance
- **Input**: `test_data/process_records.py` (deliberately broken)
- **Expected output**: Clean, working Python script with comprehensive quality analysis

### Prompt 2: Error Detection & Format Conversion (25 points)  

- **Challenge**: Fix a broken YAML file and convert it to JSON
- **7-category assessment** (4/6/8/6/1/0/0): Structure and execution focused evaluation
  - **Syntax** (4pts): YAML and JSON parsing validation
  - **Structure** (6pts): Data integrity and shape preservation
  - **Execution** (8pts): Cross-format equivalence and deep validation
  - **Quality** (6pts): Format standards, indentation, and data type correctness
  - **Security** (1pt): YAML safety and dangerous construct detection
  - **Performance** (0pts): Not applicable for static file analysis
  - **Maintainability** (0pts): Not applicable for configuration files
- **Input**: `test_data/config.yaml` (syntax errors, wrong types)
- **Expected output**: Valid YAML + correctly typed JSON with comprehensive format analysis

### Prompt 3: Data Transformation & Logic (25 points)

- **Challenge**: Implement complex data transformation with error handling
- **7-category assessment** (3/3/12/3/1/1/2): Execution-heavy transformation testing
  - **Syntax** (3pts): File compilation and function loading
  - **Structure** (3pts): Function signature and basic organization
  - **Execution** (12pts): Comprehensive transformation testing with business rules
  - **Quality** (3pts): Error handling patterns and code readability
  - **Security** (1pt): Safe construct usage and input validation
  - **Performance** (1pt): Single-pass processing efficiency
  - **Maintainability** (2pts): Code organization and complexity analysis
- **Input**: `test_data/user_data.json`
- **Expected output**: Function that enriches and validates user data with detailed rule verification

### Prompt 4: API Integration & Robustness (25 points)

- **Challenge**: Write a robust API client with comprehensive error handling
- **7-category assessment** (2/3/7/3/7/2/1): Security-critical API testing with behavioral validation
  - **Syntax** (2pts): File compilation and function existence
  - **Structure** (3pts): Function signature and HTTP request formation
  - **Execution** (7pts): Behavioral testing under mocked conditions
  - **Quality** (3pts): Error messages and documentation standards
  - **Security** (7pts): Bearer token handling, timeout requirements, credential safety
  - **Performance** (2pts): Retry logic and network resilience patterns
  - **Maintainability** (1pt): Code organization and readability
- **Expected output**: Production-ready API synchronization function with comprehensive security analysis

## 🎯 How to Add Your AI Model

1. **Copy the template**

   **Windows (CMD):**
   ```cmd
   xcopy /E /I submissions\template submissions\your_model_name
   ```

   **Windows (PowerShell):**
   ```powershell
   Copy-Item -Recurse submissions\template submissions\your_model_name
   ```

   **macOS/Linux (Bash):**
   ```bash
   cp -r submissions/template submissions/your_model_name
   ```

2. **Present each prompt to your AI model**
   - Show the AI the contents of `test_data/` files (these contain deliberately broken code that needs fixing)
   - Give it the specific prompt from the `prompts/` directory
   - Save the AI's Python code response in the appropriate file

3. **Run the benchmark**

   **All Platforms:**
   ```bash
   python run_benchmark.py --model your_model_name
   ```

## 📊 Understanding results

### Scoring system

- **Each prompt**: 25 points (100 total)
- **Passing threshold**: 60% (15/25 points per prompt)
- **Overall grades**: A (90%+), B (80%+), C (70%+), D (60%+), F (<60%)

**🆕 Enhanced 7-category scoring system:**
- **Security analysis**: SQL injection detection, hardcoded secrets, path traversal, unsafe execution patterns
- **Performance evaluation**: O(n²) algorithm detection, memory usage patterns, efficiency analysis
- **Maintainability metrics**: Function length analysis, code duplication detection, complexity indicators
- **Detailed feedback**: Category-specific rationale with pass/fail breakdown for each check
- **Comprehensive coverage**: All 4 prompts use complete 7-category assessment with prompt-specific emphasis

> **📖 For detailed scoring rubrics and result interpretation, see the `/docs` directory**

### Output files

- `results/latest_results.json` - Complete benchmark data with detailed scoring
- `results/summary_report_TIMESTAMP.txt` - Human-readable summary with enhanced feedback
- `results/comparison_chart_TIMESTAMP.txt` - Visual comparison with progress bars

## 🛠️ Advanced usage

### Test Specific Model Only

**All Platforms:**
```bash
python run_benchmark.py --model gpt4
```

### Custom Directories

**All Platforms:**
```bash
python run_benchmark.py --submissions-dir my_tests --results-dir my_results
```

### Quiet Mode

**All Platforms:**
```bash
python run_benchmark.py --quiet
```

### Key documentation

- **`docs/scoring_rubric.md`** - Complete scoring breakdown and criteria
- **`docs/interpreting_results.md`** - Guide to understanding benchmark results
- **`docs/adding_models.md`** - Step-by-step model submission guide

## 📁 Repository structure

```
AIBugBench/
├── .gitignore                   # Git ignore patterns
├── CHANGELOG.md                 # Version history and changes
├── EXAMPLE_SUBMISSION.md        # Detailed submission example walkthrough
├── QUICKSTART.md                # Fast setup guide for new users
├── README.md                    # This file, main documentation
├── requirements.txt             # Python dependencies
├── run_benchmark.py             # Main entry point - single command to run all tests
├── setup.py                     # Project setup and directory creation script
│
├── benchmark/                   # Core testing framework
│   ├── __init__.py
│   ├── runner.py                # Main test execution logic
│   ├── validators.py            # Validation functions for each prompt
│   ├── scoring.py               # Scoring algorithms and rubrics
│   └── utils.py                 # Helper functions
│
├── prompts/                     # Test case definitions
│   ├── __init__.py
│   ├── prompt_1_refactoring.md
│   ├── prompt_2_yaml_json.md
│   ├── prompt_3_transformation.md
│   └── prompt_4_api_simulation.md
│
├── test_data/                   # Original "broken" files for testing
│   ├── config.yaml              # Deliberately broken YAML
│   ├── process_records.py       # Poorly written Python script
│   ├── user_data.json           # Sample data
│   └── expected_outputs/        # Reference solutions/outputs
│       ├── corrected_config.yaml
│       ├── refactored_process_records.py
│       └── transformed_users_sample.json
│
├── submissions/                 # Where users put their AI model outputs
│   ├── README.md                # Instructions for users
│   ├── example_model/           # Example submission structure
│   │   ├── prompt_1_solution.py
│   │   ├── prompt_2_config_fixed.yaml
│   │   ├── prompt_2_config.json
│   │   ├── prompt_3_transform.py
│   │   └── prompt_4_api_sync.py
│   └── template/                # Empty template for users to copy
│       ├── prompt_1_solution.py
│       ├── prompt_2_config_fixed.yaml
│       ├── prompt_2_config.json
│       ├── prompt_3_transform.py
│       ├── prompt_4_api_sync.py
│       └── README.md
│
├── results/                     # Generated test results and reports
│   ├── latest_results.json
│   ├── detailed_results/
│   └── comparison_charts/
│
├── docs/                        # Additional documentation
│   ├── adding_models.md
│   ├── interpreting_results.md
│   └── scoring_rubric.md
│
└── tests/                       # Unit tests for the framework itself
    ├── test_runner.py
    ├── test_scoring.py
    └── test_validators.py
```
    └── test_runner.py
```

## Contributing

Contributions welcome! Ideas for new prompts:

- Database query optimization
- Algorithm implementation
- Security vulnerability detection
- Performance optimization challenges

## 📝 License

MIT License - Feel free to use this tool for your AI model evaluations.
