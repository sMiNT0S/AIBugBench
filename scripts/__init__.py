"""Utility and maintenance scripts package for AIBugBench.

This file exists to make the `scripts` directory a proper Python package so
type checkers (mypy) and tooling resolve modules under a single qualified
name (e.g., `scripts.update_requirements_lock`) and avoid duplicate module
discovery.
"""

__all__: list[str] = []
