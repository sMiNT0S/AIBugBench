"""Additional light tests hitting unicode safety and discovery summary paths."""

from run_benchmark import AICodeBenchmark, use_safe_unicode_standalone


def test_use_safe_unicode_standalone_smoke():
    # Should return bool without raising
    assert isinstance(use_safe_unicode_standalone(), bool)


def test_benchmark_unicode_method_and_structure(tmp_path, monkeypatch):
    # Point benchmark at empty temp submissions/results to avoid real runs
    bench = AICodeBenchmark(submissions_dir=tmp_path / "subs", results_dir=tmp_path / "res")
    # Force no TTY to exercise safe branch
    class DummyStdout:
        def isatty(self):
            return False
        encoding = "utf-8"
    monkeypatch.setattr("sys.stdout", DummyStdout())
    assert bench.use_safe_unicode() is True
