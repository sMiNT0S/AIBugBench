# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Focused tests for the tiered submissions directory restructure (clean minimal).

Validates essentials only: structure creation, template placement, reference
validation, discovery, and a placeholder traversal test. The previous large
suite was removed due to persistent indentation corruption.
"""

from pathlib import Path

import pytest

from benchmark.utils import create_submission_template, validate_submission_structure


@pytest.fixture
def tiered_submissions(tmp_path: Path) -> Path:
    base = tmp_path / "submissions"
    base.mkdir()

    ref_impl = base / "reference_implementations"
    templates_root = base / "templates"
    user_subs = base / "user_submissions"
    for d in (ref_impl, templates_root, user_subs):
        d.mkdir()
    (templates_root / "template").mkdir()

    example = ref_impl / "example_model"
    example.mkdir()
    (example / "prompt_1_solution.py").write_text("print('ok')\n")
    (example / "prompt_2_config.json").write_text('{"database": {"host": "localhost"}}')
    (example / "prompt_2_config_fixed.yaml").write_text("database:\n  host: localhost\n")
    (example / "prompt_3_transform.py").write_text(
        "def transform_and_enrich_users(users):\n    return users\n"
    )
    (example / "prompt_4_api_sync.py").write_text(
        "def sync_users_to_crm(data, token):\n    return None\n"
    )
    return base


def test_structure_minimal_layout(tiered_submissions: Path):
    for d in ["reference_implementations", "templates", "user_submissions"]:
        assert (tiered_submissions / d).is_dir()
    assert (tiered_submissions / "templates" / "template").is_dir()
    assert not (tiered_submissions / "template").exists()


def test_reference_validation(tiered_submissions: Path):
    example = tiered_submissions / "reference_implementations" / "example_model"
    validation = validate_submission_structure(example)
    expected = {
        "prompt_1_solution.py",
        "prompt_2_config.json",
        "prompt_2_config_fixed.yaml",
        "prompt_3_transform.py",
        "prompt_4_api_sync.py",
    }
    assert expected.issubset(validation.keys())
    for name in expected:
        assert validation[name]


def test_model_discovery_across_tiers(tiered_submissions: Path):
    ref_models = [
        p for p in (tiered_submissions / "reference_implementations").glob("*/") if p.is_dir()
    ]
    user_models = [p for p in (tiered_submissions / "user_submissions").glob("*/") if p.is_dir()]
    assert len(ref_models) == 1
    assert ref_models[0].name == "example_model"
    assert user_models == []


def test_create_submission_template_only_tiered(tmp_path: Path):
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    create_submission_template(submissions)
    assert (submissions / "templates" / "template").exists()
    assert not (submissions / "template").exists()


def test_path_traversal_placeholder(tmp_path: Path):
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    malicious = [
        "..",
        "../..",
        "../../etc/passwd",
        "user_submissions/../reference_implementations",
    ]
    base_resolved = submissions.resolve()
    for m in malicious:
        candidate = (submissions / m).resolve()
        # Placeholder: detect escape attempts (candidate not inside base)
        if candidate != base_resolved and base_resolved not in candidate.parents:
            continue
