# tests/test_runner_contract.py

import pytest

from aibugbench.orchestration.runner import BenchmarkRunner


@pytest.mark.xfail(strict=True, reason="Phase 2 orchestrator split pending")
def test_runner_exposes_benchmarkrunner_api():
    # In Phase 0 the stub raises NotImplementedError.
    # This should xfail now; when Phase 2 implements it, it should get XPASS(strict) as reminder to update the test.
    BenchmarkRunner().run_once("p1")
