# Model Submissions

Three-tier structure for code quality and security:

## reference_implementations/

Production-quality reference implementations. (This is roughly the expected behavior/output)

- Full linting and security scanning
- Complete test coverage required
- Used as baseline for comparison

## templates/

Starting templates for new model implementations.

- Basic safety checks only
- Minimal viable examples

## user_submissions/

Your AI model implementations.

- Excluded from automated quality checks
- Not tracked in git by default

## Directory Structure

```
submissions/
├── reference_implementations/
│   └── example_model/
│       └── [prompt solutions]
├── templates/
│   └── template/
│       └── [prompt templates]
└── user_submissions/
    └── [your models here]
```

## Getting Started

1. Copy the template directory to user_submissions with your model name
2. Implement solutions for each prompt
3. Run the benchmark against your model
4. Review results in the results/ directory

For detailed submission instructions, see [submissions/templates/template/README.md](templates/template/README.md).
