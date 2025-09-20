# AIBugBench

AIBugBench benchmarks AI-generated code across four progressive challenges with a 7-category scoring system (syntax, structure, execution, quality, security, performance, maintainability). It uses deliberately flawed fixtures to test real corrective ability, not pattern copying. Results are deterministic and saved locally.

## Quick Navigation

**New Users** → Start with [Getting Started](getting-started.md) for setup and your first benchmark  
**Model Developers** → See [Developer Guide](developer-guide.md) for adding and testing AI models  
**Power Users** → Check [User Guide](user-guide.md) for advanced usage and result interpretation  
**API Integration** → Reference [API Documentation](api-reference.md) for programmatic usage

## Documentation

### Core Guides

- **[Getting Started](getting-started.md)** - Setup and first benchmark run
- **[User Guide](user-guide.md)** - Running benchmarks and interpreting results
- **[Developer Guide](developer-guide.md)** - Adding and testing AI models
- **[API Reference](api-reference.md)** - CLI and Python API documentation

### Understanding the System

- **[Architecture](architecture.md)** - System design and components
- **[Scoring Methodology](scoring-methodology.md)** - How the 7-category scoring works
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Sabotage Notes](sabotage-notes.md)** - Debug patterns and test hazards

### Project Information

- **[Contributing](contributing.md)** - Development workflow and contribution guidelines
- **[Code of Conduct](code-of-conduct.md)** - Community guidelines
- **[Security](security.md)** - Security policy and reporting
- **[License](license.md)** - MIT license information

## Quick Start

```bash
# Install and run your first benchmark
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python scripts/bootstrap_repo.py
python run_benchmark.py --model example_model
```

See [Getting Started](getting-started.md) for detailed setup instructions.
