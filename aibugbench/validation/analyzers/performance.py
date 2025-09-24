"""Performance analyzer scaffolding for Phase 3."""

from __future__ import annotations

from typing import Any


def run(run_dir: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return performance checks and stats for the given run directory."""

    raise NotImplementedError("Phase 3.C will implement performance analyzer")


__all__ = ["run"]
