# SAFETY.md

**AIBugBench** executes model-generated Python in a constrained environment. This document explains what is enforced, how it works, what it does not cover, how to verify it, and recent hardening changes.

## 1) Threat model

### In scope

- Arbitrary Python supplied by a model or user attempting to:
  - execute dynamic code (`eval`, `exec`, `compile`)
  - spawn processes (`subprocess`, `os.system`, spawn/exec families)
  - access filesystem outside a temp workdir
  - exfiltrate data via network sockets
  - consume excessive CPU, memory, or PIDs
  - tamper with guards via `importlib.reload` or re-binding

### Out of scope

- Kernel escapes, CPython interpreter vulnerabilities, or native code inside C extensions
- Host-wide protection (use containers/VMs for stronger isolation)
- User-approved “unsafe mode” runs (see `--unsafe`)

## 2) Execution model

- **Child process sandbox**: generated code runs in a separate Python process, not the harness process.
- **Guard injection via `sitecustomize`**: a bootstrap module installs runtime guards in the child:
  - dynamic execution blocked: `eval/exec/compile`
  - dangerous imports blocked: `ctypes`, `pickle`, `marshal`
  - import tampering blocked: `importlib.reload`
  - subprocess/exec/spawn blocked: `subprocess.run/call/Popen`, `os.system`, `os.exec*`, `os.spawn*`
  - filesystem confined: critical file ops validate paths against a temp root
  - directory enumeration guarded: `os.listdir`, `os.scandir` validated
  - network egress blocked by default
- **Why not `-I` (isolated mode)**: `-I` prevents `sitecustomize` from loading. We instead inject `PYTHONPATH` for deterministic guard loading and run with `-B` to avoid `.pyc` side effects.
- **Ephemeral workspace**: each run gets a unique temp directory (exported as `AIBB_TMP`). Inputs are copied in; outputs are harvested; the directory is removed.

## 3) Filesystem confinement

- All sensitive file operations validate the target path:
  - Paths are `resolve()`d and must `relative_to(SANDBOX_ROOT)` or they are denied.
  - Guards wrap `open`, `os.remove`, `shutil.rmtree/copyfile/move`, etc.
  - Symlink traversal is constrained by `resolve()`; attempts to step outside the sandbox raise.
- Read-only inputs are mounted/copied in; writes must stay under the temp root.

## 4) Process and network blocking

- **Process creation**: blocked for `subprocess.run/call/Popen`, `os.system`, spawn/exec/fork families. Calls raise with a clear error.
- **Network egress**: socket operations are denied by default. Allow with an explicit flag (see configuration) only if you understand the risk.

## 5) Dynamic execution and import hardening

- `eval`, `exec`, `compile` are replaced with guards that raise.
- `builtins.__import__` is wrapped to ban `ctypes`, `pickle`, `marshal` and other disallowed modules.
- `importlib.reload` is blocked to prevent guard removal.
- Critical guard references are hidden in closures to reduce rebind bypasses.

## 6) Resource limits

- **POSIX**: CPU time, address space, file size, and open files are limited via `resource.setrlimit`.
- **Windows**: OS-level hard caps via Job Objects (memory limits, process caps, kill-on-close) are implemented when `pywin32` is available. If unavailable, the runner enforces wall-clock timeouts with full process-tree termination as a fallback.
- **Global watchdog** kills the entire child process tree on timeout; no orphans.

## 7) Pre-run security audit (local and CI)

Before any run, the harness invokes a self-contained audit script that verifies:

- required guard symbols exist and are active
- subprocess/network/filesystem canaries fail as expected
- CLI surface exposes only documented opt-outs
- repo CI matches local checks

The audit must pass or the run is aborted unless the user opts into `--unsafe`.

## 8) Configuration

- `--timeout <s>`: wall-clock timeout per run
- `--mem <MB>`: memory limit (enforced via rlimits on POSIX; Job Objects on Windows when available)
- `--cpu <shares>`: CPU cap (future)
- `--pids <n>`: max processes/threads (future/Job Objects)
- `--allow-network`: enable network egress for the child process
- `--unsafe`: bypasses the audit and disables protections; logged loudly in output
- `--isolation=docker` (roadmap): run the child in a container (`--network=none`, read-only root, resource flags)

## 9) Guarantees and non-goals

### Guarantees

- In default mode, the child process cannot spawn other processes, call dynamic code, import banned modules, access files outside its temp root, or open network sockets.
- The pre-run audit verifies these guarantees and fails closed.

### Non-goals

- This is not a VM. Kernel-level isolation requires containers/VMs you control.
- Code requiring subprocess, system tools, or outbound network will fail by design.

## 10) Verifying locally

```bash
# must succeed
python scripts/security_audit.py

# a canary that should FAIL inside the sandbox:
python - <<'PY'
import subprocess; subprocess.run(["whoami"])
PY
# Expect: RuntimeError indicating subprocess is disabled
```

## 11) Writing validators safely

Always execute candidate code via the sandboxed child helper (not in-process).

Pass only explicit inputs; never pass host paths you aren’t comfortable exposing.

Enforce a per-validator wall-clock timeout and memory limit by delegating to the runner.

## 12) Disclosure policy

Use GitHub’s private vulnerability reporting for security issues. Do not open a public issue first.

Include minimal PoC, environment, exact command, and expected vs actual behavior.

## 13) Recent hardening summary (consolidated)

The following internal hardening steps were recently completed to reduce latent security and correctness risks:

- Selective strict typing ("strict-core") applied to benchmark core modules to surface unsafe dynamic patterns early.
- Centralized result schemas (TypedDicts) eliminated ad-hoc dict shape assumptions in the runner/validators, lowering mutation & key error risk.
- Decorator signatures preserved via `ParamSpec` + `Concatenate` + `Self` to avoid untyped call-through that could mask guard parameter changes.
- Lint & static analysis hygiene: removal of redundant casts / ignores, modernization of imports, and consistent explicit return typing for guard-related paths.
- Safer I/O printing path (`safe_print`) refactored for deterministic fallback (reducing rare Unicode/log handling exceptions that could obscure security audit failures).

These changes are non-functional from a sandbox policy perspective but materially improve the reliability of enforcement and audit tooling.

## 14) Roadmap excerpt (security-relevant)

- Windows Job Object enforcement for memory / CPU / handle caps
- Optional container (`--isolation=docker`) execution backend
- Expanded statistics & provenance typing for stricter audit assertions
- Additional guard canaries (module import fuzz, symlink race probes)

---
For a concise overview, see the "Security at a glance" section in the root README.
