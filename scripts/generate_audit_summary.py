#!/usr/bin/env python3
"""Generate a concise Markdown summary for security audit results.

Usage:
    python scripts/generate_audit_summary.py audit.json

Writes audit_summary.md and appends to $GITHUB_STEP_SUMMARY if present.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def main(path: str) -> int:
    p = Path(path)
    lines: list[str] = []
    if not p.exists():
        lines.append("### Security Audit Summary")
        lines.append("Audit file missing; audit script may have crashed.")
    else:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover
            lines.append("### Security Audit Summary")
            lines.append(f"Failed to parse audit JSON: {exc}")
        else:
            results = data.get("results", [])
            mandatory = [r for r in results if r.get("mandatory")]
            failed = [r for r in mandatory if r.get("status") == "FAIL"]
            deferred = [r for r in mandatory if r.get("status") == "DEFERRED"]
            passed = [r for r in mandatory if r.get("status") == "PASS"]
            lines.append("### Security Audit Summary")
            lines.append(f"* Overall OK: **{data.get('ok')}**")
            lines.append(f"* Mandatory Passed: {len(passed)} / {len(mandatory)}")
            lines.append(f"* Mandatory Deferred: {len(deferred)}")
            lines.append(f"* Mandatory Failed: {len(failed)}")
            if failed:
                lines.append("")
                lines.append("#### Failed Mandatory Checks")
                for r in failed:
                    lines.append(f"- {r.get('name')}: {r.get('message')}")
    Path("audit_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:  # pragma: no cover - env dep
            fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "audit.json"))
