# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Shared pytest fixtures for the AIBugBench test suite.

Provides commonly used temporary directories, sample data, and helper mocks
that multiple test modules depend on. Centralising these here fixes the
missing fixture errors (e.g. temp_dir, test_data_dir, example_model_dir) and
reduces duplication.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

# Phase-0 scaffolding: ensure repository root on sys.path so provisional
# 'aibugbench' package (not yet part of original setup config) resolves.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def temp_dir(tmp_path):
    """Return a convenient temporary directory Path object (alias of tmp_path)."""
    return tmp_path


@pytest.fixture
def test_data_dir():
    """Return the repository's bundled test_data directory (skip if absent)."""
    repo_root = Path(__file__).parent.parent
    td = repo_root / "test_data"
    if not td.exists():  # Defensive: allow running with pruned assets
        pytest.skip("test_data directory missing")
    return td


@pytest.fixture
def example_model_dir():
    """Return the example_model directory based on tiered structure (may be missing)."""
    repo_root = Path(__file__).parent.parent

    # Check tiered structure first
    tiered_path = repo_root / "submissions" / "reference_implementations" / "example_model"
    if tiered_path.exists():
        return tiered_path

    # Legacy fallback
    legacy_path = repo_root / "submissions" / "example_model"
    return legacy_path


@pytest.fixture
def tiered_submissions_dir():
    """Return the submissions directory with tiered structure awareness."""
    repo_root = Path(__file__).parent.parent
    return repo_root / "submissions"


@pytest.fixture
def reference_implementations_dir(tiered_submissions_dir):
    """Return the reference implementations directory."""
    return tiered_submissions_dir / "reference_implementations"


@pytest.fixture
def user_submissions_dir(tiered_submissions_dir):
    """Return the user submissions directory."""
    return tiered_submissions_dir / "user_submissions"


@pytest.fixture
def templates_dir(tiered_submissions_dir):
    """Return the templates directory."""
    return tiered_submissions_dir / "templates"


@pytest.fixture
def sample_user_data(test_data_dir):
    """Structured user data list used by transformation tests.

    Falls back to an inline minimal dataset if user_data.json is missing.
    """
    file = test_data_dir / "user_data.json"
    if file.exists():
        try:
            return json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # Corrupted file edge case
            pass
    # Fallback minimal representative sample
    return [
        {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "age": 28,
            "registration_date": "2024-01-05",
        },
        {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "age": "35",
            "registration_date": "2023-12-11",
        },
    ]


@pytest.fixture
def mock_requests_session(monkeypatch):
    """Provide a lightweight mocked requests session / post for API validator tests.

    Returns an object whose post() returns a stub response with user_ids.
    Also monkeypatches requests.post directly for simple call sites.
    """

    class DummyResponse:  # Simple stand-in for requests.Response
        def __init__(self, data, status=200):
            self._data = data
            self.status_code = status

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception("HTTP error")

    def _post(*_args, **_kwargs):  # Ignore args/kwargs for deterministic tests
        return DummyResponse({"user_ids": [1, 2, 3]})

    # Patch the top-level requests.post used in simple scripts
    monkeypatch.setattr("requests.post", _post)

    class DummySession:
        def post(self, *args, **kwargs):
            return _post(*args, **kwargs)

    return DummySession()


# Optional: register custom markers programmatically (backup to pytest.ini)
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow / exhaustive tests")
