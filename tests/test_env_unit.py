"""Unit tests for aibugbench.config.env helpers."""

from __future__ import annotations

import pytest

from aibugbench.config import env as env_mod


def test_get_env_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    assert env_mod.get_env("MISSING_KEY", default="fallback") == "fallback"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1", True),
        ("true", True),
        ("yes", True),
        ("on", True),
        ("y", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("off", False),
        ("n", False),
    ],
)
def test_get_env_bool_truthy_falsy(monkeypatch: pytest.MonkeyPatch, value: str, expected: bool):
    monkeypatch.setenv("FLAG", value)
    assert env_mod.get_env_bool("FLAG", default=not expected) is expected


def test_get_env_bool_invalid_uses_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FLAG", "maybe")
    assert env_mod.get_env_bool("FLAG", default=True) is True
    monkeypatch.delenv("FLAG")
    assert env_mod.get_env_bool("FLAG", default=False) is False


@pytest.mark.parametrize("value,expected", [("42", 42), (" 7 ", 7)])
def test_get_env_int_valid(monkeypatch: pytest.MonkeyPatch, value: str, expected: int):
    monkeypatch.setenv("NUM", value)
    assert env_mod.get_env_int("NUM", default=0) == expected


def test_get_env_int_invalid_or_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NUM", "not-an-int")
    assert env_mod.get_env_int("NUM", default=5) == 5
    monkeypatch.delenv("NUM")
    assert env_mod.get_env_int("NUM", default=9) == 9


@pytest.mark.parametrize("value,expected", [("3.14", 3.14), (" 2.5 ", 2.5)])
def test_get_env_float_valid(monkeypatch: pytest.MonkeyPatch, value: str, expected: float):
    monkeypatch.setenv("FNUM", value)
    assert env_mod.get_env_float("FNUM", default=0.0) == pytest.approx(expected)


def test_get_env_float_invalid_or_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FNUM", "oops")
    assert env_mod.get_env_float("FNUM", default=1.25) == pytest.approx(1.25)
    monkeypatch.delenv("FNUM")
    assert env_mod.get_env_float("FNUM", default=2.75) == pytest.approx(2.75)
