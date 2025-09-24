"""Round-trip helper using facade functions."""

from __future__ import annotations

from pathlib import Path

from aibugbench.io.fs import read_text, write_text


def test_roundtrip(tmp_path):
    """Simple UTF-8 round-trip including combining mark."""
    p = Path(tmp_path) / "x.txt"
    text = "héllo"  # "e" + COMBINING ACUTE
    write_text(p, text)
    assert read_text(p) == text


def test_newline_normalisation(tmp_path):
    raw = "line1\r\nline2\rline3\n"
    p = tmp_path / "nl.txt"
    # write raw bytes to bypass helper normalisation
    p.write_bytes(raw.encode())
    assert read_text(p) == "line1\nline2\nline3\n"


def test_atomic_write_text(tmp_path):
    from aibugbench.io.fs import atomic_write_text

    target = tmp_path / "atomic.txt"
    atomic_write_text(target, "data")
    assert target.read_text() == "data"


def test_atomic_write_json(tmp_path):
    import json

    from aibugbench.io.fs import atomic_write_json

    payload = {"b": 2, "a": 1}
    target = tmp_path / "j.json"
    atomic_write_json(target, payload)
    loaded = json.loads(target.read_text())
    # keys should be sorted due to sort_keys=True
    assert list(loaded.keys()) == ["a", "b"]
    assert loaded == payload
