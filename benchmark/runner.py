"""
Test runner utilities for the AI Code Benchmark
"""

import contextlib
import os
from pathlib import Path
import subprocess  # Bandit B404/B603: controlled usage; fixed arg list [sys.executable, script]
import sys
import tempfile
from typing import Any


class TestRunner:
    """Handles execution of test scripts and validation."""

    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir

    def run_python_script(
        self,
        script_path: Path,
        args: list | None = None,
        timeout: int = 30
    ) -> dict[str, Any]:
        """Run a Python script and capture output."""
        if args is None:
            args = []

        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "timeout": False,
        }

        try:
            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(script_path.parent)

            # Run the script
            process = subprocess.run(
                [sys.executable, str(script_path), *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script_path.parent,
                env=env,
            )

            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["return_code"] = process.returncode
            result["success"] = process.returncode == 0

        except subprocess.TimeoutExpired:
            result["timeout"] = True
            result["stderr"] = (
                f"Script execution timed out after {timeout} seconds"
            )
        except Exception as e:
            result["stderr"] = f"Execution error: {e!s}"

        return result

    def create_temp_config(self, config_content: str) -> str:
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            temp_file.write(config_content)
            return temp_file.name

    def setup_test_environment(self, target_dir: Path) -> None:
        """Set up test environment by copying necessary files."""
        # Copy user_data.json to target directory
        user_data_src = self.test_data_dir / "user_data.json"
        user_data_dst = target_dir / "user_data.json"

        if user_data_src.exists() and not user_data_dst.exists():
            import shutil

            shutil.copy2(user_data_src, user_data_dst)

    def cleanup_test_environment(self, target_dir: Path) -> None:
        """Clean up temporary test files."""
        temp_files = ["user_data.json", "config.yaml"]

        for filename in temp_files:
            file_path = target_dir / filename
            if file_path.exists():
                with contextlib.suppress(OSError):
                    file_path.unlink()  # Ignore errors during cleanup
