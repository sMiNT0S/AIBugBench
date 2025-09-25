"""Tests for aibugbench.util.unicode_safety helpers."""

from __future__ import annotations

import sys
from typing import TextIO, cast

import pytest

from aibugbench.util import unicode_safety as us


class DummyStream:
    def __init__(self, *, encoding: str | None, tty: bool) -> None:
        self.encoding = encoding
        self._tty = tty
        self._buf: list[str] = []

    def isatty(self) -> bool:  # mimic TextIO API
        return self._tty

    def write(self, s: str) -> int:  # print(file=...) calls write
        self._buf.append(s)
        return len(s)

    def getvalue(self) -> str:
        return "".join(self._buf)


@pytest.mark.unit
def test_is_unicode_safe_non_tty_is_safe():
    s = DummyStream(encoding=None, tty=False)
    assert us.is_unicode_safe(cast(TextIO, s)) is True


@pytest.mark.unit
def test_is_unicode_safe_utf_encoding_is_safe():
    s = DummyStream(encoding="utf-8", tty=True)
    assert us.is_unicode_safe(cast(TextIO, s)) is True


@pytest.mark.unit
def test_is_unicode_safe_non_utf_tty_is_not_safe_on_non_windows(monkeypatch: pytest.MonkeyPatch):
    s = DummyStream(encoding="cp1252", tty=True)
    monkeypatch.setattr(sys, "platform", "linux")
    assert us.is_unicode_safe(cast(TextIO, s)) is False


@pytest.mark.unit
def test_safe_print_replaces_non_ascii_when_unsafe(monkeypatch: pytest.MonkeyPatch):
    # Force non-Windows to avoid codepage 65001 shortcut
    monkeypatch.setattr(sys, "platform", "linux")
    s = DummyStream(tty=True, encoding="ascii")
    us.safe_print("héllo — ✓", stream=cast(TextIO, s))  # default ascii_replace=True
    out = s.getvalue()
    assert out.strip() == "h?llo ? ?"
