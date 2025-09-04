# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Secure execution environment for untrusted code.

Phase 1 baseline + Phase 5.5 hardening additions:
    - Strict environment whitelist (no parent env copy)
    - sitecustomize.py guard (network & filesystem) unless network allowed
    - Isolated Python subprocess helper (-B) with resource limits
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
    import resource
except ImportError:  # pragma: no cover - platform specific
    resource = None

# Windows Job Objects for real resource limits
try:  # Windows-specific imports
    import win32api
    import win32job

    WINDOWS_JOB_SUPPORT = True
except ImportError:  # pragma: no cover - platform specific
    WINDOWS_JOB_SUPPORT = False

# ---- Platform RLIMIT typing shim (Windows-safe) ----
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

try:
    import resource as _resource  # POSIX only
except Exception:
    _resource = None

if TYPE_CHECKING:
    # Satisfy the type checker; actual values set at runtime below
    RLIMIT_CPU: int
    RLIMIT_AS: int
    RLIMIT_FSIZE: int
else:
    RLIMIT_CPU = getattr(_resource, "RLIMIT_CPU", 0) if _resource else 0
    RLIMIT_AS = getattr(_resource, "RLIMIT_AS", 0) if _resource else 0
    RLIMIT_FSIZE = getattr(_resource, "RLIMIT_FSIZE", 0) if _resource else 0

import shutil
import tempfile

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
    def sandbox(self) -> Iterator[Any]:
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
                "# Security guards - automatically generated by SecureRunner",
                "# WARNING: These guards prevent access outside sandbox",
                "import socket, builtins, os, pathlib, subprocess, shutil",
                (
                    "ALLOW_NETWORK = os.environ.get('AIBUGBENCH_ALLOW_NETWORK','0') in "
                    "('1','true','yes','on')"
                ),
                ("SANDBOX_ROOT = pathlib.Path(os.environ.get('AIBUGBENCH_SANDBOX_ROOT','.') )"),
                "SANDBOX_ROOT = SANDBOX_ROOT.resolve()",
                "",
                "# Install security guards using closures to hide real functions",
                "def _install_guards():",
                "    # Capture originals in closure scope before patching",
                "    real_socket = socket.socket",
                "    real_create_connection = socket.create_connection",
                "    real_popen = subprocess.Popen",
                "    real_run = subprocess.run",
                "    real_call = subprocess.call",
                "    real_system = os.system",
                "    # Capture exec/spawn/fork family functions",
                "    real_execv = getattr(os, 'execv', None)",
                "    real_execve = getattr(os, 'execve', None)",
                "    real_execvp = getattr(os, 'execvp', None)",
                "    real_execvpe = getattr(os, 'execvpe', None)",
                "    real_spawnv = getattr(os, 'spawnv', None)",
                "    real_spawnve = getattr(os, 'spawnve', None)",
                "    real_spawnvp = getattr(os, 'spawnvp', None)",
                "    real_spawnvpe = getattr(os, 'spawnvpe', None)",
                "    real_posix_spawn = getattr(os, 'posix_spawn', None)",
                "    real_posix_spawnp = getattr(os, 'posix_spawnp', None)",
                "    real_fork = getattr(os, 'fork', None)",
                "    real_forkpty = getattr(os, 'forkpty', None)",
                "    # Capture dynamic code execution functions",
                "    real_eval = builtins.eval",
                "    real_exec = builtins.exec",
                "    real_compile = builtins.compile",
                "    real_import = builtins.__import__",
                "    # Capture dangerous modules and functions",
                "    import importlib, sys, types, marshal, pickle, codecs",
                "    real_importlib_reload = getattr(importlib, 'reload', None)",
                "    real_marshal_loads = getattr(marshal, 'loads', None)",
                "    real_pickle_loads = getattr(pickle, 'loads', None)",
                "    real_codecs_decode = getattr(codecs, 'decode', None)",
                "    try:",
                "        import ctypes",
                "        real_ctypes_cdll = getattr(ctypes, 'CDLL', None)",
                "        real_ctypes_windll = getattr(ctypes, 'WinDLL', None)",
                "        real_ctypes_oledll = getattr(ctypes, 'OleDLL', None)",
                "        ctypes_available = True",
                "    except ImportError:",
                "        ctypes_available = False",
                "    real_open = builtins.open",
                "    real_os_open = os.open",
                "    real_os_remove = os.remove",
                "    real_os_rmdir = os.rmdir",
                "    real_os_unlink = os.unlink",
                "    # Capture directory listing functions",
                "    real_listdir = os.listdir",
                "    real_scandir = getattr(os, 'scandir', None)",
                "    real_shutil_copy = shutil.copy",
                "    real_shutil_copy2 = shutil.copy2",
                "    real_shutil_copytree = shutil.copytree",
                "    real_shutil_move = shutil.move",
                "    real_shutil_rmtree = shutil.rmtree",
                "",
                "    # Path validation helpers",
                "    def _path_inside_sandbox(p):",
                "        try:",
                "            resolved = pathlib.Path(p).resolve()",
                "            # Check if resolved path is under sandbox root",
                "            try:",
                "                resolved.relative_to(SANDBOX_ROOT)",
                "                return True",
                "            except ValueError:",
                "                return False",
                "        except (OSError, RuntimeError):",
                "            # Handle broken symlinks, permission errors, etc.",
                "            return False",
                "",
                "    def _check_path_or_raise(path, operation='access'):",
                "        if not _path_inside_sandbox(path):",
                (
                    "            raise RuntimeError("
                    "f'filesystem {operation} denied outside sandbox: {path}')"
                ),
                "",
                "    # Blocking functions",
                "    def _network_blocked(*a, **k):",
                "        raise RuntimeError('network disabled in sandbox')",
                "",
                "    def _subprocess_blocked(*a, **k):",
                "        raise RuntimeError('subprocess execution disabled in sandbox')",
                "",
                "    def _process_blocked(*a, **k):",
                "        raise RuntimeError('process spawning/exec disabled in sandbox')",
                "",
                "    def _dynamic_code_blocked(*a, **k):",
                "        raise RuntimeError('dynamic code execution disabled in sandbox')",
                "",
                "    def _import_reload_blocked(*a, **k):",
                "        raise RuntimeError('module reloading disabled in sandbox')",
                "",
                "    def _dangerous_deserialization_blocked(*a, **k):",
                "        raise RuntimeError('dangerous deserialization disabled in sandbox')",
                "",
                "    def _memory_manipulation_blocked(*a, **k):",
                "        raise RuntimeError('memory manipulation disabled in sandbox')",
                "",
                "    def _protected_import(name, *a, **k):",
                "        # Allow normal imports but block dangerous ones",
                "        dangerous_modules = {'ctypes', 'marshal', 'pickle', '_ctypes'}",
                "        is_dangerous = (name in dangerous_modules or ",
                "                       (isinstance(name, str) and name.startswith('ctypes.')))",
                "        if is_dangerous:",
                "            raise RuntimeError(",
                "                f'import of dangerous module {name} disabled in sandbox')",
                "        return real_import(name, *a, **k)",
                "",
                "    def _directory_list_blocked(path, *a, **k):",
                "        _check_path_or_raise(path, 'directory-list')",
                "        # This is a placeholder - actual implementation handled separately",
                "        pass",
                "",
                "    def guarded_listdir(path, *a, **k):",
                "        _check_path_or_raise(path, 'listdir')",
                "        return real_listdir(path, *a, **k)",
                "",
                "    def guarded_scandir(path='.', *a, **k):",
                "        _check_path_or_raise(path, 'scandir')",
                "        return real_scandir(path, *a, **k) if real_scandir else None",
                "",
                "    # Guarded file operations using closure-captured originals",
                "    def guarded_open(file, *a, **k):",
                "        _check_path_or_raise(file, 'open')",
                "        return real_open(file, *a, **k)",
                "",
                "    def guarded_os_open(path, *a, **k):",
                "        _check_path_or_raise(path, 'open')",
                "        return real_os_open(path, *a, **k)",
                "",
                "    def guarded_os_remove(path):",
                "        _check_path_or_raise(path, 'remove')",
                "        return real_os_remove(path)",
                "",
                "    def guarded_os_rmdir(path):",
                "        _check_path_or_raise(path, 'rmdir')",
                "        return real_os_rmdir(path)",
                "",
                "    def guarded_os_unlink(path):",
                "        _check_path_or_raise(path, 'unlink')",
                "        return real_os_unlink(path)",
                "",
                "    def guarded_shutil_copy(src, dst):",
                "        _check_path_or_raise(src, 'copy-src')",
                "        _check_path_or_raise(dst, 'copy-dst')",
                "        return real_shutil_copy(src, dst)",
                "",
                "    def guarded_shutil_copy2(src, dst):",
                "        _check_path_or_raise(src, 'copy2-src')",
                "        _check_path_or_raise(dst, 'copy2-dst')",
                "        return real_shutil_copy2(src, dst)",
                "",
                "    def guarded_shutil_copytree(src, dst, *a, **k):",
                "        _check_path_or_raise(src, 'copytree-src')",
                "        _check_path_or_raise(dst, 'copytree-dst')",
                "        return real_shutil_copytree(src, dst, *a, **k)",
                "",
                "    def guarded_shutil_move(src, dst):",
                "        _check_path_or_raise(src, 'move-src')",
                "        _check_path_or_raise(dst, 'move-dst')",
                "        return real_shutil_move(src, dst)",
                "",
                "    def guarded_shutil_rmtree(path, *a, **k):",
                "        _check_path_or_raise(path, 'rmtree')",
                "        return real_shutil_rmtree(path, *a, **k)",
                "",
                "    # Install network guards",
                "    if not ALLOW_NETWORK:",
                "        socket.socket = _network_blocked",
                "        socket.create_connection = _network_blocked",
                "",
                "    # Install subprocess guards",
                "    subprocess.Popen = _subprocess_blocked",
                "    subprocess.run = _subprocess_blocked",
                "    subprocess.call = _subprocess_blocked",
                "    os.system = _subprocess_blocked",
                "",
                "    # Install process exec/spawn/fork guards",
                "    if real_execv: os.execv = _process_blocked",
                "    if real_execve: os.execve = _process_blocked",
                "    if real_execvp: os.execvp = _process_blocked",
                "    if real_execvpe: os.execvpe = _process_blocked",
                "    if real_spawnv: os.spawnv = _process_blocked",
                "    if real_spawnve: os.spawnve = _process_blocked",
                "    if real_spawnvp: os.spawnvp = _process_blocked",
                "    if real_spawnvpe: os.spawnvpe = _process_blocked",
                "    if real_posix_spawn: os.posix_spawn = _process_blocked",
                "    if real_posix_spawnp: os.posix_spawnp = _process_blocked",
                "    if real_fork: os.fork = _process_blocked",
                "    if real_forkpty: os.forkpty = _process_blocked",
                "",
                "    # Install dynamic code execution guards",
                "    builtins.eval = _dynamic_code_blocked",
                "    builtins.exec = _dynamic_code_blocked",
                "    builtins.compile = _dynamic_code_blocked",
                "    builtins.__import__ = _protected_import",
                "",
                "    # Install import manipulation guards",
                "    if real_importlib_reload: importlib.reload = _import_reload_blocked",
                "",
                "    # Install dangerous deserialization guards",
                "    if real_marshal_loads: marshal.loads = _dangerous_deserialization_blocked",
                "    if real_pickle_loads: pickle.loads = _dangerous_deserialization_blocked",
                "",
                "    # Install memory manipulation guards",
                "    if ctypes_available:",
                "        if real_ctypes_cdll: ctypes.CDLL = _memory_manipulation_blocked",
                "        if real_ctypes_windll: ctypes.WinDLL = _memory_manipulation_blocked",
                "        if real_ctypes_oledll: ctypes.OleDLL = _memory_manipulation_blocked",
                "",
                "    # Install filesystem guards",
                "    builtins.open = guarded_open",
                "    os.open = guarded_os_open",
                "    os.remove = guarded_os_remove",
                "    os.rmdir = guarded_os_rmdir",
                "    os.unlink = guarded_os_unlink",
                "    # Install directory listing guards",
                "    os.listdir = guarded_listdir",
                "    if real_scandir: os.scandir = guarded_scandir",
                "    shutil.copy = guarded_shutil_copy",
                "    shutil.copy2 = guarded_shutil_copy2",
                "    shutil.copytree = guarded_shutil_copytree",
                "    shutil.move = guarded_shutil_move",
                "    shutil.rmtree = guarded_shutil_rmtree",
                "",
                "# Install all guards and clean up namespace",
                "_install_guards()",
                "del _install_guards  # Remove installer function from module scope",
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

        def target(queue: multiprocessing.Queue[tuple[str, Any]]) -> None:
            try:
                # Apply CPU limit
                if resource and hasattr(resource, "setrlimit") and hasattr(resource, "RLIMIT_CPU"):
                    resource.setrlimit(RLIMIT_CPU, (timeout, timeout))
                # Apply address space (best-effort)
                if resource and hasattr(resource, "setrlimit") and hasattr(resource, "RLIMIT_AS"):
                    bytes_limit = memory_mb * 1024 * 1024
                    resource.setrlimit(RLIMIT_AS, (bytes_limit, bytes_limit))
                result = func(*args)
                queue.put(("ok", result))
            except Exception as exc:  # Broad exception boundary acceptable at sandbox edge
                queue.put(("err", f"{type(exc).__name__}: {exc}"))

        queue: multiprocessing.Queue[tuple[str, Any]] = multiprocessing.Queue()
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
        """Execute a python module or script with -B inside the sandbox.

        Caller MUST be inside `with self.sandbox():` context so that
        sitecustomize guard + strict env are active.
        Applies resource limits: rlimits on POSIX, Job Objects on Windows.
        """

        # Use -B flag only: avoids .pyc files but allows sitecustomize to load
        # The isolation flag would prevent sitecustomize loading entirely, breaking security guards
        # Instead rely on PYTHONPATH control and environment scrubbing for isolation
        cmd = [sys.executable, "-B", *args]
        env = os.environ.copy()  # Inherit the sandbox environment

        # Add sandbox directory to PYTHONPATH so sitecustomize.py is found
        # Place it first for priority, ensuring our security guards load
        if cwd:
            pythonpath = env.get("PYTHONPATH", "")
            if pythonpath:
                env["PYTHONPATH"] = f"{cwd}{os.pathsep}{pythonpath}"
            else:
                env["PYTHONPATH"] = str(cwd)

        # Apply resource limits based on platform
        if WINDOWS_JOB_SUPPORT:
            return self._run_with_job_objects(
                cmd, cwd=cwd, env=env, timeout=timeout, memory_mb=memory_mb
            )
        else:
            # POSIX: use traditional rlimits via preexec_fn
            preexec = None
            if resource is not None and hasattr(resource, "setrlimit"):

                def _limits() -> None:
                    with suppress(Exception):
                        has_setrlimit_cpu = (
                            resource
                            and hasattr(resource, "setrlimit")
                            and hasattr(resource, "RLIMIT_CPU")
                        )
                        if has_setrlimit_cpu and isinstance(RLIMIT_CPU, int) and RLIMIT_CPU:
                            # Guarded: RLIMIT_CPU may be 0 placeholder on non-POSIX
                            resource.setrlimit(RLIMIT_CPU, (timeout, timeout))  # type: ignore[attr-defined]
                        has_setrlimit_as = (
                            resource
                            and hasattr(resource, "setrlimit")
                            and hasattr(resource, "RLIMIT_AS")
                        )
                        if has_setrlimit_as and isinstance(RLIMIT_AS, int) and RLIMIT_AS:
                            bytes_limit = memory_mb * 1024 * 1024
                            resource.setrlimit(RLIMIT_AS, (bytes_limit, bytes_limit))  # type: ignore[attr-defined]
                        has_setrlimit_fsize = (
                            resource
                            and hasattr(resource, "setrlimit")
                            and hasattr(resource, "RLIMIT_FSIZE")
                        )
                        if has_setrlimit_fsize and isinstance(RLIMIT_FSIZE, int) and RLIMIT_FSIZE:
                            resource.setrlimit(  # type: ignore[attr-defined]
                                RLIMIT_FSIZE,
                                (10 * 1024 * 1024, 10 * 1024 * 1024),
                            )

                preexec = _limits

            return subprocess.run(  # noqa: S603  # Secure sandbox execution
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
                preexec_fn=preexec,
            )

    def _run_with_job_objects(
        self,
        cmd: list[str],
        *,
        cwd: Path | None,
        env: dict[str, str],
        timeout: int,
        memory_mb: int,
    ) -> subprocess.CompletedProcess[str]:
        """Windows-specific execution using Job Objects for hard resource limits.

        Creates a job object with memory and process limits, then runs the
        command within that job for hard enforcement of resource constraints.
        """
        if not WINDOWS_JOB_SUPPORT:
            # Fallback to regular subprocess if Job Objects unavailable
            return subprocess.run(  # noqa: S603  # Windows fallback execution
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
                close_fds=True,  # SECURITY: Prevent handle leakage to child processes
            )

        # Create Job Object with resource limits
        job = win32job.CreateJobObject(None, "")

        # Configure memory and process limits
        info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
        info["BasicLimitInformation"]["LimitFlags"] |= (
            win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
            | win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            | win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
        )
        # CRITICAL SECURITY: Prevent breakaway to keep all descendants in job
        info["BasicLimitInformation"]["LimitFlags"] &= ~(
            win32job.JOB_OBJECT_LIMIT_BREAKAWAY_OK | win32job.JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK
        )
        # Allow 3 processes: main + subprocess + nested subprocess for canary tests
        # This enables testing of subprocess blocking while maintaining resource limits
        info["BasicLimitInformation"]["ActiveProcessLimit"] = 3
        info["ProcessMemoryLimit"] = memory_mb * 1024 * 1024
        win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)

        try:
            # Start process (creation flags ensure handle inheritance is possible)
            proc = subprocess.Popen(  # noqa: S603  # Job object controlled execution
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                close_fds=True,  # SECURITY: Prevent handle leakage to child processes
            )
            job_assigned = True
            try:
                win32job.AssignProcessToJobObject(
                    job,
                    win32api.OpenProcess(0x1F0FFF, False, proc.pid),
                )
            except Exception as assign_exc:  # pragma: no cover - defensive fallback
                job_assigned = False
                # Soft fallback: continue without hard job object limits rather than failing CI
                with suppress(Exception):
                    # If assignment failed early keep process running; no blind terminate
                    pass
                sys.stderr.write(
                    "[sandbox] job object assignment failed; fallback to normal process: "
                    f"{assign_exc}\n"
                )
            try:
                stdout, _ = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                with suppress(Exception):
                    proc.terminate()
                raise TimeoutError(f"Execution exceeded {timeout}s limit (job object)") from exc
            if not job_assigned:
                # We still return the output but note lack of enforced hard limits
                stdout = (
                    stdout + "\n[sandbox] WARNING: Job Object limits not enforced; "
                    "running under standard process limits."
                )
            return subprocess.CompletedProcess(cmd, proc.returncode, stdout, None)
        finally:
            # Clean up job object
            with suppress(Exception):
                win32job.TerminateJobObject(job, 0)
            win32api.CloseHandle(job)
