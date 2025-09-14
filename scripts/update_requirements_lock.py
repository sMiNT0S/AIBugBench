#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import packaging.version as _pkgver
except Exception:  # pragma: no cover
    _pkgver = None

ROOT = Path(__file__).resolve().parent.parent
REQ_RUNTIME = ROOT / "requirements.txt"
LOCK_RUNTIME = ROOT / "requirements.lock"
REQ_DEV = ROOT / "requirements-dev.txt"
LOCK_DEV = ROOT / "requirements-dev.lock"

# Canonical ephemeral output name used in CI diff job. We embed this in the
# header even though the committed file is requirements.lock so that local
# runs and CI produce byte-identical files.
CANONICAL_OUTPUT_NAME = "new.requirements.lock"


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=str(ROOT))  # noqa


def _require_modern_piptools() -> str | None:
    try:
        if _pkgver is None:
            return None
        import importlib.metadata as _im

        ver = _pkgver.Version(_im.version("pip-tools"))
        if ver >= _pkgver.Version("7.5.0"):
            return str(ver)
        return None
    except Exception:  # pragma: no cover
        return None


def _rewrite_header(lock_path: Path, req_name: str, allow_unsafe: bool = True) -> None:
    """Normalize header comment to canonical form used by CI.

    CI generates an ephemeral file via:
        pip-compile --allow-unsafe --generate-hashes \
            --output-file=new.requirements.lock requirements.txt

    We intentionally mirror this exact command (argument ordering included)
    inside the committed lock for deterministic diffs.
    """
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return
    desired = (
        f"#    pip-compile"
        f"{' --allow-unsafe' if allow_unsafe else ''}"
        f" --generate-hashes --output-file={CANONICAL_OUTPUT_NAME} {req_name}\n"
    )
    for _idx, line in enumerate(lines):
        if line.startswith("#    pip-compile"):
            if line != desired:
                lines[_idx] = desired
                _write_unix(lock_path, "".join(lines))
            break


def _strip_platform_specific(lock_path: Path) -> None:
    """Remove Windows-only requirement blocks for deterministic cross-OS locks.

    Strips any requirement line containing one of:
      ; sys_platform == "win32"  |  'win32'
      ; platform_system == "Windows"  |  'Windows'
    Also removes the immediately following indented hash lines (    --hash=...).
    """
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    out: list[str] = []
    skip_hashes = False
    win_marker = re.compile(
        r""";\s*(?:sys_platform\s*==\s*['"]win32['"]|platform_system\s*==\s*['"]Windows['"])"""
    )
    for line in lines:
        is_hash_line = line.startswith("    --hash=")
        is_win_marked = bool(win_marker.search(line))
        if skip_hashes and is_hash_line:
            # skip hash lines immediately following a removed Windows-only requirement
            continue
        if is_win_marked:
            # drop the Windows-only requirement line and enable hash skipping
            skip_hashes = True
            continue
        out.append(line)
        if skip_hashes and not is_hash_line:
            # first non-hash line after skipping hash lines -> reset
            skip_hashes = False
    if out != lines:
        # splitlines() above dropped newlines; re-add a trailing LF for stability
        _write_unix(lock_path, "\n".join(out) + "\n")


def _dedupe_provenance(lock_path: Path) -> None:
    """Remove redundant provenance lines like '# via -r requirements.txt'.

    On some platforms (observed on Windows) pip-compile emits an extra line
    `# via -r requirements.txt` immediately following an existing
    `# via <package>` provenance comment for the same requirement. On Linux
    (CI) only the more specific `# via <package>` line is produced. This
    causes deterministic drift in the lock verification job. We normalize by
    dropping the generic root file provenance when it directly follows *any*
    other provenance comment line. (If a requirement is *directly* specified
    in requirements.txt and has no other provenance, pip-compile will emit
    only the `# via -r requirements.txt` line and we retain it.)
    """
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:  # pragma: no cover
        return
    out: list[str] = []
    for _i, line in enumerate(lines):
        if line.strip() == "# via -r requirements.txt":
            # Look backwards for previous non-empty, non-hash lines pertaining to provenance
            j = len(out) - 1
            while j >= 0 and out[j].strip() == "":
                j -= 1
            if (
                j >= 0
                and out[j].lstrip().startswith("# via ")
                and (
                    out[j].strip() != "# via -r requirements.txt" or out[j].strip() == line.strip()
                )
            ):
                # Redundant generic provenance -> skip
                continue
        out.append(line)
    if out != lines:
        _write_unix(lock_path, "".join(out))


_VIA_RE = re.compile(r"^# via (.+)$")


def _write_unix(path: Path, text: str) -> None:
    """Write with LF newlines so locks are byte-stable across OS."""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _canonicalize_via_lines(lock_path: Path) -> None:
    """Normalize '# via ...' comment lines so ordering is stable across OS."""
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# via ") and stripped != "# via -r requirements.txt":
            payload = stripped[len("# via ") :]
            # Split on commas, trim, sort, rejoin with single spaces after comma.
            parts = [p.strip() for p in payload.split(",")]
            parts = [p for p in parts if p]  # drop empties
            payload = ", ".join(sorted(dict.fromkeys(parts)))
            line = f"# via {payload}\n"
        out.append(line)
    if out != lines:
        _write_unix(lock_path, "".join(out))


def compile_lock(req: Path, output: Path, allow_unsafe: bool, strip_platform: bool) -> int:
    """Run pip-tools compile producing the given output path for req file.

    Uses relative requirement filename (stable across platforms) and injects a
    --custom-compile-command so the header in the generated lock file matches
    the committed canonical command. This keeps diffs stable between Linux,
    macOS, and Windows (avoids absolute path leakage).

    If allow_unsafe=True, adds --allow-unsafe to capture tooling packages
    like pip/setuptools/wheel (useful for reproducible isolated environments).
    """
    print(f"Using pip-tools to generate hash-pinned lock for {req.name}...")
    if _require_modern_piptools() is None:
        print(
            "pip-tools ==7.5.0 required. Install with: pip install -U 'pip-tools==7.5.0'",
            file=sys.stderr,
        )
        return 4
    cmd: list[str] = [sys.executable, "-m", "piptools", "compile"]
    if allow_unsafe:
        # ordering chosen to match committed header (allow-unsafe precedes generate-hashes)
        cmd.append("--allow-unsafe")
    cmd.extend(["--generate-hashes", "-o", str(output), req.name])
    rc = run(cmd)
    if rc == 0:
        _rewrite_header(output, req.name, allow_unsafe=allow_unsafe)
        if strip_platform:
            _strip_platform_specific(output)
        _dedupe_provenance(output)
        _canonicalize_via_lines(output)
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update or check requirements(.lock) consistency (runtime or dev)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if requirements.lock is out of date (no write)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Operate on requirements-dev.txt / requirements-dev.lock instead of runtime",
    )
    parser.add_argument(
        "--no-allow-unsafe",
        action="store_true",
        help=(
            "Exclude unsafe packages (pip, setuptools, wheel). Default: include for reproducibility"
        ),
    )
    parser.add_argument(
        "--keep-platform-markers",
        action="store_true",
        help="Do not strip platform-specific (e.g. win32) requirement blocks",
    )
    args = parser.parse_args()

    req = REQ_DEV if args.dev else REQ_RUNTIME
    lock = LOCK_DEV if args.dev else LOCK_RUNTIME

    if not req.exists():
        print(f"{req} not found", file=sys.stderr)
        return 1

    if not lock.exists() and args.check:
        print(f"{lock} missing (cannot --check). Run without --check first.", file=sys.stderr)
        return 1

    piptools = shutil.which("pip-compile") or shutil.which("piptools")
    if not piptools:
        # Try local venv Scripts (Windows) / bin (POSIX) directly
        if sys.platform.startswith("win"):
            candidate = ROOT / "venv" / "Scripts" / "pip-compile.exe"
        else:
            candidate = ROOT / "venv" / "bin" / "pip-compile"
        if candidate.exists():
            piptools = str(candidate)
        else:
            print(
                "pip-tools not found. Install with: pip install 'pip-tools==7.5.0'",
                file=sys.stderr,
            )
            return 2

    # Canonical policy: always include unsafe packages to avoid resolver drift.
    allow_unsafe = not args.no_allow_unsafe
    strip_platform = not args.keep_platform_markers

    if args.check:
        # Canonical, in-memory compare (normalize LF + sorted '# via …')
        def _norm_for_compare(text: str) -> list[str]:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            out: list[str] = []
            for ln in text.split("\n"):
                m = _VIA_RE.match(ln.strip())
                if m and m.group(1) != "-r requirements.txt":
                    parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
                    ln = f"# via {', '.join(sorted(dict.fromkeys(parts)))}"
                out.append(ln.rstrip())
            return out

        with tempfile.TemporaryDirectory() as td:
            tmp_lock = Path(td) / "_lock.tmp"
            code = compile_lock(req, tmp_lock, allow_unsafe, strip_platform)
            if code != 0:
                return code
            new_content = _norm_for_compare(tmp_lock.read_text(encoding="utf-8"))

        old_content = _norm_for_compare(lock.read_text(encoding="utf-8"))
        if new_content != old_content:
            print(f"{lock.name} is OUT OF DATE with {req.name}", file=sys.stderr)
            diff_iter = difflib.unified_diff(
                old_content,
                new_content,
                fromfile=str(lock.name),
                tofile="(recompiled)",
                lineterm="",
            )
            diff_lines: list[str] = []
            for i, line in enumerate(diff_iter):
                if i > 400:  # safety cut
                    print("... diff truncated ...", file=sys.stderr)
                    break
                print(line.rstrip(), file=sys.stderr)
                diff_lines.append(line)
            added = sum(1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++"))
            removed = sum(1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---"))
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path:
                try:
                    with open(summary_path, "a", encoding="utf-8") as fh:
                        fh.write(f"Lock drift: {lock.name} (+{added} -{removed})\n")
                except Exception as exc:
                    print(f"Warning: failed writing summary: {exc}", file=sys.stderr)
            print(
                "Run: python scripts/update_requirements_lock.py"
                + (" --dev" if args.dev else "")
                + (" --no-allow-unsafe" if args.no_allow_unsafe else "")
                + (" --keep-platform-markers" if args.keep_platform_markers else "")
                + " to refresh.",
                file=sys.stderr,
            )
            return 3
        print(f"{lock.name} up to date")
        return 0

    # Update mode (write lock)
    code = compile_lock(req, lock, allow_unsafe, strip_platform)
    if code == 0:
        print(f"wrote {lock}")
    return code


EXIT_CODE_LEGEND = {
    0: "up to date or successful write",
    1: "missing files / basic error",
    2: "pip-tools missing",
    3: "drift detected in --check",
    4: "pip-tools too old (<7.5.0)",
}

if __name__ == "__main__":
    rc = main()
    meaning = EXIT_CODE_LEGEND.get(rc, "(unknown)")
    print(f"Exit code {rc}: {meaning}")
    sys.exit(rc)
