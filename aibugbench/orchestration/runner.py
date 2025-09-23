"""Stub BenchmarkRunner (Phase 0)."""

from __future__ import annotations

from typing import Any

__all__ = ["BenchmarkRunner"]


class BenchmarkRunner:
    def run_once(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError("Phase 2 will implement runner")
