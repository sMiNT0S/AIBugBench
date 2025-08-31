#!/usr/bin/env python3
"""
Security validation script for AIBugBench.
Validates security configurations and runs local security scans.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


def run_command(cmd: list[str], capture_output: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def check_security_files() -> dict[str, bool]:
    """Check if security configuration files exist."""
    security_files = {
        ".github/dependabot.yml": "Dependabot configuration",
        ".github/workflows/security.yml": "Security workflow",
        ".github/workflows/security-audit.yml": "SAFETY2.0 security audit workflow",
        ".github/codeql/codeql-config.yml": "CodeQL configuration",
        ".trufflehogignore": "TruffleHog ignore patterns",
        ".semgrepignore": "Semgrep ignore patterns",
        ".safety-project.ini": "Safety configuration",
        ".github/secret-patterns.yml": "Custom secret patterns",
        "docs/security.md": "Security documentation"
    }

    project_root = Path(__file__).parent.parent
    results = {}

    print("Checking security configuration files...")
    for file_path, description in security_files.items():
        full_path = project_root / file_path
        exists = full_path.exists()
        results[file_path] = exists
        status = "[OK]" if exists else "[MISSING]"
        print(f"  {status} {description}: {file_path}")

    return results


def run_ruff_security_check() -> bool:
    """Run Ruff security linting."""
    print("\nRunning Ruff security analysis...")
    exit_code, stdout, stderr = run_command(["ruff", "check", ".", "--select=S", "--format=json"])

    if exit_code == 127:  # Command not found
        print("  [WARNING] Ruff not installed, skipping security linting")
        return True
    try:
        if stdout.strip():
            results = json.loads(stdout)
            security_issues = [r for r in results if r.get("code", "").startswith("S")]

            if security_issues:
                print(f"  [WARNING] Found {len(security_issues)} security issues:")
                for issue in security_issues[:5]:  # Show first 5
                    code = issue.get('code', 'Unknown')
                    message = issue.get('message', 'No message')
                    filename = issue.get('filename', 'Unknown')
                    row = issue.get('location', {}).get('row', '?')
                    print(f"     {code}: {message}")
                    print(f"     File: {filename}:{row}")
                if len(security_issues) > 5:
                    print(f"     ... and {len(security_issues) - 5} more")
                return False
            else:
                print("  [OK] No security issues found")
                return True
        else:
            print("  [OK] No security issues found")
            return True
    except json.JSONDecodeError:
        print("  [ERROR] Failed to parse Ruff output")
        return False


def run_safety_check() -> bool:
    """Run Safety dependency vulnerability scan."""
    print("\nRunning Safety dependency scan...")
    exit_code, stdout, stderr = run_command(["safety", "check", "--json"])

    if exit_code == 127:  # Command not found
        print("  [WARNING] Safety not installed, install with: pip install safety")
        return True
    if exit_code == 0:
        print("  [OK] No known vulnerabilities found in dependencies")
        return True
    else:
        try:
            if stdout.strip():
                results = json.loads(stdout)
                vulns = results.get("vulnerabilities", [])
                if vulns:
                    print(f"  [WARNING] Found {len(vulns)} vulnerabilities:")
                    for vuln in vulns[:3]:  # Show first 3
                        pkg_name = vuln.get('package_name', 'Unknown')
                        vuln_id = vuln.get('vulnerability_id', 'Unknown')
                        advisory = vuln.get('advisory', 'No advisory')
                        print(f"     {pkg_name}: {vuln_id}")
                        print(f"     {advisory}")
                    if len(vulns) > 3:
                        print(f"     ... and {len(vulns) - 3} more")
                    return False
                else:
                    print("  [OK] No known vulnerabilities found in dependencies")
                    return True
            else:
                print("  [OK] No known vulnerabilities found in dependencies")
                return True
        except json.JSONDecodeError:
            print(f"  [ERROR] Safety check failed: {stderr}")
            return False


def check_git_history_safety() -> bool:
    """Basic check for obvious secrets in recent commits."""
    print("\nChecking recent git history for obvious secrets...")

    # Get recent commit messages and diffs
    exit_code, stdout, stderr = run_command([
        "git", "log", "--oneline", "-10", "--no-merges"
    ])

    if exit_code != 0:
        print("  [WARNING] Failed to access git history")
        return True

    # Look for obvious secret patterns in commit messages
    secret_patterns = [
        "password", "secret", "key", "token", "api_key",
        "private_key", "credentials", "auth"
    ]

    issues_found = []
    for line in stdout.split('\n'):
        line_lower = line.lower()
        for pattern in secret_patterns:
            if pattern in line_lower and "test" not in line_lower and "dummy" not in line_lower:
                issues_found.append(f"Commit message contains '{pattern}': {line}")

    if issues_found:
        print(f"  [WARNING] Found {len(issues_found)} potential issues in commit messages:")
        for issue in issues_found[:3]:
            print(f"     {issue}")
        return False
    else:
        print("  [OK] No obvious secrets found in recent commit messages")
        return True


def validate_test_data_safety() -> bool:
    """Validate that test data doesn't contain real secrets."""
    print("\nValidating test data safety...")

    test_data_path = Path(__file__).parent.parent / "test_data"
    if not test_data_path.exists():
        print("  [WARNING] Test data directory not found")
        return True

    # Check for suspicious patterns in test files
    suspicious_patterns = [
        "sk-[a-zA-Z0-9]{48}",  # OpenAI key pattern
        "AKIA[0-9A-Z]{16}",    # AWS access key pattern
        "sk-ant-[a-zA-Z0-9\\-_]{95}",  # Anthropic key pattern
    ]

    issues = []
    for file_path in test_data_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.py', '.json', '.yaml', '.yml']:
            try:
                content = file_path.read_text(encoding='utf-8')
                for pattern in suspicious_patterns:
                    if re.search(pattern, content):
                        # Check if it's a known dummy pattern
                        dummy_keywords = ["dummy", "test", "fake", "placeholder"]
                        if not any(dummy in content for dummy in dummy_keywords):
                            issues.append(f"Suspicious pattern in {file_path}: {pattern}")
            except Exception as e:
                print(f"  [WARNING] Could not read {file_path}: {e}")

    if issues:
        print(f"  [WARNING] Found {len(issues)} potential real secrets in test data:")
        for issue in issues:
            print(f"     {issue}")
        return False
    else:
        print("  [OK] Test data appears safe (contains only dummy values)")
        return True


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate AIBugBench security infrastructure")
    parser.add_argument(
        "--check-files", action="store_true", help="Check security configuration files"
    )
    parser.add_argument("--run-scans", action="store_true", help="Run local security scans")
    parser.add_argument("--all", action="store_true", help="Run all security validations")
    parser.add_argument(
        "--list-checks", action="store_true", help="List available scan checks and exit"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which checks would run without executing them",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout")
    parser.add_argument("--json-file", type=str, help="Path to write JSON summary (implies --json)")

    args = parser.parse_args()

    if args.json_file:
        args.json = True

    if args.list_checks:
        checks = ["config_files", "ruff_security", "safety", "git_history", "test_data"]
        if args.json:
            payload = {"available_checks": checks}
            if args.json_file:
                Path(args.json_file).write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(json.dumps(payload, indent=2))
        else:
            print("Available checks:")
            for c in checks:
                print(f" - {c}")
        return

    if not any([args.check_files, args.run_scans, args.all, args.dry_run]):
        args.all = True  # Default to running everything (unless dry-run/list invoked)

    print("AIBugBench Security Validation")
    print("=" * 40)

    all_passed = True

    executed = []
    # Check security configuration files
    if args.check_files or args.all:
        file_results = check_security_files()
        missing_files = [f for f, exists in file_results.items() if not exists]
        if missing_files:
            print(f"\n[ERROR] {len(missing_files)} security configuration files are missing")
            all_passed = False
        else:
            print("\n[OK] All security configuration files are present")
        executed.append("config_files")

    # Run security scans
    if args.run_scans or args.all:
        scan_results = []
        if args.dry_run:
            print("\nDry run: would execute ruff security, safety, git history, test data scans")
        else:
            scan_results.append(run_ruff_security_check())
            executed.append("ruff_security")
            scan_results.append(run_safety_check())
            executed.append("safety")
            scan_results.append(check_git_history_safety())
            executed.append("git_history")
            scan_results.append(validate_test_data_safety())
            executed.append("test_data")

        failed_scans = sum(1 for result in scan_results if not result)
        if not args.dry_run and failed_scans > 0:
            print(f"\n[ERROR] {failed_scans} security scans found issues")
            all_passed = False
        elif not args.dry_run:
            print("\n[OK] All security scans passed")

    if args.json:
        summary_payload = {
            "executed": executed,
            "all_passed": all_passed,
        }
        if args.json_file:
            Path(args.json_file).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
        print(json.dumps(summary_payload, indent=2))

    # Final summary
    print("\n" + "=" * 40)
    if all_passed or args.dry_run:
        print("SUCCESS: Security validation completed successfully!")
        print("Next steps:")
        print("   - Run GitHub Actions security workflow")
        print("   - Monitor Dependabot alerts")
        print("   - Review CodeQL results in Security tab")
        sys.exit(0)
    else:
        print("WARNING: Security validation found issues that need attention")
        print("Recommended actions:")
        print("   - Review and fix security issues identified above")
        print("   - Ensure all security configuration files are present")
        print("   - Check Security Infrastructure documentation")
        sys.exit(1)


if __name__ == "__main__":
    main()
