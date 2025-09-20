"""Lightweight import test for scripts/bootstrap_repo.py.

Ensures the module is imported during a default `pytest -q` run so that
regressions (e.g. syntax errors, guard logic) surface without requiring
explicit `--cov=bootstrap_repo` invocation.
"""


def test_bootstrap_module_imports():
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import bootstrap_repo  # import triggers top-level definitions only

    # Guard variable should not trigger main bootstrap automatically
    assert hasattr(bootstrap_repo, "main")
    # AIBUGBENCH_BOOTSTRAP not set, so side-effect directories shouldn't be created here.
