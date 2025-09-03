#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REQ = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock"

def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=str(ROOT)) # noqa

def main() -> int:
    if not REQ.exists():
        print(f"❌ {REQ} not found", file=sys.stderr)
        return 1

    piptools = shutil.which("pip-compile") or shutil.which("piptools")
    if piptools:
        print("🔒 Using pip-tools to generate hash-pinned lock…")
        code = run([
            sys.executable, "-m", "piptools", "compile",
            "--generate-hashes",
            "-o", str(LOCK),
            str(REQ),
        ])
        if code == 0:
            print(f"✅ wrote {LOCK}")
        return code

    # If you really want a fallback, uncomment below.
    # But integrity without hashes is theater, so we default to failing.
    print("❌ pip-tools not found. Install with: pip install 'pip-tools>=7.5.0'", file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
