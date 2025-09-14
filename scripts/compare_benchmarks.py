#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Cross-platform benchmark results consistency checker.

Reads JSON files named platform_validation_*.json from a supplied results directory
(default: ./collected-results) and verifies that total scores are within a small
tolerance across platforms. Prints a summary and exits non-zero if inconsistency
is detected.

CLI:
  --dir PATH           Directory containing platform_validation_*.json
  --tolerance FLOAT    Allowed absolute difference (default 0.01)
  --percent            Treat tolerance as a percentage of the max score
  --require NAME       Require one or more platforms (repeat or comma-separated)
  --no-emoji           Suppress emoji in output
  --gha-summary        Also write a brief summary to $GITHUB_STEP_SUMMARY
  --json               Emit a one-line JSON summary to stdout

Environment defaults (overridden by CLI flags):
  AIBB_RESULTS_DIR, AIBB_TOLERANCE, AIBB_TOLERANCE_PERCENT=1,
  AIBB_REQUIRE (comma list), AIBB_NO_EMOJI=1, AIBB_GHA_SUMMARY=1, AIBB_JSON=1
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any

DEFAULT_DIR = Path("./collected-results")
DEFAULT_TOL = 0.01  # maximum allowed absolute difference in total scores


@dataclass(frozen=True)
class ScoreRow:
    platform: str
    total: float


def _repo_root() -> Path:
    """Return first ancestor containing .git or pyproject.toml, else CWD."""
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return here


def _coerce_bool_env(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="compare_benchmarks",
        description=(
            "Compare platform_validation_*.json totals across platforms and "
            "fail if the difference exceeds the tolerance."
        ),
    )
    env_dir = Path(os.environ.get("AIBB_RESULTS_DIR", DEFAULT_DIR))
    env_tol = os.environ.get("AIBB_TOLERANCE")
    env_tol_val = float(env_tol) if env_tol is not None else DEFAULT_TOL
    env_percent = _coerce_bool_env(os.environ.get("AIBB_TOLERANCE_PERCENT"))
    env_require = os.environ.get("AIBB_REQUIRE")
    env_require_list = (
        [p.strip() for p in env_require.split(",") if p.strip()] if env_require else []
    )
    env_no_emoji = _coerce_bool_env(os.environ.get("AIBB_NO_EMOJI"))
    env_gha_summary = _coerce_bool_env(os.environ.get("AIBB_GHA_SUMMARY"))
    env_json = _coerce_bool_env(os.environ.get("AIBB_JSON"))

    parser.add_argument(
        "--dir",
        default=str(env_dir),
        metavar="PATH",
        help=f"Directory containing platform_validation_*.json (default: {env_dir})",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=env_tol_val,
        metavar="FLOAT",
        help=f"Maximum allowed absolute score difference (default: {env_tol_val})",
    )
    parser.add_argument(
        "--percent",
        action="store_true",
        default=env_percent,
        help="Interpret tolerance as percentage of the max score instead of absolute.",
    )
    parser.add_argument(
        "--require",
        action="append",
        default=env_require_list,
        metavar="PLATFORM",
        help="Require platforms to be present (repeatable or comma-separated).",
    )
    parser.add_argument(
        "--no-emoji",
        action="store_true",
        default=env_no_emoji,
        help="Suppress emoji in output.",
    )
    parser.add_argument(
        "--gha-summary",
        action="store_true",
        default=env_gha_summary,
        help="Write a brief summary to $GITHUB_STEP_SUMMARY if available.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=env_json,
        help="Emit a one-line JSON summary to stdout.",
    )

    args = parser.parse_args()

    # Normalize require list
    req: list[str] = []
    for item in args.require or []:
        req.extend([p.strip() for p in str(item).split(",") if p.strip()])
    args.require = req

    if args.tolerance < 0:
        parser.error("--tolerance must be non-negative")
    return args


def _discover_files(results_dir: Path) -> list[Path]:
    return sorted(results_dir.glob("platform_validation_*.json"))


def _platform_from_filename(p: Path) -> str:
    name = p.stem
    parts = name.split("platform_validation_", 1)
    return parts[1] if len(parts) == 2 else name


def _extract_total(payload: Mapping[str, Any]) -> float:
    if "total_score" in payload and isinstance(payload["total_score"], (int | float)):
        return float(payload["total_score"])
    if "total" in payload and isinstance(payload["total"], (int | float)):
        return float(payload["total"])
    if "totals" in payload and isinstance(payload["totals"], Mapping):
        t = payload["totals"].get("total")
        if isinstance(t, (int | float)):
            return float(t)
    if "summary" in payload and isinstance(payload["summary"], Mapping):
        t = payload["summary"].get("total")
        if isinstance(t, (int | float)):
            return float(t)
    raise ValueError("Could not find a numeric 'total' in results JSON")


def load_results(results_dir: Path) -> list[ScoreRow]:
    files = _discover_files(results_dir)
    rows: list[ScoreRow] = []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            total = _extract_total(data)
            rows.append(ScoreRow(platform=_platform_from_filename(fp), total=total))
        except Exception as e:
            raise RuntimeError(f"Failed to parse {fp}: {e}") from e
    return rows


def _check_required_platforms(
    rows: list[ScoreRow], required: Iterable[str]
) -> tuple[bool, list[str]]:
    have = {r.platform for r in rows}
    missing = [r for r in required if r not in have]
    return (len(missing) == 0, missing)


def _compute_ok(
    rows: list[ScoreRow], tol: float, use_percent: bool
) -> tuple[bool, float, float, float]:
    if not rows:
        return True, 0.0, 0.0, 0.0
    vals = [r.total for r in rows]
    min_v, max_v = min(vals), max(vals)
    diff = max_v - min_v
    if use_percent:
        basis = max(abs(max_v), 1e-12)
        pct = (diff / basis) * 100.0
        return (pct <= tol), min_v, max_v, pct
    else:
        return (diff <= tol), min_v, max_v, diff


def _fmt_ok(ok: bool, no_emoji: bool) -> str:
    if no_emoji:
        return "OK" if ok else "FAIL"
    return ("✅" if ok else "❌") + " " + ("OK" if ok else "FAIL")


def _write_gha_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
    except Exception as exc:  # pragma: no cover - non-critical best-effort
        logging.debug("Failed to append to GITHUB_STEP_SUMMARY: %s", exc)


def summarize(
    rows: list[ScoreRow],
    tol: float = DEFAULT_TOL,
    use_percent: bool = False,
    no_emoji: bool = False,
    gha_summary: bool = False,
    as_json: bool = False,
    required: Iterable[str] | None = None,
) -> int:
    required = list(required or [])
    ok_req, missing = _check_required_platforms(rows, required)
    ok_comp, min_v, max_v, delta = _compute_ok(rows, tol, use_percent)

    platforms = ", ".join(sorted({r.platform for r in rows})) or "(none)"
    unit = "%" if use_percent else "abs"
    status = ok_req and ok_comp
    header = (
        f"{_fmt_ok(status, no_emoji)}  platforms=[{platforms}]  "
        f"tol={tol:.4g}{unit}  delta={delta:.4g}{unit}"
    )

    print(header)
    for r in sorted(rows, key=lambda x: x.platform):
        print(f"  - {r.platform}: {r.total:.6g}")
    if missing:
        print(f"  missing required: {', '.join(missing)}")

    if as_json:
        payload = {
            "ok": status,
            "ok_platforms": ok_req,
            "ok_tolerance": ok_comp,
            "min": min_v,
            "max": max_v,
            "delta": delta,
            "tolerance": tol,
            "unit": unit,
            "platforms": {r.platform: r.total for r in rows},
            "missing": missing,
        }
        print(json.dumps(payload, ensure_ascii=False))

    if gha_summary:
        lines = [
            f"### Benchmark consistency: {'OK' if status else 'FAIL'}",
            "",
            f"- Platforms: {platforms}",
            f"- Tolerance: {tol:.4g}{unit}",
            f"- Delta: {delta:.4g}{unit}",
        ]
        if missing:
            lines.append(f"- Missing required: {', '.join(missing)}")
        _write_gha_summary(lines)

    return 0 if status else 1


def main() -> int:
    args = _parse_args()
    if not sys.stdout.isatty():
        args.no_emoji = True  # auto-disable emoji in non-TTY

    results_dir = Path(args.dir)
    # Reject glob metacharacters before resolution
    if any(ch in str(results_dir) for ch in "*?[]"):
        print(
            _fmt_ok(False, bool(getattr(args, "no_emoji", False)))
            + "  invalid --dir contains glob metacharacters"
        )
        return 1

    base = _repo_root()
    rd = (results_dir if results_dir.is_absolute() else (base / results_dir)).resolve()
    if not rd.is_dir():
        print(_fmt_ok(False, args.no_emoji) + f"  results directory does not exist: {rd}")
        return 1
    try:
        if not rd.is_relative_to(base):  # Python 3.9+
            print(
                _fmt_ok(False, args.no_emoji)
                + f"  results dir escapes repo root: {rd} (base={base})"
            )
            return 1
    except AttributeError:  # pragma: no cover
        if base not in [rd, *rd.parents]:
            print(
                _fmt_ok(False, args.no_emoji)
                + f"  results dir escapes repo root: {rd} (base={base})"
            )
            return 1
    results_dir = rd

    rows = load_results(results_dir)
    if not rows and args.require:
        print(_fmt_ok(False, args.no_emoji) + "  no result files found")
        return 1
    return summarize(
        rows,
        tol=float(args.tolerance),
        use_percent=bool(args.percent),
        no_emoji=bool(args.no_emoji),
        gha_summary=bool(args.gha_summary),
        as_json=bool(args.json),
        required=list(args.require),
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
