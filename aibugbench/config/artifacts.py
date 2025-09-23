"""Facade for resolving artifact path precedence (Phase 0)."""

from __future__ import annotations

__all__ = ["choose_artifact_path"]


def choose_artifact_path(args: dict, env: dict, defaults: str) -> str:
    """Return artifact path with precedence: args > env > defaults."""
    if args.get("artifact"):
        return args["artifact"]
    if env.get("ARTIFACT"):
        return env["ARTIFACT"]
    return defaults
