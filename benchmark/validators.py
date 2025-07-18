"""
Validators for AI Code Benchmark prompts
"""

import json
import yaml
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import importlib.util
import tempfile
import os


class PromptValidators:
    """Validates solutions for each benchmark prompt."""

    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self._load_test_data()

    def _load_test_data(self):
        """Load test data files."""
        # Load user data
        user_data_path = self.test_data_dir / "user_data.json"
        if user_data_path.exists():
            with open(user_data_path, "r") as f:
                self.user_data = json.load(f)
        else:
            self.user_data = None

        # Load original config (for comparison)
        config_path = self.test_data_dir / "config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                self.original_config = f.read()
        else:
            self.original_config = None

    def validate_prompt_1_refactoring(self, solution_file: Path) -> Dict[str, Any]:
        """Validate Prompt 1: Code Refactoring & Analysis."""
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
        }

        if not solution_file.exists():
            result["feedback"].append("❌ Solution file not found")
            return result

        # Test 1: Check if script is valid Python (5 points)
        try:
            with open(solution_file, "r") as f:
                code = f.read()
            compile(code, str(solution_file), "exec")
            result["tests_passed"]["valid_python"] = True
            result["score"] += 5
            result["feedback"].append("✅ Valid Python syntax")
        except SyntaxError as e:
            result["feedback"].append(f"❌ Syntax error: {e}")
            return result

        # Test 2: Check for proper imports and structure (5 points)
        checks = {
            "has_yaml_import": "import yaml" in code or "from yaml" in code,
            "has_json_import": "import json" in code or "from json" in code,
            "has_error_handling": "try:" in code and "except" in code,
            "has_logging": "logging" in code or "logger" in code,
            "has_type_hints": "->" in code or ": str" in code or ": int" in code,
        }

        structure_score = sum(1 for check in checks.values() if check)
        if structure_score >= 3:
            result["score"] += 5
            result["tests_passed"]["good_structure"] = True
            result["feedback"].append(
                f"✅ Good code structure ({structure_score}/5 best practices)"
            )
        else:
            result["feedback"].append(
                f"⚠️  Limited best practices ({structure_score}/5)"
            )

        # Test 3: Check if it runs without errors (10 points)
        try:
            # Create a temporary directory for testing
            with tempfile.TemporaryDirectory() as tmpdir:
                # Copy test files to temp directory
                test_config = Path(tmpdir) / "config.yaml"
                test_data = Path(tmpdir) / "user_data.json"

                # Write corrected config for testing
                corrected_config = """use_legacy_paths: true
paths:
  data_source: /srv/data/production/users.json
  legacy_data_source: ./user_data.json
  log_file: /var/log/processor.log
validation_rules:
  min_age_years: 21
  minimum_posts: 5
  required_fields:
    - id
    - first_name
    - last_name
    - contact.email"""

                with open(test_config, "w") as f:
                    f.write(corrected_config)

                if self.user_data:
                    with open(test_data, "w") as f:
                        json.dump(self.user_data, f)

                # Run the script
                cmd = [sys.executable, str(solution_file), str(test_config)]
                proc = subprocess.run(
                    cmd, cwd=tmpdir, capture_output=True, text=True, timeout=10
                )

                if proc.returncode == 0:
                    result["score"] += 10
                    result["tests_passed"]["runs_successfully"] = True
                    result["feedback"].append("✅ Script runs without errors")

                    # Check output contains expected users
                    output = proc.stdout
                    if "Jane" in output and "Emily" in output:
                        result["feedback"].append(
                            "✅ Correctly filters USA users")
                    else:
                        result["feedback"].append(
                            "⚠️  May not be filtering correctly")
                else:
                    result["feedback"].append(
                        f"❌ Runtime error: {proc.stderr[:200]}")

        except Exception as e:
            result["feedback"].append(f"❌ Error testing script: {str(e)}")

        # Test 4: Code quality checks (5 points)
        quality_checks = {
            "no_global_vars": not any(
                line.strip().startswith(("global ", "globals()"))
                for line in code.split("\n")
            ),
            "uses_pathlib": "pathlib" in code or "Path" in code,
            "has_main_guard": 'if __name__ == "__main__"' in code
            or "if __name__ == '__main__'" in code,
            "proper_file_handling": "with open" in code,
        }

        quality_score = sum(2.5 for check in quality_checks.values() if check)
        if quality_score >= 5:
            result["score"] += 5
            result["tests_passed"]["good_quality"] = True
            result["feedback"].append("✅ High code quality")
        elif quality_score >= 2.5:
            result["score"] += int(quality_score)
            result["feedback"].append(
                f"⚠️  Moderate code quality ({quality_score}/5)")

        # Determine if passed
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_2_yaml_json(
        self, yaml_file: Path, json_file: Path
    ) -> Dict[str, Any]:
        """Validate Prompt 2: YAML/JSON Correction."""
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
        }

        # Test 1: YAML file exists and is valid (10 points)
        if not yaml_file.exists():
            result["feedback"].append("❌ YAML file not found")
        else:
            try:
                with open(yaml_file, "r") as f:
                    yaml_data = yaml.safe_load(f)
                result["score"] += 10
                result["tests_passed"]["valid_yaml"] = True
                result["feedback"].append("✅ Valid YAML syntax")

                # Check if structure is preserved
                expected_keys = {
                    "use_legacy_paths",
                    "paths",
                    "validation_rules",
                    "api_keys",
                    "feature_flags",
                    "server_settings",
                }
                if expected_keys.issubset(set(yaml_data.keys())):
                    result["feedback"].append("✅ All sections preserved")
                else:
                    result["feedback"].append("⚠️  Some sections missing")

            except yaml.YAMLError as e:
                result["feedback"].append(f"❌ Invalid YAML: {e}")
                yaml_data = None

        # Test 2: JSON file exists and is valid (10 points)
        if not json_file.exists():
            result["feedback"].append("❌ JSON file not found")
        else:
            try:
                with open(json_file, "r") as f:
                    json_data = json.load(f)
                result["score"] += 10
                result["tests_passed"]["valid_json"] = True
                result["feedback"].append("✅ Valid JSON syntax")

            except json.JSONDecodeError as e:
                result["feedback"].append(f"❌ Invalid JSON: {e}")
                json_data = None

        # Test 3: Data type corrections (5 points)
        if yaml_data and json_data:
            type_checks = {
                "use_legacy_paths": isinstance(json_data.get("use_legacy_paths"), bool),
                "min_age_years": isinstance(
                    json_data.get("validation_rules", {}).get(
                        "min_age_years"), int
                ),
                "port": isinstance(
                    json_data.get("server_settings", {}).get("port"), int
                ),
                "enable_email_notifications": isinstance(
                    json_data.get("feature_flags", {}).get(
                        "enable_email_notifications"
                    ),
                    bool,
                ),
            }

            correct_types = sum(1 for check in type_checks.values() if check)
            if correct_types == len(type_checks):
                result["score"] += 5
                result["tests_passed"]["correct_types"] = True
                result["feedback"].append("✅ All data types corrected")
            elif correct_types > 0:
                partial_score = int(5 * correct_types / len(type_checks))
                result["score"] += partial_score
                result["feedback"].append(
                    f"⚠️  Some types corrected ({correct_types}/{len(type_checks)})"
                )
            else:
                result["feedback"].append("❌ Data types not corrected")

        # Determine if passed
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_3_transformation(self, transform_file: Path) -> Dict[str, Any]:
        """Validate Prompt 3: Data Transformation."""
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
        }

        if not transform_file.exists():
            result["feedback"].append("❌ Transform file not found")
            return result

        try:
            # Load the transform module
            spec = importlib.util.spec_from_file_location(
                "transform_module", transform_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "transform_and_enrich_users"):
                result["feedback"].append(
                    "❌ Function 'transform_and_enrich_users' not found"
                )
                return result

            transform_func = module.transform_and_enrich_users
            result["score"] += 5
            result["tests_passed"]["function_exists"] = True
            result["feedback"].append("✅ Transform function found")

        except Exception as e:
            result["feedback"].append(f"❌ Error loading module: {e}")
            return result

        # Test with sample data
        if self.user_data:
            try:
                # Test 1: Function doesn't crash (5 points)
                test_users = self.user_data.get("users", [])
                transformed = transform_func(test_users)
                result["score"] += 5
                result["tests_passed"]["no_crash"] = True
                result["feedback"].append("✅ Function runs without crashing")

                # Test 2: ID standardization (5 points)
                id_checks = []
                for user in transformed:
                    if "id" in user:
                        id_checks.append(isinstance(user["id"], int))

                if all(id_checks) and len(id_checks) == len(transformed):
                    result["score"] += 5
                    result["tests_passed"]["id_standardization"] = True
                    result["feedback"].append(
                        "✅ All IDs converted to integers")
                else:
                    result["feedback"].append(
                        "❌ ID standardization incomplete")

                # Test 3: Email provider extraction (5 points)
                email_checks = 0
                null_email_handled = False

                for orig, trans in zip(test_users, transformed):
                    if orig.get("contact", {}).get("email"):
                        if "contact" in trans and "email_provider" in trans["contact"]:
                            expected = orig["contact"]["email"].split("@")[1]
                            if trans["contact"]["email_provider"] == expected:
                                email_checks += 1
                    elif orig.get("contact", {}).get("email") is None:
                        # Check Pierre's case (null email)
                        if "email_provider" not in trans.get("contact", {}):
                            null_email_handled = True

                if email_checks >= 3 and null_email_handled:
                    result["score"] += 5
                    result["tests_passed"]["email_provider"] = True
                    result["feedback"].append(
                        "✅ Email providers extracted correctly")
                else:
                    result["feedback"].append(
                        "⚠️  Email provider extraction has issues")

                # Test 4: Account tier logic (5 points)
                tier_checks = {
                    101: "Gold",  # Jane: 150 posts, 450 comments
                    102: "Bronze",  # John: 4 posts
                    105: "Bronze",  # Emily: 25 posts
                }

                correct_tiers = 0
                for user in transformed:
                    user_id = user.get("id")
                    if user_id in tier_checks:
                        if user.get("account_tier") == tier_checks[user_id]:
                            correct_tiers += 1

                if correct_tiers == len(tier_checks):
                    result["score"] += 5
                    result["tests_passed"]["account_tiers"] = True
                    result["feedback"].append(
                        "✅ Account tiers calculated correctly")
                else:
                    result["feedback"].append(
                        f"⚠️  Account tier logic issues ({correct_tiers}/{len(tier_checks)} correct)"
                    )

                # Test 5: Age type correction (5 points)
                age_checks = []
                for user in transformed:
                    if "stats" in user and "age" in user["stats"]:
                        age_checks.append(isinstance(
                            user["stats"]["age"], int))

                if all(age_checks) and len(age_checks) > 0:
                    result["score"] += 5
                    result["tests_passed"]["age_correction"] = True
                    result["feedback"].append(
                        "✅ All ages converted to integers")

            except Exception as e:
                result["feedback"].append(
                    f"❌ Error during transformation: {str(e)}")

        # Determine if passed
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_4_api(self, api_file: Path) -> Dict[str, Any]:
        """Validate Prompt 4: API Simulation."""
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
        }

        if not api_file.exists():
            result["feedback"].append("❌ API file not found")
            return result

        try:
            with open(api_file, "r") as f:
                code = f.read()

            # Test 1: Function exists and has correct signature (5 points)
            if (
                "def sync_users_to_crm" in code
                and "user_data" in code
                and "api_token" in code
            ):
                result["score"] += 5
                result["tests_passed"]["function_signature"] = True
                result["feedback"].append("✅ Function signature correct")
            else:
                result["feedback"].append("❌ Function signature incorrect")

            # Test 2: Uses requests library (5 points)
            if "import requests" in code or "from requests" in code:
                result["score"] += 5
                result["tests_passed"]["uses_requests"] = True
                result["feedback"].append("✅ Uses requests library")
            else:
                result["feedback"].append("❌ Doesn't use requests library")

            # Test 3: Error handling (10 points)
            error_handlers = {
                "ConnectionError": "ConnectionError" in code,
                "401 handling": "401" in code,
                "400 handling": "400" in code,
                "503 handling": "503" in code,
                "HTTP errors": "HTTPError" in code or "status_code" in code,
            }

            handled = sum(1 for check in error_handlers.values() if check)
            error_score = int(10 * handled / len(error_handlers))
            result["score"] += error_score

            if handled == len(error_handlers):
                result["tests_passed"]["error_handling"] = True
                result["feedback"].append("✅ Comprehensive error handling")
            elif handled > 0:
                result["feedback"].append(
                    f"⚠️  Partial error handling ({handled}/{len(error_handlers)})"
                )
            else:
                result["feedback"].append("❌ No error handling")

            # Test 4: Correct API structure (5 points)
            api_checks = {
                "correct_url": "https://api.crm-system.com/v2/users/sync" in code,
                "post_method": "requests.post" in code or ".post(" in code,
                "headers": "Content-Type" in code
                and "Authorization" in code
                and "Bearer" in code,
                "json_payload": '{"users"' in code
                or "{'users'" in code
                or '"users":' in code,
            }

            api_score = sum(1.25 for check in api_checks.values() if check)
            result["score"] += int(api_score)

            if all(api_checks.values()):
                result["tests_passed"]["api_structure"] = True
                result["feedback"].append("✅ Correct API structure")
            else:
                result["feedback"].append(f"⚠️  API structure issues")

        except Exception as e:
            result["feedback"].append(f"❌ Error analyzing code: {str(e)}")

        # Determine if passed
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result
