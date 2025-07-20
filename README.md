# RealityCheckBench 🤖

A comprehensive benchmarking tool for evaluating AI models' code generation, refactoring, and problem-solving capabilities. Test any AI model's programming skills across 4 distinct challenges!

## Requirements

```
pyyaml>=6.0
requests>=2.25.0
```

## 🚀 Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/sMiNT0S/RealityCheckBench.git
   cd RealityCheckBench
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up virtual environment (strongly recommended)**

   For consistent and fair benchmark results across all users, we **strongly recommend** using a virtual environment. This ensures:
   - All tests run with the same dependency versions
   - No interference from system-installed packages
   - Reproducible results regardless of your local Python setup
   - Prevention of package conflicts that could affect scoring

   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   # Install dependencies in the virtual environment
   pip install -r requirements.txt
   ```

   > **Note**: Always activate your virtual environment before running benchmarks to ensure fair and consistent results.

4. **Run the benchmark**

   ```bash
   python run_benchmark.py
   ```

## 📋 What This Tool Tests

The benchmark consists of 4 progressively challenging prompts that test different AI capabilities:

### Prompt 1: Code Refactoring & Analysis (25 points)

- **Challenge**: Analyze and refactor a poorly written Python script
- **Tests**: Code quality, PEP8 compliance, error handling, efficiency
- **Input**: `test_data/process_records.py` (deliberately broken)
- **Expected Output**: Clean, working Python script

### Prompt 2: Error Detection & Format Conversion (25 points)  

- **Challenge**: Fix a broken YAML file and convert it to JSON
- **Tests**: Debugging skills, data format handling, type conversion
- **Input**: `test_data/config.yaml` (syntax errors, wrong types)
- **Expected Output**: Valid YAML + correctly typed JSON

### Prompt 3: Data Transformation & Logic (25 points)

- **Challenge**: Implement complex data transformation with error handling
- **Tests**: Programming logic, edge case handling, type safety
- **Input**: `test_data/user_data.json`
- **Expected Output**: Function that enriches and validates user data

### Prompt 4: API Integration & Robustness (25 points)

- **Challenge**: Write a robust API client with comprehensive error handling
- **Tests**: Real-world programming, error scenarios, best practices
- **Expected Output**: Production-ready API synchronization function

## 🎯 How to Add Your AI Model

1. **Copy the template**

   ```bash
   cp -r submissions/template submissions/your_model_name
   ```

2. **Present each prompt to your AI model**
   - Show the AI the contents of `test_data/` files
   - Give it the specific prompt (see `prompts/` directory)
   - Save the AI's response in the appropriate file

3. **Run the benchmark**

   ```bash
   python run_benchmark.py --model your_model_name
   ```

## 📊 Understanding Results

### Scoring System

- **Each prompt**: 25 points (100 total)
- **Passing threshold**: 60% (15/25 points per prompt)
- **Overall grades**: A (90%+), B (80%+), C (70%+), D (60%+), F (<60%)

### Output Files

- `results/latest_results.json` - Complete benchmark data
- `results/summary_report_TIMESTAMP.txt` - Human-readable summary  
- `results/comparison_chart_TIMESTAMP.txt` - Visual comparison

## 🛠️ Advanced Usage

### Test Specific Model Only

```bash
python run_benchmark.py --model gpt4
```

### Custom Directories

```bash
python run_benchmark.py --submissions-dir my_tests --results-dir my_results
```

### Quiet Mode

```bash
python run_benchmark.py --quiet
```

## 📁 Repository Structure

```
RealityCheckBench/
├── README.md                    # This file, main documentation
├── requirements.txt             # Python dependencies
├── run_benchmark.py             # Main entry point - single command to run all tests
├── setup.py                     # Package installation (optional)
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
│
├── results/                     # Generated test results and reports
│   ├── latest_results.json
│   ├── detailed_reports/
│   └── comparison_charts/
│
├── docs/                        # Additional documentation
│   ├── scoring_rubric.md
│   ├── adding_models.md
│   └── interpreting_results.md
│
└── tests/                       # Unit tests for the framework itself
    ├── test_validators.py
    ├── test_scoring.py
    └── test_runner.py
```

## Contributing

Contributions welcome! Ideas for new prompts:

- Database query optimization
- Algorithm implementation
- Security vulnerability detection
- Performance optimization challenges

## 📝 License

MIT License - Feel free to use this tool for your AI model evaluations!
