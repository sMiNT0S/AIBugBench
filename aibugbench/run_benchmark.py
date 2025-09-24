"""CLI entry point delegating to the Phase-2 BenchmarkRunner."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
import os
import sys
import tempfile

from aibugbench.io import fs as io_fs
from aibugbench.orchestration.runner import BenchmarkRunner
from aibugbench.validation.adapters.legacy_validator import LegacyValidatorAdapter

SUMMARY_PREFIX = "SUMMARY:"


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("AIBugBench CLI", add_help=False)
    p.add_argument("--prompt", default="p1")
    p.add_argument("--artifact", help="Explicit artifact output directory")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit summary but perform no work",
    )
    return p


def _default_validator_factory() -> Callable[[str], LegacyValidatorAdapter]:
    return lambda prompt: LegacyValidatorAdapter()


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    env = os.environ.copy()
    args_map = vars(args).copy()

    runner = BenchmarkRunner(
        validator_factory=_default_validator_factory(),
        env=env,
        fs=io_fs,
        args=args_map,
        default_artifact=tempfile.gettempdir(),  # nosec B108 - deterministic test fallback
    )

    summary = runner.run_once(args.prompt)

    summary_payload = {
        "status": summary.get("status", "ok"),
        "artifact": summary.get("artifact"),
    }
    print(f"{SUMMARY_PREFIX}{json.dumps(summary_payload)}")

    if summary.get("artifacts") and not args.dry_run:
        print("Benchmark artifacts written:")
        for name, location in summary["artifacts"].items():
            print(f"  - {name}: {location}")

    if not args.dry_run:
        sys.stdout.flush()


if __name__ == "__main__":
    main()
