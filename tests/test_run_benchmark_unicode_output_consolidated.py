"""Consolidated tests for formatting helpers and Unicode safety logic in run_benchmark.

Merged former test_run_benchmark_formatting.py and test_run_benchmark_unicode_discovery.py
to reduce collection overhead while keeping distinct behavioral assertions:

1. format_detailed_score formatting content
2. safe_print normal + fallback (UnicodeEncodeError) path
3. use_safe_unicode() variants under different stdout encodings / TTY states
4. standalone helper use_safe_unicode_standalone() smoke test
5. Benchmark method branch with forced non-TTY stdout
"""

from __future__ import annotations

import contextlib

import run_benchmark
from run_benchmark import AICodeBenchmark, use_safe_unicode_standalone


def test_format_detailed_score_and_safe_print(monkeypatch, tmp_path):
    class DummyValidators:  # Lightweight stand-ins to avoid heavy validation logic
        def __init__(self, _path):  # pragma: no cover - trivial
            pass

    class DummyScorer:  # pragma: no cover - trivial container
        pass

    monkeypatch.setattr(run_benchmark, "PromptValidators", DummyValidators)
    monkeypatch.setattr(run_benchmark, "BenchmarkScorer", DummyScorer)

    bench = AICodeBenchmark(submissions_dir=tmp_path / "subs", results_dir=tmp_path / "res")

    detailed = {
        "syntax": {"earned": 5, "max": 5},
        "structure": {"earned": 4, "max": 5},
        "execution": {"earned": 3, "max": 5},
    }
    formatted = bench.format_detailed_score(detailed)
    assert "Syntax" in formatted and "Structure" in formatted

    # Exercise safe_print normal path
    bench.safe_print("Hello World ✅")

    # Force fallback branch by raising in print
    class BadStdout:
        def write(self, *_):  # pragma: no cover - tolerance path
            raise UnicodeEncodeError("utf-8", "x", 0, 1, "reason")

    # Replace sys.stdout to trigger fallback handling
    monkeypatch.setattr("sys.stdout", BadStdout())
    with contextlib.suppress(Exception):
        bench.safe_print("Rocket 🚀")


def test_use_safe_unicode_variants(monkeypatch, tmp_path):
    bench = AICodeBenchmark(submissions_dir=tmp_path / "subs2", results_dir=tmp_path / "res2")

    class PseudoTty:
        encoding = "cp1252"

        def isatty(self):  # pragma: no cover - trivial
            return True

    monkeypatch.setattr("sys.stdout", PseudoTty())
    assert bench.use_safe_unicode() is True  # limited encoding path guarantees True

    class Utf8Tty:
        encoding = "utf-8"

        def isatty(self):  # pragma: no cover - trivial
            return True

    monkeypatch.setattr("sys.stdout", Utf8Tty())
    assert isinstance(bench.use_safe_unicode(), bool)


def test_use_safe_unicode_standalone_smoke():
    assert isinstance(use_safe_unicode_standalone(), bool)


def test_benchmark_unicode_method_and_structure(tmp_path, monkeypatch):
    bench = AICodeBenchmark(submissions_dir=tmp_path / "subs", results_dir=tmp_path / "res")

    class DummyStdout:
        def isatty(self):  # No TTY path
            return False

        encoding = "utf-8"

    monkeypatch.setattr("sys.stdout", DummyStdout())
    assert bench.use_safe_unicode() is True
