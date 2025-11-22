"""Capture Prompt 2 legacy analysis and persist it as the golden fixture.

This script runs the monolithic Prompt 2 validator defined in LEGACY_validators.py
against the reference submission and writes the raw legacy output to
``tests/fixtures/prompt2/legacy_analysis.json``.

Usage (from repo root):

    python scripts/capture_prompt2_legacy_fixture.py

Optional flags let you override the legacy module path, reference directory,
output location, or test-data directory.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DEFAULT_LEGACY = REPO_ROOT / "LEGACY_validators.py"
DEFAULT_REFERENCE = REPO_ROOT / "submissions" / "reference_implementations" / "example_model"
DEFAULT_OUTPUT = REPO_ROOT / "tests" / "fixtures" / "prompt2" / "legacy_analysis.json"
DEFAULT_TEST_DATA = REPO_ROOT / "test_data"


def load_legacy_validators(path: Path) -> Any:
    """Dynamically load the legacy validators module from an arbitrary path."""

    if not path.exists():
        raise FileNotFoundError(f"Legacy validators file not found: {path}")

    module_name = "benchmark.legacy_prompt2_capture"
    benchmark_pkg = importlib.import_module("benchmark")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {path}")

    module = importlib.util.module_from_spec(spec)
    module.__package__ = "benchmark"
    sys.modules.setdefault("benchmark", benchmark_pkg)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--legacy", type=Path, default=DEFAULT_LEGACY, help="Path to LEGACY_validators.py"
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=DEFAULT_REFERENCE,
        help="Directory containing prompt_2_config_fixed.yaml and prompt_2_config.json",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination JSON file")
    parser.add_argument(
        "--test-data", type=Path, default=DEFAULT_TEST_DATA, help="test_data directory"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    os.environ.setdefault("AIBUGBENCH_UNSAFE", "true")

    module = load_legacy_validators(args.legacy)
    try:
        prompt_validators = module.PromptValidators(args.test_data)
    except AttributeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("LEGACY_validators.py is missing PromptValidators") from exc

    yaml_path = args.reference_dir / "prompt_2_config_fixed.yaml"
    json_path = args.reference_dir / "prompt_2_config.json"
    if not yaml_path.exists() or not json_path.exists():
        raise FileNotFoundError("Reference Prompt 2 files are missing; ensure example_model exists")

    analysis = prompt_validators.validate_prompt_2_yaml_json(yaml_path, json_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote legacy analysis to {args.output}")


if __name__ == "__main__":
    main()
