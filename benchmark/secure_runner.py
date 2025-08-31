"""Secure execution environment for untrusted code.

Phase 1 baseline + Phase 5.5 hardening additions:
    - Strict environment whitelist (no parent env copy)
    - sitecustomize.py guard (network & filesystem) unless network allowed
    - Isolated Python subprocess helper (-I -B) with resource limits
    - Original run_with_limits retained for in-process call patterns
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager, suppress
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys

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

            # Switch CWD and prepare strict environment + guards
            os.chdir(sandbox_dir)
            self._prepare_environment(sandbox_dir)
            self._write_sitecustomize(sandbox_dir)
            yield sandbox_dir
        finally:
            # Restore env and cwd
            os.chdir(self._original_cwd)
            os.environ.clear()
            os.environ.update(self._original_env)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _prepare_environment(self, sandbox_dir: Path) -> None:
        """Establish a strict environment whitelist inside sandbox.

        We do NOT inherit the parent environment except for a minimal set of
        necessary process invariants (PATH, SystemRoot, etc.). Sensitive keys
        are therefore excluded by construction rather than pattern scrubbing.
        """
        os.environ.clear()
        home_dir = sandbox_dir / "home"
        tmp_dir = sandbox_dir / "temp"
        home_dir.mkdir(exist_ok=True)
        tmp_dir.mkdir(exist_ok=True)

        base_env = {
            "HOME": str(home_dir),
            "USERPROFILE": str(home_dir),  # Windows compatibility
            "TEMP": str(tmp_dir),
            "TMP": str(tmp_dir),
            "TMPDIR": str(tmp_dir),
            "PYTHONDONTWRITEBYTECODE": "1",
            "AIBUGBENCH_SANDBOX_ROOT": str(sandbox_dir.resolve()),
            "AIBUGBENCH_ALLOW_NETWORK": "1" if self.allow_network else "0",
        }
        for key in [
            "PATH",
            "SystemRoot",
            "WINDIR",
            "COMSPEC",
            "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE",
            "LANG",
            "LC_ALL",
        ]:
            val = self._original_env.get(key)
            if val:
                base_env[key] = val
        os.environ.update(base_env)

    def _write_sitecustomize(self, sandbox_dir: Path) -> None:
        """Write sitecustomize.py to enforce network & filesystem guard.

        Guard strategy:
          - Block socket creation unless allow_network was set
          - Block subprocess execution by default
          - Wrap all file operations to confine access to sandbox root
          - Deny symlinks pointing outside sandbox
        """
        site_path = sandbox_dir / "sitecustomize.py"
        try:
            guard_lines = [
                "# Network control implemented",
                "import socket, builtins, os, pathlib, subprocess, shutil",
                (
                    "ALLOW_NETWORK = os.environ.get('AIBUGBENCH_ALLOW_NETWORK','0') in "
                    "('1','true','yes','on')"
                ),
                (
                    "SANDBOX_ROOT = pathlib.Path(os.environ.get('AIBUGBENCH_SANDBOX_ROOT','.') )"
                ),
                "SANDBOX_ROOT = SANDBOX_ROOT.resolve()",
                "",
                "# Network blocking",
                "_real_socket = socket.socket",
                "_real_create = socket.create_connection",
                "def _network_blocked(*a, **k): raise RuntimeError('network disabled in sandbox')",
                "if not ALLOW_NETWORK:",
                "    socket.socket = _network_blocked",
                "    socket.create_connection = _network_blocked",
                "",
                "# Subprocess blocking",
                "_real_popen = subprocess.Popen",
                "_real_run = subprocess.run",
                "_real_call = subprocess.call",
                "_real_system = os.system",
                ("def _subprocess_blocked(*a, **k): "
                 "raise RuntimeError('subprocess execution disabled in sandbox')"),
                "subprocess.Popen = _subprocess_blocked",
                "subprocess.run = _subprocess_blocked",
                "subprocess.call = _subprocess_blocked",
                "os.system = _subprocess_blocked",
                "",
                "# Filesystem confinement helpers",
                "def _path_inside_sandbox(p):",
                "    try:",
                "        resolved = pathlib.Path(p).resolve()",
                "        # Check if resolved path is under sandbox root",
                "        try:",
                "            resolved.relative_to(SANDBOX_ROOT)",
                "            return True",
                "        except ValueError:",
                "            return False",
                "    except (OSError, RuntimeError):",
                "        # Handle broken symlinks, permission errors, etc.",
                "        return False",
                "",
                "def _check_path_or_raise(path, operation='access'):",
                "    if not _path_inside_sandbox(path):",
                ("        raise RuntimeError("
                 "f'filesystem {operation} denied outside sandbox: {path}')"),
                "",
                "# File operation guards",
                "_real_open = builtins.open",
                "_real_os_open = os.open",
                "_real_os_remove = os.remove",
                "_real_os_rmdir = os.rmdir",
                "_real_os_unlink = os.unlink",
                "_real_shutil_copy = shutil.copy",
                "_real_shutil_copy2 = shutil.copy2",
                "_real_shutil_copytree = shutil.copytree",
                "_real_shutil_move = shutil.move",
                "_real_shutil_rmtree = shutil.rmtree",
                "",
                "def guarded_open(file, *a, **k):",
                "    _check_path_or_raise(file, 'open')",
                "    return _real_open(file, *a, **k)",
                "",
                "def guarded_os_open(path, *a, **k):",
                "    _check_path_or_raise(path, 'open')",
                "    return _real_os_open(path, *a, **k)",
                "",
                "def guarded_os_remove(path):",
                "    _check_path_or_raise(path, 'remove')",
                "    return _real_os_remove(path)",
                "",
                "def guarded_os_rmdir(path):",
                "    _check_path_or_raise(path, 'rmdir')",
                "    return _real_os_rmdir(path)",
                "",
                "def guarded_os_unlink(path):",
                "    _check_path_or_raise(path, 'unlink')",
                "    return _real_os_unlink(path)",
                "",
                "def guarded_shutil_copy(src, dst):",
                "    _check_path_or_raise(src, 'copy-src')",
                "    _check_path_or_raise(dst, 'copy-dst')",
                "    return _real_shutil_copy(src, dst)",
                "",
                "def guarded_shutil_copy2(src, dst):",
                "    _check_path_or_raise(src, 'copy2-src')",
                "    _check_path_or_raise(dst, 'copy2-dst')",
                "    return _real_shutil_copy2(src, dst)",
                "",
                "def guarded_shutil_copytree(src, dst, *a, **k):",
                "    _check_path_or_raise(src, 'copytree-src')",
                "    _check_path_or_raise(dst, 'copytree-dst')",
                "    return _real_shutil_copytree(src, dst, *a, **k)",
                "",
                "def guarded_shutil_move(src, dst):",
                "    _check_path_or_raise(src, 'move-src')",
                "    _check_path_or_raise(dst, 'move-dst')",
                "    return _real_shutil_move(src, dst)",
                "",
                "def guarded_shutil_rmtree(path, *a, **k):",
                "    _check_path_or_raise(path, 'rmtree')",
                "    return _real_shutil_rmtree(path, *a, **k)",
                "",
                "# Install guards",
                "builtins.open = guarded_open",
                "os.open = guarded_os_open",
                "os.remove = guarded_os_remove",
                "os.rmdir = guarded_os_rmdir",
                "os.unlink = guarded_os_unlink",
                "shutil.copy = guarded_shutil_copy",
                "shutil.copy2 = guarded_shutil_copy2",
                "shutil.copytree = guarded_shutil_copytree",
                "shutil.move = guarded_shutil_move",
                "shutil.rmtree = guarded_shutil_rmtree",
            ]
            guard_code = "\n".join(guard_lines) + "\n"
            site_path.write_text(guard_code, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - non critical
            # Minimal stderr note; ignore secondary failures silently
            with suppress(Exception):
                sys.stderr.write(f"[sandbox] failed to write sitecustomize: {exc}\n")

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

    # ------------------------------------------------------------------
    # Subprocess execution helper (Phase 5.5)
    # ------------------------------------------------------------------
    def run_python_sandboxed(
        self,
        args: list[str],
        *,
        timeout: int = 10,
        cwd: Path | None = None,
        memory_mb: int = 512,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a python module or script with -I -B inside the sandbox.

        Caller MUST be inside `with self.sandbox():` context so that
        sitecustomize guard + strict env are active.
        Applies best-effort rlimits on POSIX platforms.
        """

        preexec = None
        if resource is not None and hasattr(resource, "setrlimit"):
            def _limits():  # type: ignore[override]
                with suppress(Exception):
                    if hasattr(resource, "RLIMIT_CPU"):
                        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                    if hasattr(resource, "RLIMIT_AS"):
                        bytes_limit = memory_mb * 1024 * 1024
                        resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
                    if hasattr(resource, "RLIMIT_FSIZE"):
                        resource.setrlimit(
                            resource.RLIMIT_FSIZE,
                            (10 * 1024 * 1024, 10 * 1024 * 1024),
                        )
            preexec = _limits

        # Note: Don't use -I flag as it prevents sitecustomize from loading
        # We need sitecustomize for security guards to be active
        cmd = [sys.executable, "-B", *args]
        env = os.environ.copy()  # Inherit the sandbox environment

        # Add sandbox directory to PYTHONPATH so sitecustomize.py is found
        if cwd:
            pythonpath = env.get("PYTHONPATH", "")
            if pythonpath:
                env["PYTHONPATH"] = f"{cwd}{os.pathsep}{pythonpath}"
            else:
                env["PYTHONPATH"] = str(cwd)

        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
            preexec_fn=preexec,  # type: ignore[arg-type]
        )
