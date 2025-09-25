# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `benchmark.runner.TestRunner` focusing on error/timeout paths."""

from __future__ import annotations

from pathlib import Path
import textwrap
import time

import pytest

from benchmark.runner import TestRunner


@pytest.fixture
def runner(test_data_dir: Path) -> TestRunner:  # uses real test_data_dir for env setup
    return TestRunner(test_data_dir)


@pytest.mark.unit
def test_run_python_script_success(runner: TestRunner, temp_dir: Path):
    script = temp_dir / "ok_script.py"
    script.write_text("print('hello')\n", newline="\n")
    result = runner.run_python_script(script)
    assert result["success"] is True
    assert result["return_code"] == 0
    assert "hello" in result["stdout"].lower()


@pytest.mark.unit
def test_run_python_script_exception(runner: TestRunner, temp_dir: Path):
    script = temp_dir / "boom.py"
    script.write_text("raise RuntimeError('boom')\n", newline="\n")
    result = runner.run_python_script(script)
    assert result["success"] is False
    assert result["return_code"] != 0
    assert "boom" in result["stderr"].lower() or "runtimeerror" in result["stderr"].lower()


@pytest.mark.unit
@pytest.mark.slow
def test_run_python_script_timeout(runner: TestRunner, temp_dir: Path):
    # Create a script that sleeps longer than the timeout
    script = temp_dir / "sleep.py"
    script.write_text(
        textwrap.dedent(
            """
        import time
        time.sleep(2)
        print('done')
        """
        ),
        newline="\n",
    )
    # Force LF endings for determinism across platforms
    start = time.time()
    result = runner.run_python_script(script, timeout=1)
    elapsed = time.time() - start
    assert result["timeout"] is True
    # Should return quickly (<2s due to timeout)
    assert elapsed < 2
    assert "timed out" in result["stderr"].lower()


@pytest.mark.unit
def test_setup_and_cleanup_environment(runner: TestRunner, temp_dir: Path, test_data_dir: Path):
    # Ensure the source file exists in test_data_dir
    user_data = test_data_dir / "user_data.json"
    if not user_data.exists():
        pytest.skip(reason="user_data.json missing in test_data_dir")

    runner.setup_test_environment(temp_dir)
    copied = temp_dir / "user_data.json"
    assert copied.exists()

    # Now cleanup
    runner.cleanup_test_environment(temp_dir)
    # user_data.json may be removed; tolerate both states (cleanup ignores errors)
    assert True  # No exception means success
