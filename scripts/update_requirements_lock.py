#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

JSON_MODE = False
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


def _say(msg: str) -> None:
    # Keep human chatter off stdout in --json mode
    if JSON_MODE:
        print(msg, file=sys.stderr)
    else:
        print(msg)


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


# --- normalization regexes for diff-compare (module scope to satisfy Ruff N806)
_VIA_RE = re.compile(r"^# via (.+)$")
_HDR_BY_CMD: re.Pattern[str] = re.compile(r"^\s*#\s*by the following command:\s*$", re.I)
_HDR_CMD: re.Pattern[str] = re.compile(r"^\s*#\s*pip-compile\b", re.I)
_ANY_VIA: re.Pattern[str] = re.compile(r"^\s*#\s*via\b.*$", re.I)


def _write_unix(path: Path, text: str) -> None:
    """Write with LF newlines so locks are byte-stable across OS."""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _seed_output_from_lock(src: Path, dst: Path) -> None:
    """Pre-fill the temp output with the current lock so pip-compile preserves pins."""
    try:
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        shutil.copy2(src, dst)


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


def _norm_for_compare(text: str) -> list[str]:
    """Canonicalize lock text for drift comparison.
    - normalize CRLF/CR to LF
    - drop the volatile 'by the following command' header line
      and the immediately following '# pip-compile ...' line
    - collapse any '# via ...' line to a single '# via'
    - strip trailing whitespace
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        ln = lines[i].rstrip()

        # Check for header marker and skip it with optional pip-compile line
        if _HDR_BY_CMD.match(ln):
            i += 1  # skip the header line
            # Skip blank comment lines and find the pip-compile line
            while i < n:
                next_line = lines[i].rstrip()
                if _HDR_CMD.match(next_line):
                    i += 1  # skip the pip-compile line
                    break
                elif next_line in ("", "#"):  # type: ignore[unreachable]
                    i += 1  # skip blank/empty comment lines
                else:
                    break  # found non-header content, stop skipping
        elif _ANY_VIA.match(ln):  # type: ignore[unreachable]
            # Collapse provenance noise
            out.append("# via")
            i += 1
        else:
            out.append(ln)
            i += 1

    # Drop trailing blank lines introduced by split when text ends with a newline
    while out and out[-1] == "":
        out.pop()

    return out


def compile_lock(req: Path, output: Path, allow_unsafe: bool, strip_platform: bool) -> int:
    """Run pip-tools compile producing the given output path for req file.
    Uses relative requirement filename (stable across platforms) and injects a
    --custom-compile-command so the header in the generated lock file matches
    the committed canonical command. This keeps diffs stable between Linux,
    macOS, and Windows (avoids absolute path leakage).
    If allow_unsafe=True, adds --allow-unsafe to capture tooling packages
    like pip/setuptools/wheel (useful for reproducible isolated environments).
    """
    _say(f"Using pip-tools to generate hash-pinned lock for {req.name}...")
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
    """
    Updates or checks the consistency of
    requirements.lock files based on specified options and flags.
    :return: The `main()` function returns an integer exit code, which indicates the status of the
    script execution. The possible return values and their meanings are defined in the
    `EXIT_CODE_LEGEND` dictionary. The exit code is then used to determine the meaning of the return
    value and is printed along with its corresponding description before the script exits.
    """
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit single-line JSON status instead of human text",
    )
    args = parser.parse_args()
    global JSON_MODE
    JSON_MODE = args.json

    def _emit_json(payload: dict) -> None:
        print(json.dumps(payload, ensure_ascii=False))

    req = REQ_DEV if args.dev else REQ_RUNTIME
    lock = LOCK_DEV if args.dev else LOCK_RUNTIME

    if not req.exists():
        if args.json:
            _emit_json(
                {
                    "tool": "lock-check",
                    "lock": lock.name,
                    "status": "error",
                    "exit": 1,
                    "error": f"{req.name} not found",
                }
            )
        else:
            _say(f"{req} not found")
        return 1

    if not lock.exists() and args.check:
        _say(f"{lock} missing (cannot --check). Run without --check first.")
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
            if args.json:
                _emit_json(
                    {
                        "tool": "lock-check",
                        "lock": lock.name,
                        "status": "error",
                        "exit": 2,
                        "error": "pip-tools not found",
                    }
                )
                return 2

            _say("pip-tools not found. Install with: pip install 'pip-tools==7.5.0'")
            return 2

    # Canonical policy: always include unsafe packages to avoid resolver drift.
    allow_unsafe = not args.no_allow_unsafe
    strip_platform = not args.keep_platform_markers

    if args.check:
        # Check mode: compile to a temp file, compare, and return 0/3
        with tempfile.TemporaryDirectory() as td:
            tmp_lock = Path(td) / "_lock.tmp"
            _seed_output_from_lock(lock, tmp_lock)
            code = compile_lock(req, tmp_lock, allow_unsafe, strip_platform)
            if code != 0:
                return code
            new_content = _norm_for_compare(tmp_lock.read_text(encoding="utf-8"))
        old_content = _norm_for_compare(lock.read_text(encoding="utf-8"))
        if old_content != new_content:
            if args.json:
                _emit_json(
                    {
                        "tool": "lock-check",
                        "lock": lock.name,
                        "status": "drift",
                        "exit": 3,
                        "artifact_hint": f"artifacts/new.{lock.name}",
                    }
                )
            else:
                _say(f"{lock.name} is OUT OF DATE with {req.name}")
            return 3
        if args.json:
            _emit_json({"tool": "lock-check", "lock": lock.name, "status": "ok", "exit": 0})
        else:
            _say(f"{lock.name} up to date")
        return 0
    else:
        # Update mode: write the real lock file and return compiler rc
        code = compile_lock(req, lock, allow_unsafe, strip_platform)
        if code == 0:
            _say(f"wrote {lock}")
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
    # In JSON mode, do not write a footer to stdout
    if not JSON_MODE:
        print(f"Exit code {rc}: {meaning}")
    sys.exit(rc)
