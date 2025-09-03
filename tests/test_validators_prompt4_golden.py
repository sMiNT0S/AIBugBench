"""High-score golden test for Prompt 4 API validator.

Ensures a well-structured implementation with headers, bearer token, timeout,
basic retry/backoff hint, and docstring achieves a passing score >= threshold.
"""

from __future__ import annotations

import pytest

from benchmark.validators import PromptValidators


@pytest.mark.unit
def test_prompt4_golden_pass(temp_dir, test_data_dir):
    api_file = temp_dir / "prompt_4_api_sync.py"
    module_code = """import time
import requests

# Sync CRM users: proper bearer header, timeout, simple retry; exercises validator scoring.
def sync_users_to_crm(user_data, api_token):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    last_exc = None
    for _ in range(2):  # basic retry
        try:
            resp = requests.post(
                "https://api.example.com/users",
                json={"users": user_data},
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("job_id") or data.get("user_ids", [])
            if resp.status_code in {400, 401, 503}:
                print(f"Non-success status: {resp.status_code}")  # quality / error keywords
        except requests.exceptions.RequestException as e:
            last_exc = e
            time.sleep(0.05)
    return None if last_exc else []
"""
    api_file.write_text(module_code, encoding="utf-8")

    validator = PromptValidators(test_data_dir)
    result = validator.validate_prompt_4_api(api_file)
    assert result["passed"], result
    assert result["score"] >= 15
    # Ensure key security + performance categories awarded some points
    ds = result["detailed_scoring"]
    assert ds["security"]["earned"] > 0
    assert ds["performance"]["earned"] >= 1.0
