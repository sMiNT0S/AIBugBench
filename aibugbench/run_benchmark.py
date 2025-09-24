"""Minimal CLI shim for Phase-0 seam tests.

It intentionally provides *very* limited behaviour: a `--dry-run` flag causes
it to output a single SUMMARY line so that the characterization test can load
and compare it to a golden JSON fixture. All real logic remains in the legacy
`run_benchmark.py` root-level script until later phases.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

from aibugbench.config.artifacts import choose_artifact_path

SUMMARY_PREFIX = "SUMMARY:"


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("AIBugBench Phase-0 CLI stub", add_help=False)
    p.add_argument("--prompt", default="p1")
    p.add_argument("--artifact", help="Explicit artifact output directory")
    p.add_argument("--dry-run", action="store_true", help="Emit summary but perform no work")
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    # Resolve artifact dir via Phase-0 facade (args > env > default)
    # Use OS temp dir instead of hardcoded /tmp to satisfy Bandit B108.
    # This remains a deterministic, low-risk default for Phase-0 snapshot tests.
    defaults = tempfile.gettempdir()  # nosec B108: test-only default path
    artifact_path = choose_artifact_path(vars(args), os.environ, defaults)

    if args.dry_run:
        print(f"{SUMMARY_PREFIX}{json.dumps({'status': 'ok', 'artifact': artifact_path})}")
        sys.exit(0)

    # In Phase 0 we do nothing else - everything else lives in legacy script.
    print("This is a Phase-0 stub. Use --dry-run for snapshot tests.")
    sys.exit(0)


if __name__ == "__main__":
    main()
