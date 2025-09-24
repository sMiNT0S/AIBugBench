"""Artifact precedence matrix validation for Phase-0 choose_artifact_path."""

from __future__ import annotations

import os

from aibugbench.config.artifacts import choose_artifact_path

CASES = [
    ({"artifact": "/from/args"}, {"ARTIFACT": "/from/env"}, "/from/defaults", "args"),
    ({}, {"ARTIFACT": "/from/env"}, "/from/defaults", "env"),
    ({}, {}, "/from/defaults", "defaults"),
]


def test_artifact_precedence_matrix(monkeypatch):
    for args, env, defaults, src in CASES:
        # Apply env to monkeypatch to avoid side-effects
        if "ARTIFACT" in env:
            monkeypatch.setenv("ARTIFACT", env["ARTIFACT"])
        else:
            monkeypatch.delenv("ARTIFACT", raising=False)
        got_path = choose_artifact_path(args, os.environ, defaults)
        if src == "args":
            assert got_path == "/from/args"
        elif src == "env":
            assert got_path == "/from/env"
        else:
            assert got_path == "/from/defaults"
