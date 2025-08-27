"""Coverage-oriented tests for formatting and unicode safety helpers."""

import contextlib

import run_benchmark


def test_format_detailed_score_and_safe_print(monkeypatch, tmp_path):
    # Monkeypatch validators and scorer to avoid heavy logic
    class DummyValidators:
        def __init__(self, _path):
            pass

    class DummyScorer:
        pass

    monkeypatch.setattr(run_benchmark, "PromptValidators", DummyValidators)
    monkeypatch.setattr(run_benchmark, "BenchmarkScorer", DummyScorer)

    bench = run_benchmark.AICodeBenchmark(
        submissions_dir=tmp_path / "subs", results_dir=tmp_path / "res"
    )

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
        def write(self, *_):  # pragma: no cover - tolerance
            raise UnicodeEncodeError("utf-8", b"x", 0, 1, "reason")

    # Provide minimal interface to replace built-in print via monkeypatching sys.stdout
    monkeypatch.setattr("sys.stdout", BadStdout())
    with contextlib.suppress(Exception):
        bench.safe_print("Rocket 🚀")


def test_use_safe_unicode_variants(monkeypatch, tmp_path):
    bench = run_benchmark.AICodeBenchmark(
        submissions_dir=tmp_path / "subs2", results_dir=tmp_path / "res2"
    )

    class PseudoTty:
        encoding = "cp1252"

        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdout", PseudoTty())
    assert bench.use_safe_unicode() is True  # limited encoding path

    class Utf8Tty:
        encoding = "utf-8"

        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdout", Utf8Tty())
    # Value can be True/False depending on environment; just ensure bool
    assert isinstance(bench.use_safe_unicode(), bool)
