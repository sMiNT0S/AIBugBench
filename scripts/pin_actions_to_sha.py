# scripts/pin_actions_to_sha.py
from __future__ import annotations

import argparse
from pathlib import Path
import re

# Single source of truth for pins (update here, not in mystery copies)
ACTION_PINS = {
    "actions/checkout@v4": "actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332",
    "actions/checkout@v5": "actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332",
    "actions/setup-python@v5": "actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d",
    "actions/cache@v4": "actions/cache@0c45773b623bea8c8e75f6c82b208c3cf94ea4f9",
    "actions/upload-artifact@v4": (
        "actions/upload-artifact@65462800fd760344b1a7b4382951275a0abb4808"
    ),
    "actions/download-artifact@v4": (
        "actions/download-artifact@65a9edc5881444af0b9093a5e628f2fe47ea3b2e"
    ),
    "codecov/codecov-action@v5": (
        "codecov/codecov-action@fdcc8476540edceab3de004e990f80d881c6cc00"
    ),
}

def _rewrite(content: str) -> str:
    for tag, pin in ACTION_PINS.items():
        content = re.sub(re.escape(tag), pin, content)
    return content

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workflows-dir", default=".github/workflows")
    p.add_argument("--list", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply", action="store_true")
    a = p.parse_args(argv)

    if a.list:
        print("Pinned actions:")
        for k, v in ACTION_PINS.items():
            print(f"  {k} -> {v}")
        return 0

    changed = 0
    for fp in Path(a.workflows_dir).glob("*.yml"):
        before = fp.read_text(encoding="utf-8")
        after = _rewrite(before)
        if after != before:
            changed += 1
            if a.apply:
                fp.write_text(after, encoding="utf-8")
                print(f"✅ updated {fp}")
            else:
                print(f"🔎 would update {fp} (use --apply)")
    print(f"Done. {changed} file(s) {'updated' if a.apply else 'needing update'}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
