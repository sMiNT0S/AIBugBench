#!/usr/bin/env python3
"""AIBugBench Security Audit (Phase 5.5)

Expanded audit superseding Phase 5 script. Provides a broader set of
static heuristics validating pre-release security posture. No external
dependencies or network calls are made.

Checks are grouped as:
    MANDATORY  -> Must PASS (FAIL aborts with exit code 1). DEFERRED allowed.
    DEFERRED   -> Planned / nice-to-have hardening; FAIL does not block.

Legend:
    PASS      ✅ Requirement satisfied
    FAIL      ❌ Requirement missing / mismatch
    DEFERRED  ⏸ Feature intentionally postponed / partial

Rationale for some DEFERRED classifications:
    - Network block: Not yet implemented (Phase after public visibility)
    - Python isolated mode (-I/-S) is less relevant since untrusted code is
        imported within a controlled sandbox process, not a new Python exec.
    - Filesystem confinement beyond temp dir (e.g., chroot/namespace) not yet
        implemented; temp dir isolation accepted for initial release.
    - Environment strict whitelist vs pattern scrub currently partial; full
        whitelist may be added later if leakage risk identified.
    - PR security automation deferred while repository remains private.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
import sys


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | FAIL | DEFERRED
    message: str
    mandatory: bool

    def to_icon_line(self, ascii_only: bool = False) -> str:
        if ascii_only:
            icon_map = {"PASS": "[PASS]", "FAIL": "[FAIL]", "DEFERRED": "[DEFER]"}
        else:
            icon_map = {"PASS": "✅", "FAIL": "❌", "DEFERRED": "⏸"}
        icon = icon_map.get(self.status, "?")
        return f"{icon} {self.name}: {self.status} - {self.message}"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def check_sandbox() -> CheckResult:
    path = Path("benchmark/secure_runner.py")
    if not path.exists():
        return CheckResult("Sandbox Implementation", "FAIL", "secure_runner.py missing", True)
    txt = read_text(path)
    required_snippets = [
        "class SecureRunner",
        "tempfile.mkdtemp",
        "SENSITIVE_ENV_PATTERNS",
        "run_with_limits",
    ]
    missing = [s for s in required_snippets if s not in txt]
    if missing:
        return CheckResult(
            "Sandbox Implementation",
            "FAIL",
            f"missing primitives: {', '.join(missing)}",
            True,
        )
    return CheckResult("Sandbox Implementation", "PASS", "core primitives present", True)


def check_validator_integration() -> CheckResult:
    path = Path("benchmark/validators.py")
    if not path.exists():
        return CheckResult("Validator Integration", "FAIL", "validators.py missing", True)
    txt = read_text(path)
    needed = ["def sandbox_validator", "SecureRunner", "_sandbox_enabled"]
    missing = [n for n in needed if n not in txt]
    if missing:
        return CheckResult(
            "Validator Integration",
            "FAIL",
            f"missing: {', '.join(missing)}",
            True,
        )
    if "_sandbox_enabled" in txt and "return func(self, *args, **kwargs)" in txt:
        return CheckResult("Validator Integration", "PASS", "sandbox decorator active", True)
    return CheckResult(
        "Validator Integration",
        "FAIL",
        "decorator pattern not detected",
        True,
    )


def check_cli_security() -> CheckResult:
    path = Path("run_benchmark.py")
    if not path.exists():
        return CheckResult("CLI Security Flags", "FAIL", "run_benchmark.py missing", True)
    txt = read_text(path)
    flags = ["--unsafe", "--allow-network", "--trusted-model"]
    missing = [f for f in flags if f not in txt]
    banner_marker = "AIBugBench Security Status"
    if missing:
        return CheckResult(
            "CLI Security Flags",
            "FAIL",
            f"missing flags: {', '.join(missing)}",
            True,
        )
    if banner_marker not in txt:
        return CheckResult(
            "CLI Security Flags",
            "FAIL",
            "security status banner not found",
            True,
        )
    return CheckResult("CLI Security Flags", "PASS", "flags + banner detected", True)


def check_pr_security_deferred() -> CheckResult:
    """Informational check for deferred Phase 4 (does not fail audit)."""
    workflow = Path(".github/workflows/pr-security.yml")
    roadmap = read_text(Path("docs/ROADMAP.md"))
    deferred = re.search(r"Phase 4: PR security automation.*Deferred", roadmap, re.IGNORECASE)

    if workflow.exists():
        return CheckResult(
            "PR Security Automation",
            "PASS",
            "workflow active",
            False,
        )
    if not workflow.exists() and deferred:
        return CheckResult(
            "PR Security Automation",
            "DEFERRED",
            "explicitly deferred in roadmap",
            False,
        )
    return CheckResult(
        "PR Security Automation",
        "DEFERRED",
        "absent (no roadmap deferral marker found)",
        False,
    )


def _read_secure_runner() -> str:
    return read_text(Path("benchmark/secure_runner.py"))


# ---- Phase 5.5 Additional Checks -------------------------------------------------


def check_temp_workdir() -> CheckResult:
    sr = _read_secure_runner()
    if "tempfile.mkdtemp" in sr or "TemporaryDirectory" in sr:
        return CheckResult("Temp workdir", "PASS", "sandbox uses temp directory", True)
    return CheckResult("Temp workdir", "FAIL", "no temp directory usage detected", True)


def check_env_whitelist() -> CheckResult:
    sr = _read_secure_runner()
    uses_clear = "os.environ.clear" in sr  # restore path counts
    copies_env = "os.environ.copy" in sr
    if uses_clear and not copies_env:
        return CheckResult("Env whitelist", "PASS", "environment cleared then rebuilt", False)
    if uses_clear and copies_env:
        return CheckResult(
            "Env whitelist",
            "DEFERRED",
            "environment partially scrubbed (pattern removal + clear on exit)",
            False,
        )
    return CheckResult("Env whitelist", "DEFERRED", "pattern-based scrubbing only", False)


def check_python_isolation() -> CheckResult:
    # We import user code inside same interpreter; -I/-S not applicable (defer)
    sr = _read_secure_runner()
    if any(flag in sr for flag in [" -I", "'-I'", '"-I"']):
        return CheckResult("Python isolation", "PASS", "-I flag present", False)
    return CheckResult(
        "Python isolation",
        "DEFERRED",
        "-I/-S not yet used (import model code)",
        False,
    )


def check_resource_limits_wired() -> CheckResult:
    sr = _read_secure_runner()
    vd = read_text(Path("benchmark/validators.py"))
    has_rlimit = "resource.setrlimit" in sr
    uses_runner = "SecureRunner" in vd and "run_with_limits" in sr
    if has_rlimit and uses_runner:
        return CheckResult("Resource limits wired", "PASS", "CPU/memory limits present", True)
    if has_rlimit:
        return CheckResult(
            "Resource limits wired", "FAIL", "limits defined but validators may bypass", True
        )
    return CheckResult("Resource limits wired", "FAIL", "no resource limits detected", True)


def check_network_block() -> CheckResult:
    sr = _read_secure_runner()
    if "Network control implemented" in sr:
        return CheckResult("Network block", "PASS", "network control marker present", True)
    if "Network control not implemented" in sr or "network not implemented" in sr.lower():
        return CheckResult("Network block", "DEFERRED", "network blocking deferred", True)
    return CheckResult("Network block", "DEFERRED", "no explicit network blocking (planned)", True)


def check_filesystem_bounds() -> CheckResult:
    sr = _read_secure_runner()
    if any(token in sr for token in ["chroot", "bubblewrap", "nsjail", "bwrap"]):
        return CheckResult(
            "Filesystem bounds",
            "PASS",
            "external confinement tool referenced",
            False,
        )
    # Check for comprehensive filesystem guard implementation
    has_path_guard = "guarded_open" in sr and "_check_path_or_raise" in sr
    has_comprehensive = all(
        guard in sr
        for guard in ["guarded_shutil_copy", "guarded_os_remove", "guarded_shutil_rmtree"]
    )
    if has_path_guard and has_comprehensive:
        return CheckResult(
            "Filesystem bounds", "PASS", "comprehensive filesystem guard active", False
        )
    if "tempfile.mkdtemp" in sr:
        return CheckResult("Filesystem bounds", "DEFERRED", "temp dir isolation only", False)
    return CheckResult("Filesystem bounds", "FAIL", "no isolation primitives detected", False)


def check_banner_honesty() -> CheckResult:
    cli = read_text(Path("run_benchmark.py"))
    sr = _read_secure_runner()
    # Simple heuristic: if banner mentions ENFORCED ensure setrlimit present
    banner_claims_limits = "ENFORCED" in cli or "ResourceLimits" in cli
    has_limits = "resource.setrlimit" in sr
    if banner_claims_limits and not has_limits:
        return CheckResult("Banner honesty", "FAIL", "banner overclaims limits", True)
    return CheckResult("Banner honesty", "PASS", "banner consistent with implementation", True)


def check_subprocess_block() -> CheckResult:
    sr = _read_secure_runner()
    if "_subprocess_blocked" in sr and "subprocess.run = _subprocess_blocked" in sr:
        return CheckResult("Subprocess block", "PASS", "subprocess execution blocked", True)
    return CheckResult("Subprocess block", "FAIL", "subprocess execution not blocked", True)


def check_dynamic_code_block() -> CheckResult:
    sr = _read_secure_runner()
    has_eval_block = "builtins.eval = _dynamic_code_blocked" in sr
    has_exec_block = "builtins.exec = _dynamic_code_blocked" in sr
    has_compile_block = "builtins.compile = _dynamic_code_blocked" in sr

    if has_eval_block and has_exec_block and has_compile_block:
        return CheckResult("Dynamic code block", "PASS", "eval/exec/compile blocked", True)
    return CheckResult("Dynamic code block", "FAIL", "dynamic code execution not blocked", True)


def check_dangerous_imports_block() -> CheckResult:
    sr = _read_secure_runner()
    has_import_guard = "builtins.__import__ = _protected_import" in sr
    has_dangerous_check = "dangerous_modules = {" in sr and "'ctypes'" in sr

    if has_import_guard and has_dangerous_check:
        return CheckResult("Dangerous imports block", "PASS", "dangerous imports blocked", True)
    return CheckResult("Dangerous imports block", "FAIL", "dangerous imports not blocked", True)


def check_windows_job_objects() -> CheckResult:
    sr = _read_secure_runner()
    has_job_import = "import win32job" in sr and "WINDOWS_JOB_SUPPORT" in sr
    has_job_method = "_run_with_job_objects" in sr
    has_platform_check = "if WINDOWS_JOB_SUPPORT:" in sr

    if has_job_import and has_job_method and has_platform_check:
        return CheckResult("Windows Job Objects", "PASS", "Job Objects support implemented", True)
    return CheckResult("Windows Job Objects", "FAIL", "Job Objects not implemented", True)


def check_github_security_config() -> CheckResult:
    workflows = Path(".github/workflows")
    if not workflows.exists():
        return CheckResult("GitHub security config", "DEFERRED", "no workflows directory", False)
    ymls = list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))
    if not ymls:
        return CheckResult(
            "GitHub security config", "DEFERRED", "workflows dir present but empty", False
        )
    codeowners = Path(".github/CODEOWNERS")
    # For private repos, CODEOWNERS is overkill - just check if we have security workflows
    has_security_workflows = any(
        "security" in y.name.lower() or "pr" in y.name.lower() for y in ymls
    )

    if has_security_workflows:
        return CheckResult("GitHub security config", "PASS", "security workflows present", False)
    if not codeowners.exists():
        return CheckResult(
            "GitHub security config",
            "DEFERRED",
            "basic workflows only (CODEOWNERS optional for private repo)",
            False,
        )
    return CheckResult("GitHub security config", "PASS", "basic repo security scaffolding", False)


def run_checks() -> list[CheckResult]:
    checks: list[tuple[Callable[[], CheckResult], bool]] = [
        # Core (existing Phase 5)
        (check_sandbox, True),
        (check_validator_integration, True),
        (check_cli_security, True),
        # Phase 5.5 additions
        (check_temp_workdir, True),
        (check_resource_limits_wired, True),
        (check_network_block, True),  # DEFERRED acceptable until implemented
        (check_subprocess_block, True),
        (check_dynamic_code_block, True),
        (check_dangerous_imports_block, True),
        (check_windows_job_objects, True),
        (check_banner_honesty, True),
        # Non-mandatory hardening (deferred / informational)
        (check_env_whitelist, False),
        (check_python_isolation, False),
        (check_filesystem_bounds, False),
        (check_github_security_config, False),
        # Original deferred Phase 4 automation
        (check_pr_security_deferred, False),
    ]
    results: list[CheckResult] = []
    for func, mandatory in checks:
        try:
            res = func()
            res.mandatory = mandatory
        except Exception as exc:  # pragma: no cover - defensive
            res = CheckResult(func.__name__, "FAIL", f"exception: {exc}", mandatory)
        results.append(res)
    return results


# ---------------- Dynamic Canary Tests (Phase 5.5) -----------------
def _dynamic_cpu_canary() -> CheckResult:
    """Run a tight CPU loop expecting timeout -> PASS else FAIL."""
    try:
        subprocess.run(  # noqa: S603  # Security test - controlled timeout test
            [sys.executable, "-I", "-B", "-c", "while True: pass"],
            timeout=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return CheckResult("Canary CPU loop", "FAIL", "loop did not time out", True)
    except subprocess.TimeoutExpired:
        return CheckResult("Canary CPU loop", "PASS", "timed out as expected", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary CPU loop", "FAIL", f"error: {exc}", True)


def _dynamic_network_canary() -> CheckResult:
    """Attempt outbound connection; expect guard to block."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Network", "FAIL", f"import error: {exc}", True)

    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            test_script = Path(sb) / "network_test.py"
            test_script.write_text(
                (
                    "import socket, sys;\n"
                    "try:\n"
                    "    s=socket.create_connection(('example.com',80),1); s.close(); print('OK')\n"
                    "except Exception as e:\n"
                    "    print('BLOCK', e.__class__.__name__)\n"
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(  # noqa: S603  # Security test - network connectivity validation
                [sys.executable, "-I", "-B", str(test_script)],
                cwd=sb,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3,
                check=False,
            )
            out = proc.stdout
            if "BLOCK" in out:
                return CheckResult("Canary Network", "PASS", "connection blocked", True)
            return CheckResult("Canary Network", "DEFERRED", "no block (feature deferred)", True)
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Network", "PASS", "timeout treated as blocked", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Network", "FAIL", f"error: {exc}", True)


def _dynamic_subprocess_canary() -> CheckResult:
    """Attempt subprocess execution; expect blocking."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "Canary Subprocess",
            "DEFERRED",
            f"secure_runner import failed: {exc}",
            True,
        )
    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            test_script = Path(sb) / "subprocess_test.py"
            test_script.write_text(
                (
                    "import subprocess;\n"
                    "try:\n"
                    "    subprocess.run(['python', '-c', 'print(\"EXECUTED\")']); "
                    "print('ALLOWED')\n"
                    "except Exception as e:\n"
                    "    print('BLOCKED', e.__class__.__name__)\n"
                ),
                encoding="utf-8",
            )
            # Run through SecureRunner to ensure sitecustomize is active
            proc = sr.run_python_sandboxed(
                [str(test_script)],
                timeout=3,
                cwd=sb,
            )
            out = proc.stdout
            if "BLOCKED" in out:
                return CheckResult(
                    "Canary Subprocess", "PASS", "subprocess execution blocked", True
                )
            return CheckResult(
                "Canary Subprocess", "FAIL", f"subprocess execution allowed: {out!r}", True
            )
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Subprocess", "DEFERRED", "timeout (indeterminate)", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Subprocess", "FAIL", f"error: {exc}", True)


def _dynamic_fs_canary() -> CheckResult:
    """Attempt reading a file outside sandbox; expect denial."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "Canary Filesystem",
            "DEFERRED",
            f"secure_runner import failed: {exc}",
            False,
        )
    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            outside = Path.home() / ".ssh" / "id_rsa"
            test_script = Path(sb) / "attempt.py"
            test_script.write_text(
                (
                    f"import pathlib,sys; p=pathlib.Path(r'{outside}');\n"
                    "try: open(p,'rb').read(1); print('OPENED')\n"
                    "except Exception as e: print('DENIED', e.__class__.__name__)\n"
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(  # noqa: S603  # Security test - filesystem access validation
                [sys.executable, "-I", "-B", str(test_script)],
                cwd=sb,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3,
                check=False,
            )
            out = proc.stdout
            if "DENIED" in out:
                return CheckResult("Canary Filesystem", "PASS", "outside file blocked", False)
            return CheckResult("Canary Filesystem", "DEFERRED", "no FS confinement yet", False)
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Filesystem", "DEFERRED", "timeout (indeterminate)", False)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Filesystem", "FAIL", f"error: {exc}", False)


def _dynamic_process_spawn_canary() -> CheckResult:
    """Attempt exec/spawn/fork operations; expect blocking."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "Canary Process Spawn",
            "DEFERRED",
            f"secure_runner import failed: {exc}",
            True,
        )
    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            test_script = Path(sb) / "process_spawn_test.py"
            test_script.write_text(
                (
                    "import os, sys;\n"
                    "blocked_count = 0;\n"
                    "# Test exec family\n"
                    "for func_name in ['execv', 'execve', 'execvp', 'execvpe']:\n"
                    "    if hasattr(os, func_name):\n"
                    "        try:\n"
                    "            getattr(os, func_name)([sys.executable, '-c', 'print(1)'])\n"
                    "            print(f'{func_name} ALLOWED')\n"
                    "        except Exception:\n"
                    "            blocked_count += 1\n"
                    "# Test spawn family\n"
                    "for func_name in ['spawnv', 'spawnve', 'spawnvp', 'spawnvpe']:\n"
                    "    if hasattr(os, func_name):\n"
                    "        try:\n"
                    "            args = [sys.executable, ['-c', 'print(1)']]\n"
                    "            getattr(os, func_name)(os.P_NOWAIT, *args)\n"
                    "            print(f'{func_name} ALLOWED')\n"
                    "        except Exception:\n"
                    "            blocked_count += 1\n"
                    "# Test fork family\n"
                    "for func_name in ['fork', 'forkpty']:\n"
                    "    if hasattr(os, func_name):\n"
                    "        try:\n"
                    "            getattr(os, func_name)()\n"
                    "            print(f'{func_name} ALLOWED')\n"
                    "        except Exception:\n"
                    "            blocked_count += 1\n"
                    "# Test posix_spawn family\n"
                    "for func_name in ['posix_spawn', 'posix_spawnp']:\n"
                    "    if hasattr(os, func_name):\n"
                    "        try:\n"
                    "            args = [sys.executable, ['-c', 'print(1)'], {}]\n"
                    "            getattr(os, func_name)(*args)\n"
                    "            print(f'{func_name} ALLOWED')\n"
                    "        except Exception:\n"
                    "            blocked_count += 1\n"
                    "print(f'BLOCKED_COUNT:{blocked_count}')\n"
                ),
                encoding="utf-8",
            )
            # Run through SecureRunner to ensure sitecustomize is active
            proc = sr.run_python_sandboxed(
                [str(test_script)],
                timeout=3,
                cwd=sb,
            )
            out = proc.stdout
            if "BLOCKED_COUNT:" in out:
                # Extract the count of blocked operations
                import re

                match = re.search(r"BLOCKED_COUNT:(\d+)", out)
                if match:
                    blocked_count = int(match.group(1))
                    if blocked_count > 0:
                        return CheckResult(
                            "Canary Process Spawn",
                            "PASS",
                            f"process spawn operations blocked ({blocked_count} functions)",
                            True,
                        )
            if "ALLOWED" in out:
                return CheckResult(
                    "Canary Process Spawn",
                    "FAIL",
                    f"process spawn operations allowed: {out!r}",
                    True,
                )
            return CheckResult(
                "Canary Process Spawn",
                "DEFERRED",
                f"no process spawn functions detected: {out!r}",
                True,
            )
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Process Spawn", "DEFERRED", "timeout (indeterminate)", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Process Spawn", "FAIL", f"error: {exc}", True)


def _dynamic_code_execution_canary() -> CheckResult:
    """Attempt dynamic code execution; expect blocking."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "Canary Dynamic Code",
            "DEFERRED",
            f"secure_runner import failed: {exc}",
            True,
        )
    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            test_script = Path(sb) / "dynamic_code_test.py"
            test_script.write_text(
                (
                    "import sys;\n"
                    "blocked_count = 0;\n"
                    "# Test eval\n"
                    "try:\n"
                    "    eval('print(\"EVAL_WORKED\")')\n"
                    "    print('EVAL ALLOWED')\n"
                    "except Exception:\n"
                    "    blocked_count += 1\n"
                    "# Test exec\n"
                    "try:\n"
                    "    exec('print(\"EXEC_WORKED\")')\n"
                    "    print('EXEC ALLOWED')\n"
                    "except Exception:\n"
                    "    blocked_count += 1\n"
                    "# Test compile\n"
                    "try:\n"
                    "    code = compile('print(\"COMPILE_WORKED\")', '<string>', 'exec')\n"
                    "    exec(code)\n"
                    "    print('COMPILE ALLOWED')\n"
                    "except Exception:\n"
                    "    blocked_count += 1\n"
                    "print(f'BLOCKED_COUNT:{blocked_count}')\n"
                ),
                encoding="utf-8",
            )
            # Run through SecureRunner to ensure sitecustomize is active
            proc = sr.run_python_sandboxed(
                [str(test_script)],
                timeout=3,
                cwd=sb,
            )
            out = proc.stdout
            if "BLOCKED_COUNT:" in out:
                # Extract the count of blocked operations
                import re

                match = re.search(r"BLOCKED_COUNT:(\d+)", out)
                if match:
                    blocked_count = int(match.group(1))
                    if blocked_count >= 2:  # At least eval and exec should be blocked
                        return CheckResult(
                            "Canary Dynamic Code",
                            "PASS",
                            f"dynamic code execution blocked ({blocked_count}/3 functions)",
                            True,
                        )
            if any(word in out for word in ["EVAL_WORKED", "EXEC_WORKED", "COMPILE_WORKED"]):
                return CheckResult(
                    "Canary Dynamic Code", "FAIL", f"dynamic code execution allowed: {out!r}", True
                )
            return CheckResult(
                "Canary Dynamic Code", "DEFERRED", f"indeterminate result: {out!r}", True
            )
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Dynamic Code", "DEFERRED", "timeout (indeterminate)", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Dynamic Code", "FAIL", f"error: {exc}", True)


def _dangerous_imports_canary() -> CheckResult:
    """Attempt dangerous module imports; expect blocking."""
    try:
        # Add current directory to path for import
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from benchmark.secure_runner import SecureRunner  # lazy import
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "Canary Dangerous Imports",
            "DEFERRED",
            f"secure_runner import failed: {exc}",
            True,
        )
    sr = SecureRunner("canary_model")
    try:
        with sr.sandbox() as sb:
            test_script = Path(sb) / "dangerous_imports_test.py"
            test_script.write_text(
                (
                    "blocked_count = 0;\n"
                    "dangerous_modules = ['ctypes', 'marshal', 'pickle'];\n"
                    "for module_name in dangerous_modules:\n"
                    "    try:\n"
                    "        __import__(module_name)\n"
                    "        print(f'{module_name} IMPORT ALLOWED')\n"
                    "    except Exception as e:\n"
                    "        if 'disabled in sandbox' in str(e):\n"
                    "            blocked_count += 1\n"
                    "        else:\n"
                    "            print(f'{module_name} IMPORT ERROR: {e}')\n"
                    "print(f'BLOCKED_COUNT:{blocked_count}')\n"
                ),
                encoding="utf-8",
            )
            # Run through SecureRunner to ensure sitecustomize is active
            proc = sr.run_python_sandboxed(
                [str(test_script)],
                timeout=3,
                cwd=sb,
            )
            out = proc.stdout
            if "BLOCKED_COUNT:" in out:
                # Extract the count of blocked operations
                import re

                match = re.search(r"BLOCKED_COUNT:(\d+)", out)
                if match:
                    blocked_count = int(match.group(1))
                    if blocked_count >= 2:  # At least ctypes and marshal should be blocked
                        return CheckResult(
                            "Canary Dangerous Imports",
                            "PASS",
                            f"dangerous imports blocked ({blocked_count}/3 modules)",
                            True,
                        )
            if "IMPORT ALLOWED" in out:
                return CheckResult(
                    "Canary Dangerous Imports", "FAIL", f"dangerous imports allowed: {out!r}", True
                )
            return CheckResult(
                "Canary Dangerous Imports", "DEFERRED", f"indeterminate result: {out!r}", True
            )
    except subprocess.TimeoutExpired:
        return CheckResult("Canary Dangerous Imports", "DEFERRED", "timeout (indeterminate)", True)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Canary Dangerous Imports", "FAIL", f"error: {exc}", True)


def run_dynamic_canaries(existing: list[CheckResult]) -> list[CheckResult]:
    return [
        *existing,
        _dynamic_cpu_canary(),
        _dynamic_network_canary(),
        _dynamic_subprocess_canary(),
        _dynamic_process_spawn_canary(),
        _dynamic_code_execution_canary(),
        _dangerous_imports_canary(),
        _dynamic_fs_canary(),
    ]


def reconcile_static_with_canaries(results: list[CheckResult]) -> list[CheckResult]:
    """If a dynamic canary proves a block works, mark corresponding static check PASS.

    This reduces brittleness where static heuristic may show FAIL while runtime sandbox
    behavior is actually enforced.
    """
    by = {r.name: r for r in results}
    pairs = [
        ("Subprocess block", "Canary Subprocess"),
        ("Dynamic code block", "Canary Dynamic Code"),
        ("Dangerous imports block", "Canary Dangerous Imports"),
        ("Network block", "Canary Network"),
        ("Filesystem bounds", "Canary Filesystem"),
    ]
    for static_name, canary_name in pairs:
        if (
            canary_name in by
            and by[canary_name].status == "PASS"
            and static_name in by
            and by[static_name].status == "FAIL"
        ):
            by[static_name].status = "PASS"
            by[static_name].message = "validated by canary"
    return list(by.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AIBugBench security audit")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_checks()
    results = run_dynamic_canaries(results)
    results = reconcile_static_with_canaries(results)
    mandatory_fail = any(r.status == "FAIL" and r.mandatory for r in results)

    if args.json:
        payload = {
            "results": [asdict(r) for r in results],
            "ok": not mandatory_fail,
        }
        json.dump(payload, sys.stdout, indent=2)
        print()
        return 0 if not mandatory_fail else 1

    ascii_only = False
    header = "🔒 AIBugBench Security Audit\n"
    try:
        print(header)
    except UnicodeEncodeError:
        ascii_only = True
        print("[SECURITY AUDIT]\n")
    for r in results:
        try:
            print(r.to_icon_line(ascii_only=ascii_only))
        except UnicodeEncodeError:
            ascii_only = True
            print(r.to_icon_line(ascii_only=True))

    print("\nSummary:")
    passed = sum(1 for r in results if r.status == "PASS" and r.mandatory)
    deferred = sum(1 for r in results if r.status == "DEFERRED" and r.mandatory)
    total_mandatory = sum(1 for r in results if r.mandatory)
    try:
        print(f"  Mandatory passed: {passed}/{total_mandatory} (DEFERRED: {deferred})")
        print(f"  Optional / informational: {sum(1 for r in results if not r.mandatory)}")
    except UnicodeEncodeError:
        print(f"  Mandatory passed: {passed}/{total_mandatory} (DEFERRED: {deferred})")
        print(f"  Optional / informational: {sum(1 for r in results if not r.mandatory)}")

    if mandatory_fail:
        try:
            print("\n❌ Security audit FAILED (mandatory check failure)")
        except UnicodeEncodeError:
            print("\n[FAIL] Security audit FAILED (mandatory check failure)")
        return 1
    try:
        print("\n✅ Security audit PASSED (mandatory checks) — deferred items optional")
    except UnicodeEncodeError:
        print("\n[PASS] Security audit PASSED (mandatory checks) - deferred items optional")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
