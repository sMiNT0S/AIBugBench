#!/usr/bin/env python
from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

try:  # packaging is a pip-tools dependency; required for strict version gate
    from packaging.version import Version
except Exception:  # pragma: no cover
    Version = None

ROOT = Path(__file__).resolve().parent.parent
REQ_RUNTIME = ROOT / "requirements.txt"
LOCK_RUNTIME = ROOT / "requirements.lock"
REQ_DEV = ROOT / "requirements-dev.txt"
LOCK_DEV = ROOT / "requirements-dev.lock"


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=str(ROOT))  # noqa


def _require_modern_piptools() -> str | None:
    """Return version string if pip-tools >=7.5.0, else None."""
    try:
        if Version is None:
            return None
        import importlib.metadata as _im

        ver = Version(_im.version("pip-tools"))
        if ver >= Version("7.5.0"):
            return str(ver)
        return None
    except Exception:  # pragma: no cover
        return None


def _rewrite_header(lock_path: Path, lock_name: str, req_name: str) -> None:
    """Normalize header comment to canonical relative form for stable diffs."""
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return
    for i, line in enumerate(lines):
        if line.startswith("#    pip-compile "):
            desired = f"#    pip-compile --generate-hashes --output-file={lock_name} {req_name}\n"
            if line != desired:
                lines[i] = desired
                lock_path.write_text("".join(lines), encoding="utf-8")
            break


def compile_lock(req: Path, output: Path, lock_name: str, dev: bool) -> int:
    """Run pip-tools compile producing the given output path for req file.

    Uses relative requirement filename (stable across platforms) and injects a
    --custom-compile-command so the header in the generated lock file matches
    the committed canonical command. This keeps diffs stable between Linux,
    macOS, and Windows (avoids absolute path leakage).

    If dev=True, adds --allow-unsafe to retain prior behavior of capturing
    tooling packages like pip/setuptools/wheel (useful for reproducible
    isolated dev environments) while leaving runtime lock minimal.
    """
    print(f"Using pip-tools to generate hash-pinned lock for {req.name}...")
    if _require_modern_piptools() is None:
        print(
            "pip-tools >=7.5.0 required. Upgrade with: pip install -U 'pip-tools>=7.5.0'",
            file=sys.stderr,
        )
        return 4
    cmd: list[str] = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--generate-hashes",
        "-o",
        str(output),
        req.name,
    ]
    if dev:
        cmd.append("--allow-unsafe")
    rc = run(cmd)
    if rc == 0:
        _rewrite_header(output, lock_name, req.name)
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update or check requirements(.lock) consistency (runtime or dev)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if requirements.lock is out of date (no write)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Operate on requirements-dev.txt / requirements-dev.lock instead of runtime",
    )
    args = parser.parse_args()

    req = REQ_DEV if args.dev else REQ_RUNTIME
    lock = LOCK_DEV if args.dev else LOCK_RUNTIME

    if not req.exists():
        print(f"{req} not found", file=sys.stderr)
        return 1

    if not lock.exists() and args.check:
        print(f"{lock} missing (cannot --check). Run without --check first.", file=sys.stderr)
        return 1

    piptools = shutil.which("pip-compile") or shutil.which("piptools")
    if not piptools:
        # Try local venv Scripts (Windows) / bin (POSIX) directly
        if sys.platform.startswith("win"):
            candidate = ROOT / "venv" / "Scripts" / "pip-compile.exe"
        else:
            candidate = ROOT / "venv" / "bin" / "pip-compile"
        if candidate.exists():
            piptools = str(candidate)
        else:
            print(
                "pip-tools not found. Install with: pip install 'pip-tools>=7.5.0'",
                file=sys.stderr,
            )
            return 2

    if args.check:
        with tempfile.TemporaryDirectory() as td:
            tmp_lock = Path(td) / "_lock.tmp"
            code = compile_lock(req, tmp_lock, lock.name, args.dev)
            if code != 0:
                return code
            new_content = tmp_lock.read_text(encoding="utf-8").splitlines(keepends=True)
            old_content = lock.read_text(encoding="utf-8").splitlines(keepends=True)
            if new_content != old_content:
                print(
                    f"{lock.name} is OUT OF DATE with {req.name}",
                    file=sys.stderr,
                )
                diff = difflib.unified_diff(
                    old_content,
                    new_content,
                    fromfile=str(lock.name),
                    tofile="(recompiled)",
                )
                for i, line in enumerate(diff):
                    if i > 400:  # safety cut
                        print("... diff truncated ...", file=sys.stderr)
                        break
                    print(line.rstrip())
                print(
                    "Run: python scripts/update_requirements_lock.py"
                    + (" --dev" if args.dev else "")
                    + " to refresh.",
                    file=sys.stderr,
                )
                return 3
            print(f"{lock.name} up to date")
            return 0
    # Update mode (write lock)
    code = compile_lock(req, lock, lock.name, args.dev)
    if code == 0:
        print(f"wrote {lock}")
    return code


EXIT_CODE_LEGEND = {
    0: "up to date or successful write",
    1: "missing files / basic error",
    2: "pip-tools missing",
    3: "drift detected in --check",
    4: "pip-tools too old (<7.5.0)",
}

if __name__ == "__main__":
    rc = main()
    meaning = EXIT_CODE_LEGEND.get(rc, "(unknown)")
    print(f"Exit code {rc}: {meaning}")
    sys.exit(rc)
