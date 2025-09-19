"""
Temporary in-tree PEP 517 build backend wrapper.

Purpose: Intercept setuptools.build_meta metadata hooks to print and persist
the candidate *.egg-info directories when setuptools raises the
"Multiple .egg-info directories found" assertion. This helps diagnose
the duplicate emission in CI across platforms.

Implementation notes:
- Delegates all hooks to setuptools.build_meta.
- On AssertionError from prepare_metadata_for_build_wheel/editable, it lists
  candidates in the provided metadata_directory, prints them to stderr, and
  writes a _candidates.txt file alongside for artifact collection.

Safe to remove once the root cause is fixed; then set build-backend back to
"setuptools.build_meta" and remove backend-path from pyproject.toml.
"""

from __future__ import annotations

import glob
import io
import os
import sys
from typing import Any, cast

from setuptools import build_meta as _orig


def _dump_dir(label: str, path: str) -> None:
    """Best-effort directory listing to stderr; never raises."""
    try:
        buf = io.StringIO()
        buf.write(f"[meta-debug] {label}: {path}\n")
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                p = os.path.join(path, name)
                tag = "/" if os.path.isdir(p) else ""
                buf.write(f"  - {name}{tag}\n")
        else:
            buf.write("  <not a directory>\n")
        sys.stderr.write(buf.getvalue())
    except Exception as _exc:  # best-effort diagnostics only
        # Intentionally silent to avoid masking the original backend error.
        # We still want to keep the build failure semantics unchanged.
        return


def _persist_candidates(metadata_directory: str, candidates: list[str]) -> None:
    """Write candidates into metadata_directory/_candidates.txt; best-effort."""
    try:
        out_path = os.path.join(metadata_directory, "_candidates.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for c in candidates:
                f.write(f"{c}\n")
    except Exception:
        # Best-effort; ignore write failures.
        return


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    try:
        return cast(
            str,
            _orig.prepare_metadata_for_build_wheel(metadata_directory, config_settings),
        )
    except AssertionError:
        pattern = os.path.join(metadata_directory, "*.egg-info")
        candidates = sorted(glob.glob(pattern))
        sys.stderr.write(
            f"[meta-debug] AssertionError in prepare_metadata_for_build_wheel; "
            f"candidates for *.egg-info in {metadata_directory}: {candidates}\n"
        )
        _dump_dir("metadata_directory listing", metadata_directory)
        _persist_candidates(metadata_directory, candidates)
        raise


def prepare_metadata_for_build_editable(
    metadata_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    try:
        return cast(
            str,
            _orig.prepare_metadata_for_build_editable(metadata_directory, config_settings),
        )
    except AssertionError:
        pattern = os.path.join(metadata_directory, "*.egg-info")
        candidates = sorted(glob.glob(pattern))
        sys.stderr.write(
            f"[meta-debug] AssertionError in prepare_metadata_for_build_editable; "
            f"candidates for *.egg-info in {metadata_directory}: {candidates}\n"
        )
        _dump_dir("metadata_directory listing", metadata_directory)
        _persist_candidates(metadata_directory, candidates)
        raise


# Delegate remaining hooks directly to setuptools.build_meta
def get_requires_for_build_wheel(config_settings: dict[str, Any] | None = None):
    return _orig.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_editable(config_settings: dict[str, Any] | None = None):
    return _orig.get_requires_for_build_editable(config_settings)


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return cast(str, _orig.build_wheel(wheel_directory, config_settings, metadata_directory))


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return cast(str, _orig.build_editable(wheel_directory, config_settings, metadata_directory))


def build_sdist(sdist_directory: str, config_settings: dict[str, Any] | None = None) -> str:
    return cast(str, _orig.build_sdist(sdist_directory, config_settings))
