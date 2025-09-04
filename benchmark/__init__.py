# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
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
    "BenchmarkScorer",
    "PromptValidators",
    "ensure_directories",
    "load_test_data",
]
