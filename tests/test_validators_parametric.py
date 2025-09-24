# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Parametric consolidation of validator tests.

Covers core variants for each prompt while reducing repetition found in original
`test_validators.py`. Kept original file for full coverage; this focuses on
succinct signal and faster feedback.
"""

from unittest.mock import patch

import pytest

from benchmark.validators import PromptValidators


@pytest.fixture  # function scope to align with test_data_dir fixture
def validators_fixture(test_data_dir):  # reuse heavy setup once
    return PromptValidators(test_data_dir)


PROMPT1_CASES = [
    (
        "valid",
        """
import json

def process_records(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return [r for r in data if r]
""",
        True,
    ),
    (
        "syntax_error",
        """
import json
def process_records(filename):
    if True
        return []
""",
        False,
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize("name,code,should_pass", PROMPT1_CASES)
def test_prompt1_parametric(validators_fixture, temp_dir, name, code, should_pass):
    file_path = temp_dir / f"p1_{name}.py"
    file_path.write_text(code, newline="\n")
    result = validators_fixture.validate_prompt_1_refactoring(file_path)
    assert result["passed"] is should_pass


PROMPT2_CASES = [
    (
        "valid",
        "database:\n  host: localhost\n  port: 5432\n",
        {"database": {"host": "localhost", "port": 5432}},
        True,
    ),
    (
        "dup_keys",
        "key: 1\nkey: 2\n",
        {"key": 1},
        False,
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize("name,yaml_text,json_obj,should_pass", PROMPT2_CASES)
def test_prompt2_parametric(validators_fixture, temp_dir, name, yaml_text, json_obj, should_pass):
    yaml_file = temp_dir / f"p2_{name}.yaml"
    json_file = temp_dir / f"p2_{name}.json"
    yaml_file.write_text(yaml_text, newline="\n")
    import json as _json

    json_file.write_text(_json.dumps(json_obj), newline="\n")
    result = validators_fixture.validate_prompt_2_yaml_json(yaml_file, json_file)
    assert result["passed"] is should_pass


PROMPT4_CASES = [
    (
        "success",
        """
import requests

def sync_users_to_crm(users, token):
    if not users: return None
    r = requests.post('https://api.example.com/users', json={'users': users})
    try:
        return r.json().get('user_ids', [])
    except Exception:
        return None
""",
        False,  # Below 60% threshold given scoring rubric
    ),
    (
        "security_issue",
        """
import requests

def sync_users_to_crm(users, token):
    hardcoded = 'sk-ABCDEF0123456789TOKENXYZ'  # deliberate
    return requests.post(
        'https://api.example.com/users',
        json={'users': users},
        verify=False,
    ).json()
""",
        False,  # Hardcoded creds + missing headers reduce score below pass threshold
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize("name,code,should_pass", PROMPT4_CASES)
def test_prompt4_parametric(validators_fixture, temp_dir, name, code, should_pass):
    file_path = temp_dir / f"p4_{name}.py"
    file_path.write_text(code, newline="\n")
    result = validators_fixture.validate_prompt_4_api(file_path)
    assert isinstance(result["score"], int | float)
    assert result["passed"] is should_pass


@pytest.mark.unit
def test_prompt3_transformation_simplified(validators_fixture, temp_dir):
    code = """
import json

def transform_users(users):
    return [u for u in users if u.get('id')]
"""
    file_path = temp_dir / "p3_simple.py"
    file_path.write_text(code, newline="\n")

    with patch("json.load", return_value=[{"id": 1}, {"id": 0}]):
        result = validators_fixture.validate_prompt_3_transformation(file_path)
    assert "detailed_scoring" in result
    assert result["score"] >= 0
