#!/usr/bin/env python
"""Lightweight wrapper to verify requirements(.lock) files are in sync.

Uses existing update_requirements_lock.py in --check mode for runtime and/or
dev dependencies. Exits non-zero if drift is detected. Intended for future
CI consolidation or tooling integration without re-implementing diff logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "update_requirements_lock.py"


def _run(args: list[str]) -> int:
    # Internal call to existing lock updater; arguments are static lists we control.
    # Invokes maintained internal script with static argument list (no user input) -> safe.
    return subprocess.call([sys.executable, str(SCRIPT), *args])  # noqa S603


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify requirements.lock and dev lock freshness")
    parser.add_argument("--dev", action="store_true", help="Check only dev lock")
    parser.add_argument("--runtime", action="store_true", help="Check only runtime lock")
    ns = parser.parse_args()

    targets: list[tuple[str, list[str]]] = []
    if ns.dev and not ns.runtime:
        targets.append(("dev", ["--check", "--dev"]))
    elif ns.runtime and not ns.dev:
        targets.append(("runtime", ["--check"]))
    else:  # default: both
        targets.append(("runtime", ["--check"]))
        targets.append(("dev", ["--check", "--dev"]))

    rc_accum = 0
    for label, cmd in targets:
        print(f"[verify-lock-sync] Checking {label} lock...")
        rc = _run(cmd)
        if rc not in (0, 3):  # 3 = drift, handled below
            rc_accum = rc_accum or rc
        elif rc == 3:
            print(f"[verify-lock-sync] {label} lock drift detected.")
            rc_accum = rc_accum or 3
        else:
            print(f"[verify-lock-sync] {label} lock up to date.")

    if rc_accum == 0:
        print("All requested locks up to date.")
    elif rc_accum == 3:
        print("One or more locks out of date.", file=sys.stderr)
    else:
        print(f"Failure during lock verification (exit {rc_accum}).", file=sys.stderr)
    return rc_accum


EXIT_CODE_LEGEND = {
    0: "all locks up to date",
    3: "drift detected (one or more locks out of date)",
}


if __name__ == "__main__":  # pragma: no cover - trivial wrapper
    code = main()
    meaning = EXIT_CODE_LEGEND.get(code, "(see update_requirements_lock.py legend)")
    print(f"verify_lock_sync exit {code}: {meaning}")
    raise SystemExit(code)
