#!/usr/bin/env python3
"""AIBugBench Pre-Release Security Audit (Phase 5)

This script performs a series of lightweight, dependency-free checks
verifying that core security hardening measures are in place prior to
public release.

Checks (Mandatory):
  1. Sandbox implementation (secure_runner) present with key primitives
  2. Validator integration (sandbox decorator + SecureRunner usage)
  3. CLI security flags & banner logic present

Checks (Deferred / Informational):
  4. PR security automation (Phase 4) — currently deferred; reported but
     absence does not fail audit (see ROADMAP deferred section).

Exit code:
  0 -> All mandatory checks pass (informational/deferred may be missing)
  1 -> One or more mandatory checks fail or script internal error occurs

Optional Flags:
  --json  Emit machine-readable JSON summary to stdout (no color/icons)

The script purposely avoids external imports and network calls.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | FAIL | DEFERRED
    message: str
    mandatory: bool

    def to_icon_line(self) -> str:
        icon = {"PASS": "✅", "FAIL": "❌", "DEFERRED": "⏸"}.get(self.status, "❓")
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
    codeowners = Path(".github/CODEOWNERS")
    roadmap = read_text(Path("docs/ROADMAP.md"))
    deferred = re.search(r"Phase 4: PR security automation.*Deferred", roadmap, re.IGNORECASE)

    if workflow.exists() and codeowners.exists():
        return CheckResult(
            "PR Security Automation",
            "PASS",
            "workflow active",
            False,
        )
    if not workflow.exists() and not codeowners.exists() and deferred:
        return CheckResult(
            "PR Security Automation",
            "DEFERRED",
            "explicitly deferred in roadmap",
            False,
        )
    if codeowners.exists() or workflow.exists():
        return CheckResult(
            "PR Security Automation",
            "DEFERRED",
            "partial artifacts present; finalize or remove",
            False,
        )
    return CheckResult(
        "PR Security Automation",
        "DEFERRED",
        "absent (no roadmap deferral marker found)",
        False,
    )


def run_checks() -> list[CheckResult]:
    checks: list[tuple[Callable[[], CheckResult], bool]] = [
        (check_sandbox, True),
        (check_validator_integration, True),
        (check_cli_security, True),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AIBugBench security audit")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_checks()
    mandatory_fail = any(r.status == "FAIL" and r.mandatory for r in results)

    if args.json:
        payload = {
            "results": [asdict(r) for r in results],
            "ok": not mandatory_fail,
        }
        json.dump(payload, sys.stdout, indent=2)
        print()
        return 0 if not mandatory_fail else 1

    print("🔒 AIBugBench Security Audit\n")
    for r in results:
        print(r.to_icon_line())

    print("\nSummary:")
    passed = sum(1 for r in results if r.status == "PASS")
    deferred = sum(1 for r in results if r.status == "DEFERRED")
    print(
        f"  Mandatory passed: {passed - deferred}/{sum(1 for r in results if r.mandatory)}"
    )
    print(f"  Deferred / informational: {deferred}")

    if mandatory_fail:
        print("\n❌ Security audit FAILED (mandatory check failure)")
        return 1
    print("\n✅ Security audit PASSED (mandatory checks) — deferred items optional")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
