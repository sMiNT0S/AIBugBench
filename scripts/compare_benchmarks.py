"""Cross-platform benchmark results consistency checker.

Reads JSON files named platform_validation_*.json from a supplied results directory
(default: ./collected-results) and verifies that total scores are within a small
floating tolerance across platforms. Prints a summary and exits non-zero if
inconsistency is detected.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

TOLERANCE = 0.01  # allowable absolute score difference
RESULTS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./collected-results")


def load_results(results_dir: Path) -> list[dict[str, Any]]:
    platform_results: list[dict[str, Any]] = []
    if not results_dir.exists():
        print("⚠️ Results directory does not exist:", results_dir)
        return platform_results
    for result_file in results_dir.glob("platform_validation_*.json"):
        try:
            with result_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            platform_results.append(data)
            print(
                f"✅ Loaded results for {data.get('platform', 'unknown')}: "
                f"{data.get('total_score', 0):.2f}/100"
            )
        except Exception as e:
            print(f"❌ Failed to load {result_file}: {e}")
    return platform_results


def summarize(platform_results: list[dict[str, Any]]) -> int:
    if len(platform_results) < 2:
        print("⚠️ Insufficient platform results for comparison")
        return 0

    scores = [r.get("total_score", 0.0) for r in platform_results]
    platforms = [r.get("platform", "unknown") for r in platform_results]

    min_score = min(scores)
    max_score = max(scores)
    diff = max_score - min_score
    print(f"📊 Score range: {min_score:.2f} - {max_score:.2f} (diff: {diff:.2f})")

    if diff > TOLERANCE:
        print("❌ INCONSISTENT SCORES DETECTED!")
        print("Platform scores:", dict(zip(platforms, scores, strict=False)))
        return 1

    print("✅ All platform scores are consistent within tolerance.")

    # Optional timing stats
    times = [
        r.get("full_results", {}).get("execution_time", 0.0)
        for r in platform_results
        if "full_results" in r
    ]
    if times:
        avg_time = sum(times) / len(times)
        print(f"⏱️ Average execution time: {avg_time:.2f}s")
        for platform, t in zip(platforms, times, strict=False):
            deviation = abs(t - avg_time) / avg_time * 100 if avg_time else 0.0
            print(f"   {platform}: {t:.2f}s ({deviation:.1f}% from avg)")

    return 0


def main() -> int:
    results = load_results(RESULTS_DIR)
    return summarize(results)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
