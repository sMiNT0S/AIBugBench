"""Lightweight import test for setup.py.

Ensures the module is imported during a default `pytest -q` run so that
regressions (e.g. syntax errors, guard logic) surface without requiring
explicit `--cov=setup` invocation.
"""


def test_setup_module_imports():
    import setup  # import triggers top-level definitions only

    # Guard variable should not trigger main bootstrap automatically
    assert hasattr(setup, "main")
    # AIBUGBENCH_BOOTSTRAP not set, so side-effect directories shouldn't be created here.
