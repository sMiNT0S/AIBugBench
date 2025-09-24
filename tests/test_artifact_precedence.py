"""Artifact precedence matrix validation for Phase-0 choose_artifact_path."""

from __future__ import annotations

import os
from pathlib import Path

from aibugbench.config.artifacts import choose_artifact_path

CASES = [
    # args wins over env
    ({"artifact": "C:/from/args"}, {"ARTIFACT": "C:/from/env"}, "C:/from/defaults", "args"),
    # env wins over default when args absent
    ({}, {"ARTIFACT": "C:/from/env"}, "C:/from/defaults", "env"),
    # fallback to default
    ({}, {}, "C:/from/defaults", "defaults"),
    # ignore empty/whitespace env value
    ({}, {"ARTIFACT": "   "}, "C:/from/defaults", "defaults"),
]


def test_artifact_precedence_matrix(monkeypatch):
    for args, env, defaults, src in CASES:
        # Apply env to monkeypatch to avoid side-effects
        if "ARTIFACT" in env:
            monkeypatch.setenv("ARTIFACT", env["ARTIFACT"])
        else:
            monkeypatch.delenv("ARTIFACT", raising=False)
        got_path = choose_artifact_path(args, os.environ, defaults)
        expected = {
            "args": Path("C:/from/args").resolve(),
            "env": Path("C:/from/env").resolve(),
            "defaults": Path("C:/from/defaults").resolve(),
        }[src]
        assert Path(got_path) == expected
        # Path should exist after ensure_dir side-effect
        assert Path(got_path).exists()
