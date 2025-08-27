#!/usr/bin/env python3
"""Lightweight structural smoke test for AICodeBenchmark.

Avoids dynamic exec() and only inspects the imported class for a few expected
methods. This keeps lint noise minimal while providing a quick sanity check.
"""
from __future__ import annotations

import inspect

from run_benchmark import AICodeBenchmark


def main() -> None:  # pragma: no cover - simple debug aid
    methods = {name for name, obj in inspect.getmembers(AICodeBenchmark) if inspect.isfunction(obj)}
    required = {"run_single_model", "discover_models"}
    missing = sorted(required - methods)
    print("required methods present:", not missing)
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":  # pragma: no cover
    main()
