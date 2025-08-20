"""
AI Code Benchmark Package
A comprehensive tool for evaluating AI models' coding capabilities.
"""

__version__ = "1.0.0"
__author__ = "sMiNT0S, Polle"

from .scoring import BenchmarkScorer
from .utils import ensure_directories, load_test_data

# Import main classes for easy access
from .validators import PromptValidators

__all__ = [
    "PromptValidators",
    "BenchmarkScorer",
    "load_test_data",
    "ensure_directories",
]
