"""
AI Code Benchmark Package
A comprehensive tool for evaluating AI models' coding capabilities.
"""

__version__ = "1.0.0"
__author__ = "AI Code Benchmark Team"

# Import main classes for easy access
from .validators import PromptValidators
from .scoring import BenchmarkScorer
from .utils import load_test_data, ensure_directories

__all__ = [
    "PromptValidators",
    "BenchmarkScorer",
    "load_test_data",
    "ensure_directories",
]
