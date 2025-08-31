"""Secure execution environment for untrusted code (Phase 1 sandbox).

Initial minimal sandbox providing:
- Temporary isolated working directory (aibugbench_*)
- Copy of submission + test_data
- Scrubbed environment (removes sensitive patterns)
- Substituted HOME/TEMP and PYTHONPATH pointing to sandbox
- Resource limits (CPU seconds, address space) where supported
- Helper run_with_limits wrapper using multiprocessing for isolation

Notes:
- Memory limit via RLIMIT_AS may not be enforced on some platforms (Windows / macOS variants).
- Network control not implemented in Phase 1 (flag integration deferred).
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import multiprocessing
import os
from pathlib import Path

try:  # Windows compatibility: resource not available
    import resource  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - platform specific
    resource = None  # type: ignore[assignment]
import shutil
import tempfile
from typing import Any

SENSITIVE_ENV_PATTERNS = [
    "API",
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
    "AWS",
    "AZURE",
    "GOOGLE",
    "OPENAI",
    "ANTHROPIC",
    "DATABASE",
]


class SecureRunner:
    """Execute untrusted code in an isolated temporary environment."""

    def __init__(self, model_name: str, allow_network: bool = False):
        self.model_name = model_name
        self.allow_network = allow_network
        self._original_cwd = Path.cwd()
        self._original_env = os.environ.copy()

    @contextmanager
    def sandbox(self):  # type: ignore[override]
        """Context manager establishing the sandbox directory and environment."""
        temp_dir = Path(tempfile.mkdtemp(prefix="aibugbench_"))
        sandbox_dir = temp_dir / "sandbox"
        submission_dst = sandbox_dir / "submission"
        test_data_dst = sandbox_dir / "test_data"

        try:
            sandbox_dir.mkdir()
            # Copy submission if exists
            submission_src = self._original_cwd / "submissions" / self.model_name
            if submission_src.exists():
                shutil.copytree(submission_src, submission_dst)
            # Copy test_data (read-only fixtures)
            test_data_src = self._original_cwd / "test_data"
            if test_data_src.exists():
                shutil.copytree(test_data_src, test_data_dst)

            # Switch CWD and clean env
            os.chdir(sandbox_dir)
            self._prepare_environment(sandbox_dir)
            yield sandbox_dir
        finally:
            # Restore env and cwd
            os.chdir(self._original_cwd)
            os.environ.clear()
            os.environ.update(self._original_env)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _prepare_environment(self, sandbox_dir: Path) -> None:
        """Scrub sensitive env vars and set controlled vars."""
        for key in list(os.environ):
            upper = key.upper()
            if any(pattern in upper for pattern in SENSITIVE_ENV_PATTERNS):
                os.environ.pop(key, None)

        home_dir = sandbox_dir / "home"
        tmp_dir = sandbox_dir / "temp"
        home_dir.mkdir(exist_ok=True)
        tmp_dir.mkdir(exist_ok=True)

        os.environ.update(
            {
                "HOME": str(home_dir),
                "TEMP": str(tmp_dir),
                "TMP": str(tmp_dir),
                "PYTHONPATH": str(sandbox_dir),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

    def run_with_limits(
        self, func: Callable[..., Any], *args: Any, timeout: int = 30, memory_mb: int = 512
    ) -> Any:
        """Execute func(*args) under CPU & memory limits where supported.

        memory_mb: planned default; future flag --mem will allow override (512/768/1024).
        """

        def target(queue: multiprocessing.Queue):  # type: ignore[type-arg]
            try:
                # Apply CPU limit
                if resource is not None and hasattr(resource, "RLIMIT_CPU"):
                    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                # Apply address space (best-effort)
                if resource is not None and hasattr(resource, "RLIMIT_AS"):
                    bytes_limit = memory_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
                result = func(*args)
                queue.put(("ok", result))
            except Exception as exc:  # Broad exception boundary acceptable at sandbox edge
                queue.put(("err", f"{type(exc).__name__}: {exc}"))

        queue: multiprocessing.Queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=target, args=(queue,))
        process.start()
        process.join(timeout=timeout + 5)

        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutError(f"Execution exceeded {timeout}s limit")

        if queue.empty():
            raise RuntimeError("Sandboxed process ended without result")

        status, payload = queue.get()
        if status == "err":
            raise RuntimeError(f"Sandboxed execution failed: {payload}")
        return payload
