"""
Validators for AI Code Benchmark prompts
"""

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
from unittest.mock import Mock, patch

import requests
import yaml
from yaml.constructor import ConstructorError


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


class ScoringDetail:
    """Helper class to track detailed scoring with rationale."""

    def __init__(self, max_points: float):
        self.max_points = max_points
        self.earned_points = 0.0
        self.checks = []

    def add_check(self, name: str, passed: bool, points: float, rationale: str = ""):
        """Add a scoring check with detailed rationale."""
        earned = points if passed else 0.0
        self.earned_points += earned
        self.checks.append(
            {
                "name": name,
                "passed": passed,
                "points_possible": points,
                "points_earned": earned,
                "rationale": rationale,
            }
        )

    def get_feedback_line(self, category_name: str) -> str:
        """Generate detailed feedback line with breakdown."""
        if self.earned_points == self.max_points:
            status = "✅"
        elif self.earned_points > 0:
            status = "⚠️"
        else:
            status = "❌"

        # Build detailed breakdown
        passed_checks = [c["name"] for c in self.checks if c["passed"]]
        failed_checks = [c["name"] for c in self.checks if not c["passed"]]

        breakdown = ""
        if passed_checks:
            breakdown += f" ✓{', '.join(passed_checks)}"
        if failed_checks:
            breakdown += f" ✗{', '.join(failed_checks)}"

        return (
            f"{status} {category_name} ({self.earned_points:.1f}/{self.max_points:.1f}): "
            f"{breakdown}"
        )


class SecurityAnalyzer:
    """Analyzes code for common security vulnerabilities."""

    @staticmethod
    def check_sql_injection_patterns(code: str) -> list[tuple[str, str]]:
        """Check for potential SQL injection vulnerabilities."""
        issues = []

        # String concatenation with SQL keywords
        sql_concat_patterns = [
            r'["\'].*\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*["\'].*\+',
            r'\+.*["\'].*\s*(WHERE|ORDER BY|GROUP BY|HAVING)\s+.*["\']',
            r'f["\'].*\s*(SELECT|INSERT|UPDATE|DELETE)\s+.*\{.*\}.*["\']',
        ]

        for pattern in sql_concat_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(("sql_injection", "Potential SQL injection via string concatenation"))
                break

        # Check for execute() without parameterization
        if re.search(r'\.execute\(["\'].*\{.*\}.*["\']', code, re.IGNORECASE):
            issues.append(("sql_injection", "SQL execute with string formatting"))

        return issues

    @staticmethod
    def check_hardcoded_secrets(code: str) -> list[tuple[str, str]]:
        """Check for hardcoded secrets and API keys."""
        issues = []

        # Common secret patterns
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token"),
            (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', "Potential base64 encoded secret"),
            (r'["\']sk-[A-Za-z0-9]{32,}["\']', "OpenAI API key pattern"),
            (r'["\']ghp_[A-Za-z0-9]{36}["\']', "GitHub personal access token"),
        ]

        for pattern, description in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(("hardcoded_secret", description))

        return issues

    @staticmethod
    def check_path_traversal(code: str) -> list[tuple[str, str]]:
        """Check for path traversal vulnerabilities."""
        issues = []

        # Direct path concatenation without validation
        if re.search(r"open\s*\(\s*.*\+.*user.*\)", code, re.IGNORECASE):
            issues.append(("path_traversal", "Path concatenation with user input"))

        # Missing path validation
        if "../" in code and "Path(" in code:
            issues.append(("path_traversal", "Potential directory traversal pattern"))

        # Unsafe file operations
        unsafe_patterns = [
            r"os\.system\s*\(\s*.*user",
            r"subprocess\..*shell=True.*user",
            r"eval\s*\(\s*.*user",
            r"exec\s*\(\s*.*user",
        ]

        for pattern in unsafe_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(("unsafe_execution", "Unsafe execution with user input"))
                break

        return issues

    @classmethod
    def analyze_code_security(cls, code: str) -> dict[str, Any]:
        """Perform comprehensive security analysis on code."""
        all_issues = []

        all_issues.extend(cls.check_sql_injection_patterns(code))
        all_issues.extend(cls.check_hardcoded_secrets(code))
        all_issues.extend(cls.check_path_traversal(code))

        # Categorize issues
        security_score = 5.0  # Start with max security score
        issue_categories = {}

        for issue_type, description in all_issues:
            if issue_type not in issue_categories:
                issue_categories[issue_type] = []
            issue_categories[issue_type].append(description)

        # Deduct points based on severity
        severity_deductions = {
            "sql_injection": 2.0,
            "hardcoded_secret": 1.5,
            "path_traversal": 2.0,
            "unsafe_execution": 2.5,
        }

        for issue_type in issue_categories:
            security_score -= severity_deductions.get(issue_type, 1.0)

        security_score = max(0.0, security_score)  # Don't go below 0

        return {
            "score": security_score,
            "max_score": 5.0,
            "issues": issue_categories,
            "all_issues": all_issues,
            "is_secure": len(all_issues) == 0,
        }


class PerformanceAnalyzer:
    """Analyzes code for performance issues and inefficient patterns."""

    @staticmethod
    def check_nested_loops(code: str) -> list[tuple[str, str]]:
        """Check for O(n²) and nested loop patterns that may be inefficient."""
        issues = []

        # Simple check for nested for loops
        lines = code.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"^\s*for\s+\w+\s+in\s+", line.strip()):
                # Look for another for loop in the next few lines (within same indentation block)
                base_indent = len(line) - len(line.lstrip())
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip() == "":
                        continue
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if current_indent <= base_indent:
                        break
                    if re.search(r"^\s*for\s+\w+\s+in\s+", lines[j].strip()):
                        issues.append(
                            ("nested_loops", "Potential O(n²) nested loop pattern detected")
                        )
                        break

        return issues

    @staticmethod
    def check_inefficient_patterns(code: str) -> list[tuple[str, str]]:
        """Check for common inefficient programming patterns."""
        issues = []

        # Repeated string concatenation in loops (simplified check)
        if "for " in code and "+=" in code and ("str(" in code or '"' in code or "'" in code):
            lines = code.split("\n")
            in_loop = False
            for line in lines:
                if re.match(r"\s*for\s+", line):
                    in_loop = True
                elif in_loop and "+=" in line and ('"' in line or "'" in line):
                    issues.append(
                        (
                            "string_concatenation",
                            "String concatenation in loop (use join() instead)",
                        )
                    )
                    break
                elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    in_loop = False

        # Inefficient membership testing
        if re.search(r"if\s+.*\s+in\s+\[.*\]:", code):
            issues.append(("list_membership", "Use set for membership testing instead of list"))

        # Multiple sorts
        if code.count(".sort(") > 1 or code.count("sorted(") > 1:
            issues.append(("multiple_sorts", "Multiple sorts detected - consider single sort"))

        return issues

    @staticmethod
    def check_memory_patterns(code: str) -> list[tuple[str, str]]:
        """Check for potential memory inefficiencies."""
        issues = []

        # Loading entire files when partial reading might be better
        if ".read()" in code and "for " in code:
            issues.append(("full_file_read", "Consider reading file in chunks for large files"))

        # Not using generators where appropriate (simple check)
        if ("[" in code and " for " in code and " in " in code and "]" in code
                and len(code) > 500):  # Only flag in larger code
            issues.append(
                ("list_comprehension", "Consider generator expression for memory efficiency")
            )

        return issues

    @staticmethod
    def check_algorithm_efficiency(code: str) -> list[tuple[str, str]]:
        """Check for algorithmically inefficient approaches."""
        issues = []

        # Linear search in sorted data
        if "sorted(" in code and "for " in code and "if " in code and "==" in code:
            issues.append(("linear_search", "Consider binary search for sorted data"))

        # Inefficient sorting
        if code.count(".sort(") > 1 or code.count("sorted(") > 1:
            issues.append(("multiple_sorts", "Multiple sorts detected - consider single sort"))

        # Unnecessary data structure conversions
        if "list(" in code and ".sort()" in code:
            issues.append(("unnecessary_conversion", "Unnecessary list conversion before sorting"))

        return issues

    @classmethod
    def analyze_code_performance(cls, code: str) -> dict[str, Any]:
        """Perform comprehensive performance analysis on code."""
        all_issues = []

        all_issues.extend(cls.check_nested_loops(code))
        all_issues.extend(cls.check_inefficient_patterns(code))
        all_issues.extend(cls.check_memory_patterns(code))
        all_issues.extend(cls.check_algorithm_efficiency(code))

        # Calculate performance score
        performance_score = 3.0  # Start with max performance score
        issue_categories = {}

        for issue_type, description in all_issues:
            if issue_type not in issue_categories:
                issue_categories[issue_type] = []
            issue_categories[issue_type].append(description)

        # Deduct points based on severity
        severity_deductions = {
            "nested_loops": 1.0,
            "potential_quadratic": 0.8,
            "string_concatenation": 0.5,
            "nested_append": 0.5,
            "list_membership": 0.3,
            "repeated_calls": 0.4,
            "list_in_loop": 0.3,
            "full_file_read": 0.4,
            "list_comprehension": 0.2,
            "linear_search": 0.6,
            "multiple_sorts": 0.5,
            "unnecessary_conversion": 0.3,
        }

        for issue_type in issue_categories:
            performance_score -= severity_deductions.get(issue_type, 0.5)

        performance_score = max(0.0, performance_score)  # Don't go below 0

        return {
            "score": performance_score,
            "max_score": 3.0,
            "issues": issue_categories,
            "all_issues": all_issues,
            "is_efficient": len(all_issues) == 0,
        }


class MaintainabilityAnalyzer:
    """Analyzes code for maintainability issues and code quality metrics."""

    @staticmethod
    def check_function_length(code: str) -> list[tuple[str, str]]:
        """Check for overly long functions (>20 lines)."""
        issues = []

        lines = code.split("\n")
        in_function = False
        function_start = 0
        function_name = ""

        for i, line in enumerate(lines):
            # Check for function definition
            func_match = re.match(r"\s*def\s+(\w+)\s*\(", line)
            if func_match:
                if in_function:
                    # Check previous function length
                    func_length = i - function_start
                    if func_length > 20:
                        issues.append(
                            (
                                "long_function",
                                f"Function '{function_name}' is {func_length} lines (>20)",
                            )
                        )

                in_function = True
                function_start = i
                function_name = func_match.group(1)
            elif (
                line.strip()
                and not line.startswith(" ")
                and not line.startswith("\t")
                and in_function
            ):
                # End of function (non-indented line)
                func_length = i - function_start
                if func_length > 20:
                    issues.append(
                        (
                            "long_function",
                            f"Function '{function_name}' is {func_length} lines (>20)",
                        )
                    )
                in_function = False

        # Check last function if file ends with it
        if in_function:
            func_length = len(lines) - function_start
            if func_length > 20:
                issues.append(
                    ("long_function", f"Function '{function_name}' is {func_length} lines (>20)")
                )

        return issues

    @staticmethod
    def check_code_duplication(code: str) -> list[tuple[str, str]]:
        """Check for obvious code duplication patterns."""
        issues = []

        lines = [line.strip() for line in code.split("\n") if line.strip()]

        # Look for repeated blocks of 3+ lines
        for i in range(len(lines) - 2):
            block = lines[i : i + 3]
            # Skip very short or comment lines
            if any(len(line) < 10 or line.startswith("#") for line in block):
                continue

            # Look for same block later in code
            for j in range(i + 3, len(lines) - 2):
                if lines[j : j + 3] == block:
                    issues.append(("code_duplication", "Repeated code block detected"))
                    return issues  # Only report once

        return issues

    @staticmethod
    def check_variable_naming(code: str) -> list[tuple[str, str]]:
        """Check for poor variable naming practices."""
        issues = []

        # Check for single letter variables (except common ones like i, j in loops)
        single_letter_vars = re.findall(r"\b[a-z]\s*=", code)
        loop_context_vars = ["i", "j", "k", "x", "y", "z"]

        problematic_vars = [var[0] for var in single_letter_vars if var[0] not in loop_context_vars]

        if problematic_vars:
            issues.append(
                ("poor_naming", f"Single letter variables found: {set(problematic_vars)}")
            )

        # Check for variables with numbers (often indicates poor naming)
        numbered_vars = re.findall(r"\b\w*\d+\w*\s*=", code)
        if len(numbered_vars) > 2:  # Allow some numbered variables
            issues.append(("numbered_variables", "Multiple numbered variables suggest poor naming"))

        return issues

    @staticmethod
    def check_complexity_indicators(code: str) -> list[tuple[str, str]]:
        """Check for high complexity indicators."""
        issues = []

        # Count nested if statements (simplified complexity measure)
        lines = code.split("\n")
        max_if_depth = 0
        current_if_depth = 0

        for line in lines:
            indent = len(line) - len(line.lstrip())
            if "if " in line and line.strip().startswith("if"):
                current_if_depth = indent // 4 + 1  # Assuming 4-space indents
                max_if_depth = max(max_if_depth, current_if_depth)

        if max_if_depth > 3:
            issues.append(
                ("high_complexity", f"Deeply nested if statements (depth: {max_if_depth})")
            )

        # Count number of conditions in single if statements
        complex_ifs = re.findall(r"if\s+.*\sand\s.*\sand\s", code)
        if complex_ifs:
            issues.append(("complex_conditions", "Complex boolean conditions found"))

        return issues

    @classmethod
    def analyze_code_maintainability(cls, code: str) -> dict[str, Any]:
        """Perform comprehensive maintainability analysis on code."""
        all_issues = []

        all_issues.extend(cls.check_function_length(code))
        all_issues.extend(cls.check_code_duplication(code))
        all_issues.extend(cls.check_variable_naming(code))
        all_issues.extend(cls.check_complexity_indicators(code))

        # Calculate maintainability score
        maintainability_score = 2.0  # Start with max maintainability score
        issue_categories = {}

        for issue_type, description in all_issues:
            if issue_type not in issue_categories:
                issue_categories[issue_type] = []
            issue_categories[issue_type].append(description)

        # Deduct points based on severity
        severity_deductions = {
            "long_function": 0.5,
            "code_duplication": 0.8,
            "poor_naming": 0.3,
            "numbered_variables": 0.2,
            "high_complexity": 0.6,
            "complex_conditions": 0.4,
        }

        for issue_type in issue_categories:
            maintainability_score -= severity_deductions.get(issue_type, 0.3)

        maintainability_score = max(0.0, maintainability_score)  # Don't go below 0

        return {
            "score": maintainability_score,
            "max_score": 2.0,
            "issues": issue_categories,
            "all_issues": all_issues,
            "is_maintainable": len(all_issues) == 0,
        }


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
            with open(user_data_path) as f:
                self.user_data = json.load(f)
        else:
            self.user_data = None

        # Load original config (for comparison)
        config_path = self.test_data_dir / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                self.original_config = f.read()
        else:
            self.original_config = None

    def validate_prompt_1_refactoring(self, solution_file: Path) -> dict[str, Any]:
        """Validate Prompt 1: Code Refactoring & Analysis."""
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
            "detailed_scoring": {},
        }

        if not solution_file.exists():
            result["feedback"].append("❌ Solution file not found")
            return result

        # Initialize detailed scoring categories (Final scoring distribution with all 7 categories)
        syntax_scoring = ScoringDetail(5.0)  # Syntax (5pts)
        structure_scoring = ScoringDetail(3.0)  # Structure (3pts)
        execution_scoring = ScoringDetail(6.0)  # Execution (6pts) - reduced again
        quality_scoring = ScoringDetail(3.0)  # Quality (3pts)
        security_scoring = ScoringDetail(4.0)  # Security (4pts)
        performance_scoring = ScoringDetail(2.0)  # Performance (2pts) - reduced
        maintainability_scoring = ScoringDetail(2.0)  # Maintainability (2pts) - NEW!

        # Test 1: Check if script is valid Python (5 points)
        try:
            with open(solution_file, encoding="utf-8") as f:
                code = f.read()
            compile(code, str(solution_file), "exec")
            syntax_scoring.add_check("valid_syntax", True, 5.0, "Python syntax is valid")
            result["tests_passed"]["valid_python"] = True
        except SyntaxError as e:
            syntax_scoring.add_check("valid_syntax", False, 5.0, f"Syntax error: {e}")
            result["feedback"].append(syntax_scoring.get_feedback_line("Python Syntax"))
            return result

        # Test 2: Check for proper imports and structure (3 points)
        structure_checks = {
            "yaml_import": (
                "import yaml" in code or "from yaml" in code,
                "Uses YAML library",
            ),
            "json_import": (
                "import json" in code or "from json" in code,
                "Uses JSON library",
            ),
            "error_handling": (
                "try:" in code and "except" in code,
                "Has error handling",
            ),
            "logging": (
                bool(
                    re.search(
                        r"logging\.(debug|info|warning|error|critical)\s*\(", code, re.IGNORECASE
                    )
                ),
                "Uses logging calls",
            ),
            "type_hints": (
                "->" in code or ": str" in code or ": int" in code,
                "Has type hints",
            ),
        }

        for check_name, (passed, rationale) in structure_checks.items():
            structure_scoring.add_check(check_name, passed, 0.6, rationale)

        if structure_scoring.earned_points >= 3:
            result["tests_passed"]["good_structure"] = True

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

                # Always provide a deterministic, schema-correct dataset for Prompt 1
                curated_users = [
                    {
                        "id": "101",
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "contact": {"email": "jane.doe@example.com"},
                        "profile": {"country": "USA"},
                        "stats": {"age": 28, "total_posts": 15},
                    },
                    {
                        "id": "102",
                        "first_name": "Emily",
                        "last_name": "White",
                        "contact": {"email": "emily.white@example.com"},
                        "profile": {"country": "USA"},
                        "stats": {"age": 25, "total_posts": 7},
                    },
                    {
                        "id": "103",
                        "first_name": "Lucas",
                        "last_name": "Martin",
                        "contact": {"email": "lucas@example.fr"},
                        "profile": {"country": "France"},
                        "stats": {"age": 30, "total_posts": 3},
                    },
                ]

                def _coerce_users_payload(data):
                    # Accept repo test data if present, but guarantee {"users": [...]} shape
                    if data is None:
                        return {"users": curated_users}
                    if isinstance(data, dict) and isinstance(data.get("users"), list):
                        return data
                    if isinstance(data, list):
                        return {"users": data}
                    # Anything else: fall back to deterministic set
                    return {"users": curated_users}

                payload = _coerce_users_payload(self.user_data)

                with open(test_data, "w", encoding="utf-8") as f:
                    json.dump(payload, f)

                # Run the script
                cmd = [sys.executable, str(solution_file.resolve()), str(test_config)]
                proc = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True, timeout=10)

                if proc.returncode == 0:
                    execution_scoring.add_check(
                        "runs_without_error", True, 4.0, "Script executes successfully"
                    )
                    result["tests_passed"]["runs_successfully"] = True

                    # Check output contains expected users - enhanced validation
                    output = proc.stdout

                    # Enhanced JSON parsing validation
                    json_parsed = False

                    try:
                        # Attempt to parse stdout as JSON
                        if output.strip():
                            # First try to parse the entire output as JSON (in case it's
                            # pretty-printed)
                            try:
                                # Skip the "Processed Records:" line and try to parse the rest
                                lines = output.strip().split("\n")
                                json_start_line = None
                                for i, line in enumerate(lines):
                                    if line.strip().startswith("["):
                                        json_start_line = i
                                        break

                                if json_start_line is not None:
                                    # Join all lines from the JSON start to form complete JSON
                                    json_content = "\n".join(lines[json_start_line:]).strip()
                                    output_data = json.loads(json_content)
                                    json_parsed = True

                                    # Validate JSON structure
                                    if isinstance(output_data, list):
                                        # Check if output contains expected USA users (Jane, Emily)
                                        jane_found = any(
                                            "Jane" in str(user.get("full_name", ""))
                                            or "Jane" in str(user.get("first_name", ""))
                                            for user in output_data
                                            if isinstance(user, dict)
                                        )
                                        emily_found = any(
                                            "Emily" in str(user.get("full_name", ""))
                                            or "Emily" in str(user.get("first_name", ""))
                                            for user in output_data
                                            if isinstance(user, dict)
                                        )

                                        if jane_found and emily_found:
                                            execution_scoring.add_check(
                                                "json_output_validation",
                                                True,
                                                2.0,
                                                "Valid JSON output with expected USA users "
                                                "(Jane, Emily)",
                                            )
                                        elif jane_found or emily_found:
                                            execution_scoring.add_check(
                                                "json_output_validation",
                                                True,
                                                1.5,
                                                "Valid JSON output with some expected users",
                                            )
                                        elif len(output_data) > 0:
                                            execution_scoring.add_check(
                                                "json_output_validation",
                                                True,
                                                1.0,
                                                "Valid JSON output but expected users not found",
                                            )
                                        else:
                                            execution_scoring.add_check(
                                                "json_output_validation",
                                                True,
                                                0.5,
                                                "Valid JSON output but empty result",
                                            )
                                    else:
                                        execution_scoring.add_check(
                                            "json_output_validation",
                                            True,
                                            0.5,
                                            "JSON parseable but not expected list structure",
                                        )
                            except json.JSONDecodeError:
                                # Try single line parsing as fallback
                                for line in lines:
                                    if line.strip().startswith("[") or line.strip().startswith("{"):
                                        try:
                                            output_data = json.loads(line.strip())
                                            json_parsed = True
                                            execution_scoring.add_check(
                                                "json_output_validation",
                                                True,
                                                1.0,
                                                "Valid single-line JSON output found",
                                            )
                                            break
                                        except json.JSONDecodeError:
                                            continue

                    except Exception:
                        json_parsed = False

                    if not json_parsed:
                        # Fallback to substring validation for backward compatibility
                        if "Jane" in output and "Emily" in output:
                            execution_scoring.add_check(
                                "basic_filtering_check",
                                True,
                                1.0,
                                "USA filtering detected in output (non-JSON)",
                            )
                        else:
                            execution_scoring.add_check(
                                "filtering_validation",
                                False,
                                0.0,
                                "No expected users found and output not valid JSON",
                            )
                else:
                    execution_scoring.add_check(
                        "runs_without_error",
                        False,
                        4.0,
                        f"Runtime error: {proc.stderr[:100]}",
                    )
                    execution_scoring.add_check(
                        "correct_filtering",
                        False,
                        2.0,
                        "Cannot test filtering due to runtime error",
                    )

        except Exception as e:
            execution_scoring.add_check(
                "runs_without_error", False, 4.0, f"Error testing script: {e!s}"
            )
            execution_scoring.add_check(
                "correct_filtering", False, 2.0, "Cannot test filtering due to execution error"
            )

        # Test 4: Code quality checks (3 points)
        quality_checks = {
            "no_global_vars": (
                not any(
                    line.strip().startswith(("global ", "globals()")) for line in code.split("\n")
                ),
                "No global variables",
            ),
            "uses_pathlib": (
                "pathlib" in code or "Path" in code,
                "Uses modern pathlib",
            ),
            "has_main_guard": (
                'if __name__ == "__main__"' in code or "if __name__ == '__main__'" in code,
                "Has main guard",
            ),
            "proper_file_handling": (
                "with open" in code or ".open(" in code,
                "Uses context managers",
            ),
        }

        for check_name, (passed, rationale) in quality_checks.items():
            quality_scoring.add_check(check_name, passed, 0.75, rationale)

        if quality_scoring.earned_points >= 2.0:
            result["tests_passed"]["good_quality"] = True

        # Test 5: Security Analysis (4 points) - NEW!
        security_analysis = SecurityAnalyzer.analyze_code_security(code)

        if security_analysis["is_secure"]:
            security_scoring.add_check(
                "no_security_issues", True, 4.0, "No security vulnerabilities detected"
            )
            result["tests_passed"]["secure_code"] = True
        else:
            # Partial credit based on analysis (capped at category max)
            security_scoring.earned_points = min(4.0, security_analysis["score"])

            # Add specific security checks
            if "sql_injection" not in security_analysis["issues"]:
                security_scoring.add_check(
                    "no_sql_injection", True, 0.0, "No SQL injection patterns"
                )
            else:
                security_scoring.add_check(
                    "no_sql_injection",
                    False,
                    0.0,
                    f"SQL injection risks: {len(security_analysis['issues']['sql_injection'])}",
                )

            if "hardcoded_secret" not in security_analysis["issues"]:
                security_scoring.add_check(
                    "no_hardcoded_secrets", True, 0.0, "No hardcoded secrets"
                )
            else:
                security_scoring.add_check(
                    "no_hardcoded_secrets",
                    False,
                    0.0,
                    f"Hardcoded secrets found: "
                    f"{len(security_analysis['issues']['hardcoded_secret'])}",
                )

            if "path_traversal" not in security_analysis["issues"]:
                security_scoring.add_check(
                    "no_path_traversal", True, 0.0, "No path traversal risks"
                )
            else:
                security_scoring.add_check(
                    "no_path_traversal",
                    False,
                    0.0,
                    f"Path traversal risks: {len(security_analysis['issues']['path_traversal'])}",
                )

            if "unsafe_execution" not in security_analysis["issues"]:
                security_scoring.add_check("no_unsafe_execution", True, 0.0, "No unsafe execution")
            else:
                security_scoring.add_check(
                    "no_unsafe_execution",
                    False,
                    0.0,
                    f"Unsafe execution patterns: "
                    f"{len(security_analysis['issues']['unsafe_execution'])}",
                )

        # Test 6: Performance Analysis (2 points)
        performance_analysis = PerformanceAnalyzer.analyze_code_performance(code)

        if performance_analysis["is_efficient"]:
            performance_scoring.add_check(
                "no_performance_issues", True, 2.0, "No performance issues detected"
            )
            result["tests_passed"]["efficient_code"] = True
        else:
            # Partial credit based on analysis (scale to 2.0 max)
            performance_scoring.earned_points = min(
                2.0, performance_analysis["score"] * (2.0 / 3.0)
            )

            # Add specific performance checks
            if "nested_loops" not in performance_analysis["issues"]:
                performance_scoring.add_check("no_nested_loops", True, 0.0, "No O(n²) patterns")
            else:
                performance_scoring.add_check(
                    "no_nested_loops",
                    False,
                    0.0,
                    f"Nested loop patterns: {len(performance_analysis['issues']['nested_loops'])}",
                )

        # Test 7: Maintainability Analysis (2 points) - NEW!
        maintainability_analysis = MaintainabilityAnalyzer.analyze_code_maintainability(code)

        if maintainability_analysis["is_maintainable"]:
            maintainability_scoring.add_check(
                "no_maintainability_issues", True, 2.0, "No maintainability issues detected"
            )
            result["tests_passed"]["maintainable_code"] = True
        else:
            # Use the exact score from analysis
            maintainability_scoring.earned_points = maintainability_analysis["score"]

            # Add specific maintainability checks
            if "long_function" not in maintainability_analysis["issues"]:
                maintainability_scoring.add_check(
                    "no_long_functions", True, 0.0, "Functions are appropriately sized"
                )
            else:
                maintainability_scoring.add_check(
                    "no_long_functions",
                    False,
                    0.0,
                    f"Long functions: {len(maintainability_analysis['issues']['long_function'])}",
                )

            if "code_duplication" not in maintainability_analysis["issues"]:
                maintainability_scoring.add_check(
                    "no_duplication", True, 0.0, "No code duplication"
                )
            else:
                maintainability_scoring.add_check(
                    "no_duplication", False, 0.0, "Code duplication detected"
                )

            if "poor_naming" not in maintainability_analysis["issues"]:
                maintainability_scoring.add_check("good_naming", True, 0.0, "Good variable naming")
            else:
                maintainability_scoring.add_check(
                    "good_naming", False, 0.0, "Poor variable naming detected"
                )

        # Calculate final scores and generate feedback (Updated for all 7 categories)
        result["score"] = (
            syntax_scoring.earned_points
            + structure_scoring.earned_points
            + execution_scoring.earned_points
            + quality_scoring.earned_points
            + security_scoring.earned_points
            + performance_scoring.earned_points
            + maintainability_scoring.earned_points  # NEW!
        )

        result["detailed_scoring"] = {
            "syntax": {
                "earned": syntax_scoring.earned_points,
                "max": syntax_scoring.max_points,
            },
            "structure": {
                "earned": structure_scoring.earned_points,
                "max": structure_scoring.max_points,
            },
            "execution": {
                "earned": execution_scoring.earned_points,
                "max": execution_scoring.max_points,
            },
            "quality": {
                "earned": quality_scoring.earned_points,
                "max": quality_scoring.max_points,
            },
            "security": {
                "earned": security_scoring.earned_points,
                "max": security_scoring.max_points,
            },
            "performance": {
                "earned": performance_scoring.earned_points,
                "max": performance_scoring.max_points,
            },
            "maintainability": {  # NEW!
                "earned": maintainability_scoring.earned_points,
                "max": maintainability_scoring.max_points,
            },
        }

        # Add detailed feedback (Updated with all categories)
        result["feedback"] = [
            syntax_scoring.get_feedback_line("Python Syntax"),
            structure_scoring.get_feedback_line("Code Structure"),
            execution_scoring.get_feedback_line("Execution"),
            quality_scoring.get_feedback_line("Code Quality"),
            security_scoring.get_feedback_line("Security Analysis"),
            performance_scoring.get_feedback_line("Performance Analysis"),
            maintainability_scoring.get_feedback_line("Maintainability Analysis"),  # NEW!
        ]

        # Determine if passed
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_2_yaml_json(self, yaml_file: Path, json_file: Path) -> dict[str, Any]:
        """Validate Prompt 2: YAML/JSON Correction with 7-category scoring."""

        # Initialize result with 7-category structure
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
            "detailed_scoring": {
                "syntax": {"earned": 0, "max": 4},
                "structure": {"earned": 0, "max": 6},
                "execution": {"earned": 0, "max": 8},
                "quality": {"earned": 0, "max": 6},
                "security": {"earned": 0, "max": 1},
                "performance": {"earned": 0, "max": 0},  # Removed
                "maintainability": {"earned": 0, "max": 0},  # Removed
            },
        }

        # Initialize category scoring
        syntax_scoring = ScoringDetail(4.0)
        structure_scoring = ScoringDetail(6.0)
        execution_scoring = ScoringDetail(8.0)
        quality_scoring = ScoringDetail(6.0)
        security_scoring = ScoringDetail(1.0)

        # Category 1: Syntax - YAML and JSON parsing (4pts)
        yaml_data = None
        json_data = None

        # YAML parsing (2pts)
        if not yaml_file.exists():
            syntax_scoring.add_check("yaml_exists", False, 0, "YAML file not found")
        else:
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    yaml_data = yaml.safe_load(f)
                syntax_scoring.add_check("yaml_parses", True, 2.0, "YAML parses with safe loader")
                result["tests_passed"]["valid_yaml"] = True
            except yaml.YAMLError as e:
                syntax_scoring.add_check("yaml_parses", False, 0, f"YAML parsing failed: {e}")

        # JSON parsing (2pts)
        if not json_file.exists():
            syntax_scoring.add_check("json_exists", False, 0, "JSON file not found")
        else:
            try:
                with open(json_file, encoding="utf-8") as f:
                    json_data = json.load(f)
                syntax_scoring.add_check("json_parses", True, 2.0, "JSON parses successfully")
                result["tests_passed"]["valid_json"] = True
            except json.JSONDecodeError as e:
                syntax_scoring.add_check("json_parses", False, 0, f"JSON parsing failed: {e}")

        # Category 2: Structure - Data integrity and shape validation (6pts)
        if yaml_data and json_data:
            # Required top-level keys (3pts)
            expected_keys = {
                "use_legacy_paths",
                "paths",
                "validation_rules",
                "api_keys",
                "feature_flags",
                "server_settings",
            }

            yaml_keys = set(yaml_data.keys()) if isinstance(yaml_data, dict) else set()
            json_keys = set(json_data.keys()) if isinstance(json_data, dict) else set()

            yaml_has_all = expected_keys.issubset(yaml_keys)
            json_has_all = expected_keys.issubset(json_keys)

            if yaml_has_all and json_has_all:
                structure_scoring.add_check(
                    "required_keys", True, 3.0, "All required sections preserved"
                )
                result["tests_passed"]["structure_preserved"] = True
            elif yaml_has_all or json_has_all:
                structure_scoring.add_check(
                    "required_keys", False, 1.5, "Some required sections missing"
                )
            else:
                structure_scoring.add_check("required_keys", False, 0, "Major sections missing")

            # Nested shapes match (2pts)
            # Check that dictionaries are dictionaries, lists are lists
            shape_matches = 0
            total_shape_checks = 0

            for key in ["paths", "validation_rules", "server_settings"]:
                if key in yaml_data and key in json_data:
                    total_shape_checks += 1
                    if isinstance(yaml_data[key], dict) and isinstance(json_data[key], dict):
                        shape_matches += 1

            if total_shape_checks > 0:
                shape_score = 2.0 * (shape_matches / total_shape_checks)
                structure_scoring.add_check(
                    "nested_shapes",
                    shape_matches == total_shape_checks,
                    shape_score,
                    f"Nested shapes: {shape_matches}/{total_shape_checks} correct",
                )

            # Arrays vs scalars (1pt)
            # Check api_keys is list, feature_flags values are proper types
            array_scalar_correct = True
            if ("api_keys" in yaml_data and "api_keys" in json_data
                    and not (isinstance(yaml_data["api_keys"], list)
                             and isinstance(json_data["api_keys"], list))):
                array_scalar_correct = False

            structure_scoring.add_check(
                "arrays_scalars",
                array_scalar_correct,
                1.0 if array_scalar_correct else 0,
                "Arrays and scalars in correct positions",
            )

        # Category 3: Execution - Cross-format equivalence testing (8pts)
        if yaml_data and json_data:
            # Deep equivalence after normalization (6pts)
            def normalize_for_comparison(data):
                """Normalize data for accurate comparison"""
                if isinstance(data, dict):
                    normalized = {}
                    for k, v in data.items():
                        normalized[k] = normalize_for_comparison(v)
                    return normalized
                elif isinstance(data, list):
                    return [normalize_for_comparison(item) for item in data]
                elif isinstance(data, str):
                    # Convert string booleans and numbers
                    lower_val = data.lower()
                    if lower_val in ("true", "false"):
                        return lower_val == "true"
                    try:
                        # Try integer first
                        if "." not in data:
                            return int(data)
                        else:
                            return float(data)
                    except ValueError:
                        return data
                else:
                    return data

            try:
                normalized_yaml = normalize_for_comparison(yaml_data)
                normalized_json = normalize_for_comparison(json_data)

                # Deep comparison
                def deep_compare(obj1, obj2, path=""):
                    if not isinstance(obj1, type(obj2)):
                        return False, f"Type mismatch at {path}: {type(obj1)} vs {type(obj2)}"

                    if isinstance(obj1, dict):
                        if set(obj1.keys()) != set(obj2.keys()):
                            return False, f"Key mismatch at {path}"
                        for key in obj1:
                            equal, msg = deep_compare(obj1[key], obj2[key], f"{path}.{key}")
                            if not equal:
                                return False, msg
                    elif isinstance(obj1, list):
                        if len(obj1) != len(obj2):
                            return False, f"Length mismatch at {path}"
                        for i, (item1, item2) in enumerate(zip(obj1, obj2, strict=False)):
                            equal, msg = deep_compare(item1, item2, f"{path}[{i}]")
                            if not equal:
                                return False, msg
                    elif obj1 != obj2:
                        return False, f"Value mismatch at {path}: {obj1} vs {obj2}"

                    return True, "Match"

                is_equivalent, comparison_msg = deep_compare(normalized_yaml, normalized_json)

                if is_equivalent:
                    execution_scoring.add_check(
                        "deep_equivalence", True, 6.0, "Perfect cross-format equivalence"
                    )
                    result["tests_passed"]["equivalence_test"] = True
                else:
                    execution_scoring.add_check(
                        "deep_equivalence", False, 0, f"Equivalence failed: {comparison_msg}"
                    )

                # Partial credit for per-key matches (2pts)
                key_matches = 0
                total_keys = len(expected_keys)

                for key in expected_keys:
                    if (
                        isinstance(normalized_yaml, dict)
                        and isinstance(normalized_json, dict)
                        and key in normalized_yaml
                        and key in normalized_json
                        and normalized_yaml[key] == normalized_json[key]
                    ):
                        key_matches += 1

                partial_score = 2.0 * (key_matches / total_keys) if total_keys > 0 else 0
                execution_scoring.add_check(
                    "partial_matches",
                    key_matches > 0,
                    partial_score,
                    f"Per-key matches: {key_matches}/{total_keys}",
                )

            except Exception as e:
                execution_scoring.add_check(
                    "equivalence_test", False, 0, f"Equivalence testing failed: {e}"
                )

        # First, check for YAML duplicates
        yaml_has_duplicates = False
        duplicate_error_msg = ""
        if yaml_file.exists():
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    yaml.load(f, Loader=UniqueKeyLoader)
                # If load succeeds, no duplicates
            except ConstructorError as e:
                yaml_has_duplicates = True
                # Use the exception to enrich details so Ruff is happy and users see why it failed
                duplicate_error_msg = str(e)

        # Category 4: Quality - Format standards and linting (6pts)
        quality_checks = {
            "yaml_indentation": {"passed": True, "points": 2.0, "details": []},
            "json_literals": {"passed": True, "points": 2.0, "details": []},
            "formatting_style": {"passed": True, "points": 1.0, "details": []},
            "no_duplication": {
                "passed": not yaml_has_duplicates,
                "points": 1.0,
                "details": [duplicate_error_msg]
                if yaml_has_duplicates and duplicate_error_msg
                else ["Duplicate YAML keys detected"]
                if yaml_has_duplicates
                else [],
            },
        }

        # If we caught duplicates, use the exception to enrich details
        if yaml_has_duplicates and yaml_file.exists():
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    yaml.load(f, Loader=UniqueKeyLoader)
            except ConstructorError as e:
                # Use the exception to enrich details so Ruff is happy and users see why it failed
                quality_checks["no_duplication"]["details"].append(str(e))

        # YAML indentation check (2pts)
        if yaml_file.exists():
            with open(yaml_file, encoding="utf-8") as f:
                yaml_content = f.read()

            # Check for tabs
            if "\t" in yaml_content:
                quality_checks["yaml_indentation"]["passed"] = False
                quality_checks["yaml_indentation"]["details"].append(
                    "Contains tabs instead of spaces"
                )

            # Check for consistent indentation (basic check)
            lines = yaml_content.split("\n")
            indent_levels = set()
            for line in lines:
                if line.strip():  # Non-empty line
                    leading_spaces = len(line) - len(line.lstrip(" "))
                    if leading_spaces > 0:
                        indent_levels.add(leading_spaces)

            # Should be multiples of 2
            if not all(level % 2 == 0 for level in indent_levels):
                quality_checks["yaml_indentation"]["passed"] = False
                quality_checks["yaml_indentation"]["details"].append(
                    "Inconsistent indentation (not 2-space multiples)"
                )

        # JSON literals check (2pts)
        if json_data:
            # Check for proper boolean/null literals (not strings)
            expected_booleans = ["use_legacy_paths"]

            for bool_key in expected_booleans:
                if bool_key in json_data and not isinstance(json_data[bool_key], bool):
                    quality_checks["json_literals"]["passed"] = False
                    quality_checks["json_literals"]["details"].append(
                        f"{bool_key} should be boolean, not string"
                    )

            # Check for integer types in validation_rules and server_settings
            expected_integers = [("validation_rules", "min_age_years"), ("server_settings", "port")]

            for section, int_key in expected_integers:
                if (section in json_data and int_key in json_data[section]
                        and not isinstance(json_data[section][int_key], int)):
                    quality_checks["json_literals"]["passed"] = False
                    quality_checks["json_literals"]["details"].append(
                        f"{section}.{int_key} should be integer, not string"
                    )

        # Apply quality scoring
        for check_name, check_data in quality_checks.items():
            points = check_data["points"] if check_data["passed"] else 0
            details = "; ".join(check_data["details"]) if check_data["details"] else "Correct"
            quality_scoring.add_check(check_name, check_data["passed"], points, details)

        # Category 5: Security - YAML safety only (1pt)
        security_issues = []

        if yaml_file.exists():
            with open(yaml_file, encoding="utf-8") as f:
                yaml_content = f.read()

            # Check for dangerous YAML constructs
            dangerous_patterns = [
                r"!!python/",  # Python object instantiation
                r"!!map",  # Explicit mapping (can be dangerous)
                # Removed anchor/alias checks - safe with yaml.safe_load
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, yaml_content):
                    security_issues.append(f"Dangerous YAML construct: {pattern}")

        has_security_issues = len(security_issues) > 0
        security_scoring.add_check(
            "yaml_safety",
            not has_security_issues,
            1.0 if not has_security_issues else 0,
            "No dangerous YAML constructs"
            if not has_security_issues
            else f"Issues: {'; '.join(security_issues)}",
        )

        # Aggregate all scores
        categories = [
            ("syntax", syntax_scoring),
            ("structure", structure_scoring),
            ("execution", execution_scoring),
            ("quality", quality_scoring),
            ("security", security_scoring),
        ]

        total_score = 0
        for category_name, scoring in categories:
            category_score = scoring.earned_points
            total_score += category_score

            result["detailed_scoring"][category_name]["earned"] = category_score
            result["feedback"].append(scoring.get_feedback_line(category_name.title()))

        # Legacy compatibility checks
        if yaml_data and json_data:
            # Type corrections check for legacy compatibility
            type_checks = {
                "use_legacy_paths": isinstance(json_data.get("use_legacy_paths"), bool),
                "min_age_years": isinstance(
                    json_data.get("validation_rules", {}).get("min_age_years"), int
                ),
                "port": isinstance(json_data.get("server_settings", {}).get("port"), int),
                "enable_email_notifications": isinstance(
                    json_data.get("feature_flags", {}).get("enable_email_notifications"),
                    bool,
                ),
            }

            correct_types = sum(1 for check in type_checks.values() if check)
            if correct_types == len(type_checks):
                result["tests_passed"]["correct_types"] = True

        result["score"] = total_score
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_3_transformation(self, transform_file: Path) -> dict[str, Any]:
        """Validate Prompt 3: Data Transformation with 7-category scoring."""

        # Initialize result with 7-category structure
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
            "detailed_scoring": {
                "syntax": {"earned": 0, "max": 3},
                "structure": {"earned": 0, "max": 3},
                "execution": {"earned": 0, "max": 12},  # MAJOR UPGRADE
                "quality": {"earned": 0, "max": 3},
                "security": {"earned": 0, "max": 1},  # REDUCED
                "performance": {"earned": 0, "max": 1},  # REDUCED
                "maintainability": {"earned": 0, "max": 2},
            },
        }

        # Initialize category scoring
        syntax_scoring = ScoringDetail(3.0)
        structure_scoring = ScoringDetail(3.0)
        execution_scoring = ScoringDetail(12.0)  # MASSIVE
        quality_scoring = ScoringDetail(3.0)
        security_scoring = ScoringDetail(1.0)  # MINIMAL
        performance_scoring = ScoringDetail(1.0)  # MINIMAL
        maintainability_scoring = ScoringDetail(2.0)

        # Check file existence first
        if not transform_file.exists():
            result["feedback"].append("❌ Transform file not found")
            return result

        # Category 1: Syntax - File imports and compiles
        try:
            # Load the transform module
            spec = importlib.util.spec_from_file_location("transform_module", transform_file)
            if spec is None or spec.loader is None:
                syntax_scoring.add_check("module_load", False, 0, "Could not create module spec")
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

            transform_module = importlib.util.module_from_spec(spec)

            # Test compilation (2pts)
            try:
                spec.loader.exec_module(transform_module)
                syntax_scoring.add_check("file_compiles", True, 2.0, "File imports and compiles")
            except Exception as e:
                syntax_scoring.add_check("file_compiles", False, 0, f"Compilation failed: {e}")
                # Can't continue without valid module
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

            # Function loads (1pt)
            if hasattr(transform_module, "transform_and_enrich_users"):
                syntax_scoring.add_check("function_exists", True, 1.0, "Function exists")
                transform_function = transform_module.transform_and_enrich_users
            else:
                syntax_scoring.add_check(
                    "function_exists", False, 0, "Function 'transform_and_enrich_users' not found"
                )
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

        except Exception as e:
            syntax_scoring.add_check("module_load", False, 0, f"Module loading failed: {e}")
            total_score = syntax_scoring.earned_points
            result["score"] = total_score
            result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
            result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
            return result

        # Category 2: Structure - Function specification and organization
        import inspect

        # Exact signature check (2pts)
        try:
            sig = inspect.signature(transform_function)
            expected_params = ["user_list"]  # Single parameter expected
            actual_params = list(sig.parameters.keys())

            if actual_params == expected_params:
                structure_scoring.add_check(
                    "correct_signature",
                    True,
                    2.0,
                    "Exact signature: transform_and_enrich_users(user_list)",
                )
            else:
                structure_scoring.add_check(
                    "correct_signature",
                    False,
                    0,
                    f"Wrong signature: expected {expected_params}, got {actual_params}",
                )

        except Exception as e:
            structure_scoring.add_check(
                "signature_check", False, 0, f"Signature inspection failed: {e}"
            )

        # Basic organization (1pt) - check if function body is reasonable
        try:
            with open(transform_file, encoding="utf-8") as f:
                source_code = f.read()

            # Basic checks for reasonable function structure
            has_return = "return" in source_code.lower()
            has_loop_or_comprehension = any(
                keyword in source_code.lower()
                for keyword in ["for ", "while ", "[", "map(", "filter("]
            )

            if has_return and has_loop_or_comprehension:
                structure_scoring.add_check(
                    "basic_organization", True, 1.0, "Has return statement and iteration logic"
                )
            else:
                structure_scoring.add_check(
                    "basic_organization", False, 0.5, "Basic structure present but incomplete"
                )

        except Exception as e:
            structure_scoring.add_check(
                "organization_check", False, 0, f"Code analysis failed: {e}"
            )

        # Category 3: Execution - Comprehensive transformation testing
        # Load test data
        test_data_file = self.test_data_dir / "user_data.json"
        if not test_data_file.exists():
            execution_scoring.add_check("test_data_missing", False, 0, "Test data file missing")
        else:
            with open(test_data_file, encoding="utf-8") as f:
                test_data = json.load(f)

            users = test_data.get("users", [])

            # Add malformed record for error handling test (GPT requirement)
            malformed_user = {
                "id": "999",
                "first_name": "Test",
                "last_name": "User",
                # Missing 'contact' and 'stats' - this should test graceful handling
            }
            test_users = [*users, malformed_user]

            try:
                # Run the transformation function (2pts for not crashing)
                result_users = transform_function(test_users)
                execution_scoring.add_check(
                    "function_runs", True, 2.0, "Function runs without crashing"
                )

                if not isinstance(result_users, list):
                    execution_scoring.add_check(
                        "returns_list", False, 0, "Function must return a list"
                    )
                else:
                    # Test 1: ID standardization (2pts)
                    id_standardized = 0
                    total_users = len(users)  # Don't count malformed user for this test

                    for _i, user in enumerate(result_users[:total_users]):
                        if isinstance(user.get("id"), int):
                            id_standardized += 1

                    if id_standardized == total_users:
                        execution_scoring.add_check(
                            "id_standardization",
                            True,
                            2.0,
                            f"All {total_users} IDs converted to integers",
                        )
                    elif id_standardized > 0:
                        partial_score = 2.0 * (id_standardized / total_users)
                        execution_scoring.add_check(
                            "id_standardization",
                            False,
                            partial_score,
                            f"{id_standardized}/{total_users} IDs converted",
                        )
                    else:
                        execution_scoring.add_check(
                            "id_standardization", False, 0, "No ID standardization detected"
                        )

                    # Test 2: Email provider extraction (2pts)
                    email_providers_correct = 0
                    users_with_email = 0

                    for _i, (original, transformed) in enumerate(
                        zip(users, result_users[:total_users], strict=False)
                    ):
                        original_email = original.get("contact", {}).get("email")
                        if original_email:  # Only test users who have email
                            users_with_email += 1
                            transformed_contact = transformed.get("contact", {})

                            if "email_provider" in transformed_contact:
                                expected_provider = (
                                    original_email.split("@")[-1] if "@" in original_email else None
                                )
                                if transformed_contact["email_provider"] == expected_provider:
                                    email_providers_correct += 1

                    if users_with_email > 0:
                        if email_providers_correct == users_with_email:
                            execution_scoring.add_check(
                                "email_provider",
                                True,
                                2.0,
                                f"All {users_with_email} email providers extracted correctly",
                            )
                        else:
                            partial_score = 2.0 * (email_providers_correct / users_with_email)
                            execution_scoring.add_check(
                                "email_provider",
                                False,
                                partial_score,
                                f"{email_providers_correct}/{users_with_email} providers correct",
                            )
                    else:
                        execution_scoring.add_check(
                            "email_provider", False, 0, "No email providers to test"
                        )

                    # Test 3: **AGE NORMALIZATION** (2pts) - GPT-IDENTIFIED MISSING TEST
                    ages_normalized = 0
                    users_with_age = 0

                    for _i, transformed in enumerate(result_users[:total_users]):
                        stats = transformed.get("stats", {})
                        if "age" in stats:
                            users_with_age += 1
                            if isinstance(stats["age"], int):
                                ages_normalized += 1

                    if users_with_age > 0:
                        if ages_normalized == users_with_age:
                            execution_scoring.add_check(
                                "age_normalization",
                                True,
                                2.0,
                                f"All {users_with_age} ages converted to integers",
                            )
                        else:
                            partial_score = 2.0 * (ages_normalized / users_with_age)
                            execution_scoring.add_check(
                                "age_normalization",
                                False,
                                partial_score,
                                f"{ages_normalized}/{users_with_age} ages normalized",
                            )
                    else:
                        execution_scoring.add_check(
                            "age_normalization", False, 0, "No ages to normalize"
                        )

                    # Test 4: **BUSINESS RULES VALIDATION** (3pts) - GPT REQUIREMENT:
                    # Rule-based not magic IDs
                    # Define the documented business rules (these should be added to prompt text)
                    def calculate_expected_tier(posts, comments):
                        if posts > 100 and comments > 300:
                            return "Gold"
                        elif posts > 50:
                            return "Silver"
                        else:
                            return "Bronze"

                    tier_correct = 0
                    users_tested = 0

                    for _i, (original, transformed) in enumerate(
                        zip(users, result_users[:total_users], strict=False)
                    ):
                        original_stats = original.get("stats", {})
                        posts = original_stats.get("total_posts", 0)
                        comments = original_stats.get("total_comments", 0)

                        expected_tier = calculate_expected_tier(posts, comments)
                        actual_tier = transformed.get("account_tier")

                        users_tested += 1
                        if actual_tier == expected_tier:
                            tier_correct += 1

                    if users_tested > 0:
                        if tier_correct == users_tested:
                            execution_scoring.add_check(
                                "account_tiers",
                                True,
                                3.0,
                                f"All {users_tested} account tiers correct",
                            )
                        else:
                            partial_score = 3.0 * (tier_correct / users_tested)
                            execution_scoring.add_check(
                                "account_tiers",
                                False,
                                partial_score,
                                f"{tier_correct}/{users_tested} tiers correct",
                            )

                    # Test 5: **GRACEFUL ERROR HANDLING** (1pt) - GPT REQUIREMENT
                    # Check if malformed user was handled gracefully
                    malformed_handled_gracefully = (
                        len(result_users) >= total_users
                    )  # At least original users returned

                    if malformed_handled_gracefully:
                        # Check if malformed user either skipped or handled with defaults
                        if len(result_users) == total_users:
                            execution_scoring.add_check(
                                "error_handling", True, 1.0, "Malformed record skipped gracefully"
                            )
                        elif len(result_users) == total_users + 1:
                            # Check if malformed user has some default values
                            malformed_result = result_users[-1]
                            has_some_processing = (
                                "id" in malformed_result or "account_tier" in malformed_result
                            )
                            if has_some_processing:
                                execution_scoring.add_check(
                                    "error_handling",
                                    True,
                                    1.0,
                                    "Malformed record handled with defaults",
                                )
                            else:
                                execution_scoring.add_check(
                                    "error_handling",
                                    False,
                                    0.5,
                                    "Malformed record present but unprocessed",
                                )
                        else:
                            execution_scoring.add_check(
                                "error_handling",
                                False,
                                0.5,
                                "Unexpected result count with malformed record",
                            )
                    else:
                        execution_scoring.add_check(
                            "error_handling", False, 0, "Function failed with malformed input"
                        )

            except Exception as e:
                execution_scoring.add_check(
                    "execution_failed", False, 0, f"Function execution failed: {e}"
                )

        # Category 4: Quality - Error handling and code patterns
        try:
            with open(transform_file, encoding="utf-8") as f:
                code = f.read()

            # Try/catch around transformations (1pt)
            has_try_except = "try:" in code and "except" in code
            quality_scoring.add_check(
                "try_except",
                has_try_except,
                1.0 if has_try_except else 0,
                "Has try/except for error handling"
                if has_try_except
                else "Missing try/except blocks",
            )

            # Proper type conversions (1pt)
            has_type_conversion = any(
                pattern in code.lower() for pattern in ["int(", "str(", "float(", "bool("]
            )
            quality_scoring.add_check(
                "type_conversions",
                has_type_conversion,
                1.0 if has_type_conversion else 0,
                "Uses type conversion functions"
                if has_type_conversion
                else "No explicit type conversions",
            )

            # Readable loop structure (1pt)
            has_readable_iteration = any(
                pattern in code for pattern in ["for user in", "for item in", "for record in"]
            )
            quality_scoring.add_check(
                "readable_loops",
                has_readable_iteration,
                1.0 if has_readable_iteration else 0,
                "Readable iteration patterns"
                if has_readable_iteration
                else "Less readable iteration",
            )

        except Exception as e:
            quality_scoring.add_check("quality_analysis", False, 0, f"Quality analysis failed: {e}")

        # Category 5: Security - Minimal checks for in-memory transform
        try:
            with open(transform_file, encoding="utf-8") as f:
                code = f.read()

            # Check for dangerous constructs
            dangerous_patterns = [
                "eval(",
                "exec(",
                "__import__",
                "open(",
                "file(",
                "input(",
                "raw_input(",
            ]
            security_issues = [pattern for pattern in dangerous_patterns if pattern in code.lower()]

            if not security_issues:
                security_scoring.add_check(
                    "no_unsafe_constructs", True, 1.0, "No dangerous constructs detected"
                )
            else:
                security_scoring.add_check(
                    "no_unsafe_constructs",
                    False,
                    0,
                    f"Dangerous constructs: {', '.join(security_issues)}",
                )

        except Exception as e:
            security_scoring.add_check(
                "security_analysis", False, 0, f"Security analysis failed: {e}"
            )

        # Category 6: Performance - Basic efficiency
        try:
            with open(transform_file, encoding="utf-8") as f:
                code = f.read()

            # Simple heuristic - check for nested loops
            lines = code.split("\n")
            nested_detected = False
            for i, line in enumerate(lines):
                if "for " in line.strip():
                    # Look for nested for loops in subsequent indented lines
                    current_indent = len(line) - len(line.lstrip())
                    for j in range(i + 1, min(i + 10, len(lines))):  # Check next 10 lines
                        next_line = lines[j]
                        if next_line.strip():
                            next_indent = len(next_line) - len(next_line.lstrip())
                            if next_indent > current_indent and "for " in next_line:
                                nested_detected = True
                                break

            if not nested_detected:
                performance_scoring.add_check(
                    "single_pass",
                    True,
                    1.0,
                    "No nested loops detected - efficient single-pass processing",
                )
            else:
                performance_scoring.add_check(
                    "single_pass", False, 0, "Potential O(n²) nested loop patterns detected"
                )

        except Exception as e:
            performance_scoring.add_check(
                "performance_analysis", False, 0, f"Performance analysis failed: {e}"
            )

        # Category 7: Maintainability - Use existing analyzer
        try:
            with open(transform_file, encoding="utf-8") as f:
                code = f.read()

            # Reuse maintainability analyzer from Prompt 1
            maintainability_analyzer = MaintainabilityAnalyzer()
            maintainability_result = maintainability_analyzer.analyze_code_maintainability(code)

            # Scale to 2 points max
            analyzer_score = maintainability_result.get("score", 0)
            scaled_score = min(2.0, analyzer_score)

            # Generate proper summary based on actual issues found
            issues = maintainability_result.get("issues", {})
            if not issues:
                summary = "No maintainability issues detected"
            else:
                issue_list = []
                for issue_type, issue_items in issues.items():
                    if issue_type == "long_function" and issue_items:
                        issue_list.append(f"{len(issue_items)} long function(s)")
                    elif issue_type == "code_duplication" and issue_items:
                        issue_list.append("code duplication")
                    elif issue_type == "poor_naming" and issue_items:
                        issue_list.append("poor naming")
                    elif issue_items:  # other issue types
                        issue_list.append(issue_type.replace("_", " "))

                if issue_list:
                    summary = f"Issues found: {', '.join(issue_list)}"
                else:
                    summary = "No maintainability issues detected"

            maintainability_scoring.add_check(
                "code_organization",
                analyzer_score > 1.0,
                scaled_score,
                f"Maintainability analysis: {summary}",
            )

        except Exception as e:
            maintainability_scoring.add_check(
                "maintainability_check", False, 0, f"Maintainability analysis failed: {e}"
            )

        # Aggregate all scores
        categories = [
            ("syntax", syntax_scoring),
            ("structure", structure_scoring),
            ("execution", execution_scoring),  # The heavy hitter - 12pts
            ("quality", quality_scoring),
            ("security", security_scoring),
            ("performance", performance_scoring),
            ("maintainability", maintainability_scoring),
        ]

        total_score = 0
        for category_name, scoring in categories:
            category_score = scoring.earned_points
            total_score += category_score

            result["detailed_scoring"][category_name]["earned"] = category_score
            result["feedback"].append(scoring.get_feedback_line(category_name.title()))

        # Legacy test flags for backward compatibility
        result["tests_passed"]["function_exists"] = syntax_scoring.earned_points >= 1.0
        result["tests_passed"]["no_crash"] = execution_scoring.earned_points >= 2.0
        result["tests_passed"]["id_standardization"] = any(
            "id" in check["name"].lower() and check["passed"] for check in execution_scoring.checks
        )
        result["tests_passed"]["email_provider"] = any(
            "email" in check["name"].lower() and check["passed"]
            for check in execution_scoring.checks
        )
        result["tests_passed"]["account_tiers"] = any(
            "tier" in check["name"].lower() and check["passed"]
            for check in execution_scoring.checks
        )

        result["score"] = total_score
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result

    def validate_prompt_4_api(self, api_file: Path) -> dict[str, Any]:
        """Validate Prompt 4: API Integration with behavioral testing."""

        # Initialize result with 7-category structure
        result = {
            "passed": False,
            "score": 0,
            "max_score": 25,
            "feedback": [],
            "tests_passed": {},
            "detailed_scoring": {
                "syntax": {"earned": 0, "max": 2},
                "structure": {"earned": 0, "max": 3},
                "execution": {"earned": 0, "max": 7},  # BEHAVIORAL
                "quality": {"earned": 0, "max": 3},
                "security": {"earned": 0, "max": 7},  # HIGHEST
                "performance": {"earned": 0, "max": 2},
                "maintainability": {"earned": 0, "max": 1},
            },
        }

        # Initialize category scoring
        syntax_scoring = ScoringDetail(2.0)
        structure_scoring = ScoringDetail(3.0)
        execution_scoring = ScoringDetail(7.0)  # BEHAVIORAL
        quality_scoring = ScoringDetail(3.0)
        security_scoring = ScoringDetail(7.0)  # HIGHEST
        performance_scoring = ScoringDetail(2.0)
        maintainability_scoring = ScoringDetail(1.0)

        if not api_file.exists():
            result["feedback"].append("❌ API file not found")
            return result

        # Category 1: Syntax - Basic compilation and imports
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location("api_module", api_file)
            if spec is None or spec.loader is None:
                syntax_scoring.add_check("module_load", False, 0, "Could not create module spec")
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

            api_module = importlib.util.module_from_spec(spec)

            # Test compilation (1pt)
            try:
                spec.loader.exec_module(api_module)
                syntax_scoring.add_check("file_compiles", True, 1.0, "File compiles and imports")
            except Exception as e:
                syntax_scoring.add_check("file_compiles", False, 0, f"Compilation failed: {e}")
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

            # Check for required function (1pt)
            if hasattr(api_module, "sync_users_to_crm"):
                syntax_scoring.add_check(
                    "function_exists", True, 1.0, "Function 'sync_users_to_crm' exists"
                )
                sync_function = api_module.sync_users_to_crm
            else:
                syntax_scoring.add_check(
                    "function_exists", False, 0, "Function 'sync_users_to_crm' not found"
                )
                total_score = syntax_scoring.earned_points
                result["score"] = total_score
                result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
                result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
                return result

        except Exception as e:
            syntax_scoring.add_check("module_load", False, 0, f"Module loading failed: {e}")
            total_score = syntax_scoring.earned_points
            result["score"] = total_score
            result["detailed_scoring"]["syntax"]["earned"] = syntax_scoring.earned_points
            result["feedback"].append(syntax_scoring.get_feedback_line("Syntax"))
            return result

        # Category 2: Structure - Function signature and request formation
        import inspect

        # Correct signature (1pt)
        try:
            sig = inspect.signature(sync_function)
            expected_params = ["user_data", "api_token"]
            actual_params = list(sig.parameters.keys())

            if actual_params == expected_params:
                structure_scoring.add_check(
                    "correct_signature",
                    True,
                    1.0,
                    "Correct signature: sync_users_to_crm(user_data, api_token)",
                )
            else:
                structure_scoring.add_check(
                    "correct_signature",
                    False,
                    0,
                    f"Wrong signature: expected {expected_params}, got {actual_params}",
                )

        except Exception as e:
            structure_scoring.add_check(
                "signature_check", False, 0, f"Signature inspection failed: {e}"
            )

        # HTTP request structure analysis (2pts)
        try:
            with open(api_file, encoding="utf-8") as f:
                code = f.read()

            # Check for proper request formation patterns
            has_post_call = any(pattern in code.lower() for pattern in ["requests.post", ".post("])
            has_json_payload = "json=" in code.lower() or '"users"' in code
            has_headers = "headers" in code.lower() and (
                "authorization" in code.lower() or "bearer" in code.lower()
            )

            structure_points = 0
            if has_post_call:
                structure_points += 0.7
            if has_json_payload:
                structure_points += 0.7
            if has_headers:
                structure_points += 0.6

            structure_scoring.add_check(
                "request_structure",
                structure_points > 1.5,
                structure_points,
                (
                    f"Request structure: POST={'✓' if has_post_call else '✗'}, "
                    f"JSON={'✓' if has_json_payload else '✗'}, "
                    f"Headers={'✓' if has_headers else '✗'}"
                ),
            )

        except Exception as e:
            structure_scoring.add_check(
                "structure_analysis", False, 0, f"Structure analysis failed: {e}"
            )

        # Category 3: Execution - REVOLUTIONARY: Actual behavioral testing with mocks
        test_user_data = [{"id": 1, "name": "Test User"}]  # Simple test data
        test_token = "test_token_12345"

        # Monkeypatch requests.post for behavioral testing
        with patch("requests.post") as mock_post:
            # Test 1: Success case - 200 with job_id (2pts)
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"job_id": "abc123"}
            mock_post.return_value = mock_response_200

            try:
                result_success = sync_function(test_user_data, test_token)

                # Verify function returns job_id
                if result_success == "abc123" or (
                    isinstance(result_success, dict) and result_success.get("job_id") == "abc123"
                ):
                    execution_scoring.add_check(
                        "success_handling", True, 2.0, "Returns job_id on 200 success"
                    )
                else:
                    execution_scoring.add_check(
                        "success_handling", False, 0, f"Wrong return on success: {result_success}"
                    )

            except Exception as e:
                execution_scoring.add_check(
                    "success_handling", False, 0, f"Failed on 200 response: {e}"
                )

            # Test 2: 400 Bad Request handling (1pt)
            mock_response_400 = Mock()
            mock_response_400.status_code = 400
            mock_response_400.json.return_value = {"error": "Bad request"}
            mock_post.return_value = mock_response_400

            try:
                _ = sync_function(test_user_data, test_token)
                # Function should handle 400 gracefully (return error indication
                # or raise appropriate exception). Don't require specific behavior,
                # just that it doesn't crash
                execution_scoring.add_check(
                    "handle_400", True, 1.0, "Handles 400 Bad Request appropriately"
                )
            except requests.exceptions.HTTPError:
                # Acceptable to raise HTTPError for 400
                execution_scoring.add_check(
                    "handle_400", True, 1.0, "Raises HTTPError for 400 (acceptable)"
                )
            except Exception as e:
                execution_scoring.add_check("handle_400", False, 0, f"Crashes on 400: {e}")

            # Test 3: 401 Unauthorized handling (1pt)
            mock_response_401 = Mock()
            mock_response_401.status_code = 401
            mock_response_401.json.return_value = {"error": "Unauthorized"}
            mock_post.return_value = mock_response_401

            try:
                _ = sync_function(test_user_data, test_token)
                execution_scoring.add_check(
                    "handle_401", True, 1.0, "Handles 401 Unauthorized appropriately"
                )
            except requests.exceptions.HTTPError:
                execution_scoring.add_check(
                    "handle_401", True, 1.0, "Raises HTTPError for 401 (acceptable)"
                )
            except Exception as e:
                execution_scoring.add_check("handle_401", False, 0, f"Crashes on 401: {e}")

            # Test 4: 503 Service Unavailable handling (1pt)
            mock_response_503 = Mock()
            mock_response_503.status_code = 503
            mock_response_503.headers = {"Retry-After": "60"}
            mock_response_503.json.return_value = {"error": "Service unavailable"}
            mock_post.return_value = mock_response_503

            try:
                _ = sync_function(test_user_data, test_token)
                execution_scoring.add_check(
                    "handle_503", True, 1.0, "Handles 503 Service Unavailable appropriately"
                )
            except requests.exceptions.HTTPError:
                execution_scoring.add_check(
                    "handle_503", True, 1.0, "Raises HTTPError for 503 (acceptable)"
                )
            except Exception as e:
                execution_scoring.add_check("handle_503", False, 0, f"Crashes on 503: {e}")

            # Test 5: ConnectionError handling (1pt)
            mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

            try:
                _ = sync_function(test_user_data, test_token)
                execution_scoring.add_check(
                    "handle_connection_error", True, 1.0, "Handles ConnectionError appropriately"
                )
            except requests.exceptions.ConnectionError:
                execution_scoring.add_check(
                    "handle_connection_error", True, 1.0, "Propagates ConnectionError (acceptable)"
                )
            except Exception as e:
                execution_scoring.add_check(
                    "handle_connection_error", False, 0, f"Crashes on ConnectionError: {e}"
                )

            # Test 6: JSON parsing correctness (1pt)
            # Reset mock for success case and verify JSON handling
            mock_post.side_effect = None
            mock_response_json = Mock()
            mock_response_json.status_code = 200
            mock_response_json.json.return_value = {"job_id": "test123", "status": "queued"}
            mock_post.return_value = mock_response_json

            try:
                result_json = sync_function(test_user_data, test_token)
                # Check if function properly extracts job_id from JSON response
                if "test123" in str(result_json):
                    execution_scoring.add_check(
                        "json_parsing", True, 1.0, "Correctly parses JSON and extracts job_id"
                    )
                else:
                    execution_scoring.add_check("json_parsing", False, 0.5, "Partial JSON handling")
            except Exception as e:
                execution_scoring.add_check("json_parsing", False, 0, f"JSON parsing failed: {e}")

            # Category 4: Quality - Error messages and documentation
            try:
                with open(api_file, encoding="utf-8") as f:
                    code = f.read()

                # Informative error messages (2pts)
                has_informative_errors = any(
                    status in code for status in ["400", "401", "503"]
                ) and ("print(" in code or "logging." in code or "raise" in code)
                error_score = (
                    2.0
                    if has_informative_errors
                    else 1.0
                    if any(status in code for status in ["400", "401", "503"])
                    else 0
                )

                quality_scoring.add_check(
                    "informative_errors",
                    error_score >= 2.0,
                    error_score,
                    "Has informative error messages for different cases"
                    if error_score >= 2.0
                    else "Basic error handling present",
                )

                # Documentation or type hints (1pt)
                has_docstring = '"""' in code or "'''" in code
                has_type_hints = "->" in code or ": str" in code or ": dict" in code
                doc_score = 1.0 if (has_docstring or has_type_hints) else 0

                quality_scoring.add_check(
                    "documentation",
                    doc_score > 0,
                    doc_score,
                    "Has docstring or type hints" if doc_score > 0 else "Missing documentation",
                )

            except Exception as e:
                quality_scoring.add_check(
                    "quality_analysis", False, 0, f"Quality analysis failed: {e}"
                )

            # Category 5: Security - API security practices (HIGHEST WEIGHT)

            # Get the last mock call to analyze headers and security
            call_args = mock_post.call_args_list[-1] if mock_post.call_args_list else None

            if call_args:
                args, kwargs = call_args

                # Test 1: Proper Bearer token in Authorization header (3pts)
                headers = kwargs.get("headers", {})
                auth_header = headers.get("Authorization", "")

                if auth_header.startswith("Bearer ") and test_token in auth_header:
                    security_scoring.add_check(
                        "bearer_auth", True, 3.0, "Correct Bearer token in Authorization header"
                    )
                elif "Authorization" in headers:
                    security_scoring.add_check(
                        "bearer_auth", False, 1.0, "Has Authorization header but format incorrect"
                    )
                else:
                    security_scoring.add_check(
                        "bearer_auth", False, 0, "Missing Authorization header"
                    )

                # Test 2: No token leakage (2pts) - Check token not in URL or body
                url = args[0] if args else kwargs.get("url", "")
                json_data = kwargs.get("json", {})
                data = kwargs.get("data", "")

                token_in_url = test_token in str(url)
                token_in_body = test_token in str(json_data) or test_token in str(data)

                if not (token_in_url or token_in_body):
                    security_scoring.add_check(
                        "no_token_leak", True, 2.0, "Token not leaked in URL or body"
                    )
                else:
                    leaks = []
                    if token_in_url:
                        leaks.append("URL")
                    if token_in_body:
                        leaks.append("body")
                    security_scoring.add_check(
                        "no_token_leak", False, 0, f"Token leaked in: {', '.join(leaks)}"
                    )

                # Test 3: Explicit timeouts (2pts) - GPT requirement
                has_timeout = "timeout" in kwargs and isinstance(kwargs["timeout"], int | float)

                if has_timeout:
                    security_scoring.add_check(
                        "explicit_timeout", True, 2.0, f"Explicit timeout: {kwargs['timeout']}s"
                    )
                else:
                    security_scoring.add_check(
                        "explicit_timeout", False, 0, "Missing explicit timeout (security risk)"
                    )

            else:
                security_scoring.add_check(
                    "security_analysis", False, 0, "No API calls captured for security analysis"
                )

            # Additional security check: No hardcoded credentials in source
            try:
                with open(api_file, encoding="utf-8") as f:
                    code = f.read()

                # Look for suspicious hardcoded tokens/keys
                suspicious_patterns = [
                    r'token\s*=\s*["\'][a-zA-Z0-9_-]{10,}["\']',  # token = "hardcoded_value"
                    r'api_key\s*=\s*["\'][a-zA-Z0-9_-]{10,}["\']',  # api_key = "hardcoded_value"
                    r"Bearer\s+[a-zA-Z0-9_-]{10,}",  # Bearer hardcoded_token
                ]

                hardcoded_found = any(
                    re.search(pattern, code, re.IGNORECASE) for pattern in suspicious_patterns
                )

                if not hardcoded_found:
                    # This is a bonus check, don't penalize if we can't detect
                    pass  # Covered by token source validation above
                else:
                    security_scoring.add_check(
                        "no_hardcoded_creds", False, 0, "Possible hardcoded credentials detected"
                    )
                    security_scoring.earned_points = max(0.0, security_scoring.earned_points - 1.0)

            except Exception as e:
                # Record as a zero-point detail so we preserve behavior and improve diagnosability
                security_scoring.add_check(
                    "security_validator_exception", False, 0, f"{type(e).__name__}: {e}"
                )
                pass  # Security checks are best effort

            # Category 6: Performance - Retry logic and network efficiency
            try:
                with open(api_file, encoding="utf-8") as f:
                    code = f.read()

                # Check for retry/backoff patterns (2pts)
                retry_patterns = [
                    "retry",
                    "backoff",
                    "sleep",
                    "time.sleep",
                    "Retry-After",
                    "retries",
                    "max_retries",
                ]

                has_retry_logic = any(pattern.lower() in code.lower() for pattern in retry_patterns)

                # Check for requests.Session or requests.adapters usage (more sophisticated)
                has_session = "Session()" in code or "requests.Session" in code
                has_retry_adapter = "Retry" in code and "adapter" in code.lower()

                retry_score = 0
                if has_retry_adapter or has_session:
                    retry_score = 2.0  # Sophisticated retry
                elif has_retry_logic:
                    retry_score = 1.0  # Basic retry

                # Determine resilience level for better readability
                resilience_level = (
                    "Advanced" if retry_score >= 2.0
                    else "Basic" if retry_score > 0
                    else "None"
                )
                performance_scoring.add_check(
                    "retry_resilience",
                    retry_score > 0,
                    retry_score,
                    f"Network resilience: {resilience_level}",
                )

            except Exception as e:
                performance_scoring.add_check(
                    "performance_analysis", False, 0, f"Performance analysis failed: {e}"
                )

            # Category 7: Maintainability - Basic code organization
            try:
                with open(api_file, encoding="utf-8") as f:
                    code = f.read()

                # Simple readability checks
                has_clear_flow = code.count("\n") > 10  # Not all on one line
                has_meaningful_names = any(
                    name in code for name in ["response", "headers", "payload", "data"]
                )

                maintainability_score = (
                    1.0
                    if (has_clear_flow and has_meaningful_names)
                    else 0.5
                    if has_clear_flow
                    else 0
                )

                maintainability_scoring.add_check(
                    "code_organization",
                    maintainability_score > 0.8,
                    maintainability_score,
                    "Clear, readable code organization"
                    if maintainability_score >= 1.0
                    else "Basic organization",
                )

            except Exception as e:
                maintainability_scoring.add_check(
                    "maintainability_check", False, 0, f"Maintainability analysis failed: {e}"
                )

            # Reset any mock side effects for clean state
            mock_post.side_effect = None

        # Aggregate all scores
        categories = [
            ("syntax", syntax_scoring),
            ("structure", structure_scoring),
            ("execution", execution_scoring),  # BEHAVIORAL TESTING
            ("quality", quality_scoring),
            ("security", security_scoring),  # HIGHEST WEIGHT
            ("performance", performance_scoring),
            ("maintainability", maintainability_scoring),
        ]

        total_score = 0
        for category_name, scoring in categories:
            category_score = scoring.earned_points
            total_score += category_score

            result["detailed_scoring"][category_name]["earned"] = category_score
            result["feedback"].append(scoring.get_feedback_line(category_name.title()))

        # Legacy test flags for backward compatibility
        result["tests_passed"]["function_signature"] = syntax_scoring.earned_points >= 1.0
        result["tests_passed"]["uses_requests"] = any(
            c["name"] == "request_structure" and c["passed"] for c in structure_scoring.checks
        )
        result["tests_passed"]["error_handling"] = (
            execution_scoring.earned_points >= 4.0
        )  # Most error scenarios handled
        result["tests_passed"]["api_structure"] = structure_scoring.earned_points >= 2.0

        result["score"] = total_score
        result["passed"] = result["score"] >= 15  # 60% threshold

        return result
