import importlib


def test_imports_smoke():
    """Test that all benchmark modules can be imported without errors."""
    for mod in [
        "benchmark",
        "benchmark.platform_validator",
        "benchmark.runner",
        "benchmark.scoring",
        "benchmark.utils",
        "benchmark.validators",
    ]:
        importlib.import_module(mod)
