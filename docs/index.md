# AIBugBench

<!-- markdownlint-disable MD033 -->
<div class="mdx-hero" markdown>

**Deterministic, local AI code benchmarking — sandboxed and reproducible.**

Compare models on the same four tasks. Score across seven dimensions. No network. No vibes. Just receipts.

<p>
  <a class="md-button md-button--primary" href="{{ 'getting-started.md' | relative_url }}">Get started</a>
  <a class="md-button" href="{{ 'scoring-methodology.md' | relative_url }}">How scoring works</a>
  <a class="md-button" href="{{ 'architecture.md' | relative_url }}">Architecture</a>
  <a class="md-button" href="{{ 'api-reference.md' | relative_url }}">API</a>
</p>

<p>
  <img alt="CI" src="https://github.com/sMiNT0S/AIBugBench/actions/workflows/ci.yml/badge.svg?branch=main">
  <a title="Codecov trend"><img alt="codecov trend" src="https://codecov.io/github/smint0s/aibugbench/graph/badge.svg?token=0G9SHU4AZ7"></a>
  <img alt="safety" src="https://img.shields.io/endpoint?url=https://smint0s.github.io/AIBugBench/badges/safety.json">
</p>
</div>

## Pick your path

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg } **New users**  
  *Install, run your first benchmark, read the scorecard.*  
  [:octicons-arrow-right-16: Getting Started]({{ 'getting-started.md' | relative_url }}){ .md-button }

- :material-robot-outline:{ .lg } **Model authors**  
  *Add a model folder and wire outputs.*  
  [:octicons-arrow-right-16: Developer Guide]({{ 'developer-guide.md' | relative_url }}){ .md-button }

- :material-chart-box-outline:{ .lg } **Power users**  
  *CLI flags, artifacts, diffs, comparisons.*  
  [:octicons-arrow-right-16: User Guide]({{ 'user-guide.md' | relative_url }}){ .md-button }

- :material-shield-check:{ .lg } **Security first**  
  *Sandbox, audit, and guardrails at a glance.*  
  [:octicons-arrow-right-16: Security]({{ 'security.md' | relative_url }}){ .md-button }

</div>

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

## Quick start

```bash
# Install and run your first benchmark
git clone https://github.com/sMiNT0S/AIBugBench.git
cd AIBugBench
python scripts/bootstrap_repo.py
python run_benchmark.py --model example_model
```

See [Getting Started]({{ 'getting-started.md' | relative_url }} "Step-by-step install") for detailed setup.

## Code annotations example

```python
def grade(score: float) -> str:  # (1)!
    return "pass" if score >= 0.6 else "fail"
```

1. Pass/fail threshold is configurable in the CLI and documented in [Scoring Methodology]({{ 'scoring-methodology.md' | relative_url }}).
