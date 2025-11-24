# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Helpers for locating Prompt 2 submission files."""

from __future__ import annotations

from pathlib import Path

from aibugbench.validation.errors import SchemaError

YAML_NAME = "prompt_2_config_fixed.yaml"
JSON_NAME = "prompt_2_config.json"
_YML_ALTERNATE = "prompt_2_config_fixed.yml"


def find_prompt2_files(run_dir: Path) -> tuple[Path, Path]:
    """Return absolute paths to the Prompt 2 YAML and JSON submissions.

    Raises:
        SchemaError: if the expected files are missing or misnamed.
    """

    root = Path(run_dir).resolve()
    yaml_path = root / YAML_NAME
    json_path = root / JSON_NAME

    if not yaml_path.exists():
        alternate = root / _YML_ALTERNATE
        if alternate.exists():
            raise SchemaError(f"Prompt 2 YAML must be named {YAML_NAME} (found {_YML_ALTERNATE}).")
        raise SchemaError(f"Missing Prompt 2 YAML submission: {YAML_NAME}")

    if yaml_path.suffix.lower() not in {".yaml"}:
        raise SchemaError(f"Prompt 2 YAML must use .yaml extension (got {yaml_path.suffix}).")

    if not json_path.exists():
        raise SchemaError(f"Missing Prompt 2 JSON submission: {JSON_NAME}")

    if json_path.suffix.lower() != ".json":
        raise SchemaError(f"Prompt 2 JSON must use .json extension (got {json_path.suffix}).")

    return yaml_path, json_path


__all__ = ["JSON_NAME", "YAML_NAME", "find_prompt2_files"]
