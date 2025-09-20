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
import pathlib
import sys
import traceback
import typing as t

from setuptools import build_meta as _orig

_FIND_PATCHED = False


def _patch_find() -> None:
    """Wrap setuptools.build_meta._find_info_directory to log candidates on AssertionError.

    Best-effort and idempotent. We avoid raising from here; logging mirrors into the
    directory being scanned so artifacts can capture the evidence.
    """
    global _FIND_PATCHED
    if _FIND_PATCHED:
        return
    finder = getattr(_orig, "_find_info_directory", None)
    if finder is None:
        _FIND_PATCHED = True
        return

    def wrapped(suffix: str, directory: str):
        try:
            return finder(suffix, directory)
        except AssertionError:
            try:
                pattern = os.path.join(directory, f"*{suffix}")
                candidates = sorted(glob.glob(pattern))
                sys.stderr.write(
                    "[meta-debug] _find_info_directory AssertionError; "
                    f"candidates under {directory}: {candidates}\n"
                )
                # Persist alongside the directory being scanned
                out = os.path.join(directory, "_candidates_from_find.txt")
                with open(out, "w", encoding="utf-8") as f:
                    for c in candidates:
                        f.write(f"{c}\n")
            except Exception as exc:
                sys.stderr.write(
                    f"[meta-debug] failed writing _candidates_from_find.txt in {directory}: {exc}\n"
                )
            traceback.print_exc(file=sys.stderr)
            raise

    _orig._find_info_directory = wrapped  # type: ignore[attr-defined]
    _FIND_PATCHED = True


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


def _dump_all_egg_info(search_root: str, also_write_into: str | None = None) -> list[str]:
    """Find all *.egg-info under search_root recursively; log and persist best-effort.

    Returns the list of candidate paths. If also_write_into is provided, writes the same
    list into also_write_into/_all_candidates.txt to increase chances of artifact capture.
    """
    pattern = os.path.join(search_root, "**", "*.egg-info")
    candidates = sorted(glob.glob(pattern, recursive=True))
    sys.stderr.write(
        f"[meta-debug] global *.egg-info candidates from {search_root}: {candidates}\n"
    )
    try:
        out_path = os.path.join(search_root, "_all_candidates.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for c in candidates:
                f.write(f"{c}\n")
    except Exception as exc:
        # Best-effort only; log minimally without altering failure semantics.
        sys.stderr.write(
            f"[meta-debug] failed writing _all_candidates.txt in {search_root}: {exc}\n"
        )
    if also_write_into:
        try:
            out2 = os.path.join(also_write_into, "_all_candidates.txt")
            with open(out2, "w", encoding="utf-8") as f:
                for c in candidates:
                    f.write(f"{c}\n")
        except Exception as exc:
            sys.stderr.write(
                f"[meta-debug] failed writing mirrored _all_candidates.txt in {also_write_into}: "
                f"{exc}\n"
            )
    return candidates


def _dump_tree(root: str, out_path: str | None = None) -> None:
    """Recursively list all files under root to stderr, optionally to a file."""
    try:
        lines: list[str] = []
        for p in pathlib.Path(root).rglob("*"):
            lines.append(str(p))
        if lines:
            sys.stderr.write(f"[meta-debug] tree for {root} (first 200 entries shown)\n")
            # Avoid spamming logs; show a subset and rely on file for full contents.
            for s in lines[:200]:
                sys.stderr.write(s + "\n")
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                for s in lines:
                    f.write(s + "\n")
    except Exception:
        # Best-effort only
        return


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: dict[str, t.Any] | None = None
) -> str:
    try:
        _patch_find()
        return t.cast(
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
        # Global diagnostic sweep from the current working directory and mirror into metadata dir.
        _dump_all_egg_info(os.getcwd(), also_write_into=metadata_directory)
        # Dump a tree of the metadata directory to a file for artifact collection.
        _dump_tree(metadata_directory, os.path.join(metadata_directory, "_tree.txt"))
        # Print full traceback for precise failure location in setuptools.
        traceback.print_exc(file=sys.stderr)
        raise


def prepare_metadata_for_build_editable(
    metadata_directory: str, config_settings: dict[str, t.Any] | None = None
) -> str:
    try:
        _patch_find()
        return t.cast(
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
        _dump_all_egg_info(os.getcwd(), also_write_into=metadata_directory)
        _dump_tree(metadata_directory, os.path.join(metadata_directory, "_tree.txt"))
        traceback.print_exc(file=sys.stderr)
        raise


# Delegate remaining hooks directly to setuptools.build_meta
def get_requires_for_build_wheel(config_settings: dict[str, t.Any] | None = None):
    return _orig.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_editable(config_settings: dict[str, t.Any] | None = None):
    return _orig.get_requires_for_build_editable(config_settings)


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, t.Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return t.cast(str, _orig.build_wheel(wheel_directory, config_settings, metadata_directory))


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, t.Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return t.cast(str, _orig.build_editable(wheel_directory, config_settings, metadata_directory))


def build_sdist(sdist_directory: str, config_settings: dict[str, t.Any] | None = None) -> str:
    return t.cast(str, _orig.build_sdist(sdist_directory, config_settings))
