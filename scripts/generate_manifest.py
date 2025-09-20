#!/usr/bin/env python3
"""Generate standardized JSON manifests for CI artifacts."""

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any


def get_file_info(file_path: Path) -> dict[str, Any]:
    try:
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "sha256": None,
            "size": stat.st_size,
            "exists": True,
        }
    except FileNotFoundError:
        return {
            "path": str(file_path),
            "sha256": None,
            "size": None,
            "exists": False,
        }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generated-by", required=True)
    p.add_argument("--output", default="artifacts.manifest.json")
    p.add_argument("--item", action="append", nargs=2, metavar=("PATH", "KIND"))
    p.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA"))
    p.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID"))
    args = p.parse_args()

    if not args.item:
        print("No items specified. Use --item PATH KIND", file=sys.stderr)
        return 1

    items: list[dict[str, Any]] = []
    for path_str, kind in args.item:
        file_path = Path(path_str)
        item: dict[str, Any] = {"path": path_str, "kind": kind}
        item.update(get_file_info(file_path))
        items.append(item)

    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    manifest = {
        "generated_by": args.generated_by,
        "created_at": created_at,
        "commit_sha": args.commit_sha,
        "workflow_run_id": args.workflow_run_id,
        "items": items,
    }

    out = Path(args.output)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Generated manifest: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
