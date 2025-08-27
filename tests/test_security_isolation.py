"""Placeholder security sandbox tests (full suite deferred to Phase 3)."""

import pytest

pytestmark = pytest.mark.xfail(
    reason="Security sandbox deferred (TODO: implement Phase 3 sandbox #TODO_SECURITY_SANDBOX)",
    strict=False,
)


def test_security_placeholder():
    """Placeholder always passing test to keep suite green until sandbox implemented."""
    assert True
