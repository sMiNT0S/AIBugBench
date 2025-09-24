"""Round-trip helper using facade functions."""

from __future__ import annotations

from pathlib import Path

from aibugbench.io.fs import read_text, write_text


def test_roundtrip(tmp_path):
    p = Path(tmp_path) / "x.txt"
    write_text(p, "héllo")
    assert read_text(p) == "héllo"
