#!/usr/bin/env python3
"""
Documentation Validation Script for AIBugBench

This script automatically validates all documented commands across the AIBugBench project
to ensure they work correctly on different platforms.

Features:
- Scans all documentation files for command blocks
- Extracts commands by platform (Windows CMD, PowerShell, macOS/Linux)
- Runs commands in safe sandboxed environments
- Validates expected vs actual outputs
- Reports any inconsistencies or failures
- Cross-platform compatibility testing

Usage:
    python scripts/validate_docs.py [--verbose] [--docs-only] [--skip-destructive]
                                    [--allow-network] [--platform PLATFORM] [--no-sandbox-safe]

Safety Features:
- Network commands are skipped by default (use --allow-network to enable)
- SAFE commands are sandboxed by default for defense-in-depth
- Platform override available for testing specific environments
"""

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import os
from pathlib import Path
import platform as platform_module
import re
import shutil
import subprocess
import sys
import tempfile
import time

# New internal module import (extracted core parsing helpers)
try:  # pragma: no cover - fallback if package not present
    from validation.docs_core import Platform as CorePlatform  # type: ignore
except Exception:  # pragma: no cover
    CorePlatform = None  # type: ignore


class Platform(Enum):
    """Supported platform types for command execution."""

    WINDOWS_CMD = "windows_cmd"
    WINDOWS_POWERSHELL = "windows_powershell"
    MACOS_LINUX = "macos_linux"


class CommandType(Enum):
    """Types of commands for safety classification."""

    SAFE = "safe"  # Read-only, non-destructive commands
    SANDBOX = "sandbox"  # Commands that modify files but can be sandboxed
    DESTRUCTIVE = "destructive"  # Commands that could damage the system
    NETWORK = "network"  # Commands that access network resources


@dataclass
class Command:
    """Represents a command extracted from documentation."""

    content: str
    platform: Platform
    file_path: str
    line_number: int
    command_type: CommandType = CommandType.SAFE
    expected_output: str | None = None
    context: str = ""

    def __post_init__(self):
        """Classify command type based on content."""
        self.command_type = self._classify_command()

    def _classify_command(self) -> CommandType:
        """Classify command safety level."""
        content_lower = self.content.lower()

        # Destructive commands - never run these
        destructive_patterns = [
            r"\brm\s+-rf\s+/",
            r"\bdel\s+/s\s+/q",
            r"\bformat\s+",
            r"\bfdisk\s+",
            r"\bmkfs\.",
            r"\bdd\s+if=",
            r"\bshutdown\s+",
            r"\breboot\s+",
            r"\bkillall\s+",
            r"\btaskill\s+/f",
        ]

        for pattern in destructive_patterns:
            if re.search(pattern, content_lower):
                return CommandType.DESTRUCTIVE

        # Network commands
        network_patterns = [
            r"\bcurl\s+",
            r"\bwget\s+",
            r"\bgit\s+clone\s+https?://",
            r"\bping\s+",
            r"\bnslookup\s+",
        ]

        for pattern in network_patterns:
            if re.search(pattern, content_lower):
                return CommandType.NETWORK

        # Sandbox commands - file system modifications that can be isolated
        sandbox_patterns = [
            r"\bmkdir\s+",
            r"\btouch\s+",
            r"\becho\s+.*>\s*",
            r"\bcp\s+",
            r"\bcopy\s+",
            r"\bxcopy\s+",
            r"\bmv\s+",
            r"\bmove\s+",
            r"\brm\s+[^-]",  # rm without dangerous flags
            r"\bdel\s+[^/]",  # del without dangerous flags
            r"\bpython\s+setup\.py",
            r"\bpip\s+install",
            r"\bpython\s+.*\.py",
        ]

        for pattern in sandbox_patterns:
            if re.search(pattern, content_lower):
                return CommandType.SANDBOX

        return CommandType.SAFE


@dataclass
class ValidationResult:
    """Results from validating a command."""

    command: Command
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    error_message: str = ""
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class ValidationSummary:
    """Summary of all validation results."""

    total_commands: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    platform_counts: dict[Platform, int] = field(default_factory=dict)
    type_counts: dict[CommandType, int] = field(default_factory=dict)
    results: list[ValidationResult] = field(default_factory=list)


class DocumentationValidator:
    """Main class for validating documentation commands."""

    def __init__(
        self,
        project_root: Path,
        verbose: bool = False,
        skip_destructive: bool = True,
        allow_network: bool = False,
        platform_override: str | None = None,
        sandbox_safe_commands: bool = True,
    ):
        self.project_root = project_root
        self.verbose = verbose
        self.skip_destructive = skip_destructive
        self.allow_network = allow_network
        self.platform_override = platform_override
        self.sandbox_safe_commands = sandbox_safe_commands

        # Set up logging first
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

        # Now detect platform (which may need to log warnings)
        self.current_platform = self._detect_platform()

        # Documentation files to scan
        self.doc_files = [
            "README.md",
            "QUICKSTART.md",
            "EXAMPLE_SUBMISSION.md",
            "docs/adding_models.md",
            "docs/interpreting_results.md",
            "docs/scoring_rubric.md",
            # Updated canonical template path (legacy submissions/template removed)
            "submissions/templates/template/README.md",
        ]

        # Command block patterns for different platforms
        self.command_patterns = {
            Platform.WINDOWS_CMD: [
                (r"```cmd\s*\n(.*?)\n```", re.DOTALL),
                (r"```batch\s*\n(.*?)\n```", re.DOTALL),
            ],
            Platform.WINDOWS_POWERSHELL: [
                (r"```powershell\s*\n(.*?)\n```", re.DOTALL),
                (r"```ps1\s*\n(.*?)\n```", re.DOTALL),
            ],
            Platform.MACOS_LINUX: [
                (r"```bash\s*\n(.*?)\n```", re.DOTALL),
                (r"```sh\s*\n(.*?)\n```", re.DOTALL),
                (r"```shell\s*\n(.*?)\n```", re.DOTALL),
            ],
        }

        # Expected output patterns
        self.output_pattern = r"```\s*\n(.*?)\n```"

    def _detect_platform(self) -> Platform:
        """Detect the current platform."""
        # Use platform override if provided
        if self.platform_override:
            platform_map = {
                "windows_cmd": Platform.WINDOWS_CMD,
                "windows_powershell": Platform.WINDOWS_POWERSHELL,
                "macos_linux": Platform.MACOS_LINUX,
            }
            override_lower = self.platform_override.lower()
            if override_lower in platform_map:
                return platform_map[override_lower]
            else:
                self.logger.warning(
                    f"Unknown platform override '{self.platform_override}', using auto-detection"
                )

        # Auto-detect platform
        system = platform_module.system().lower()
        if system == "windows":
            # For Windows, default to CMD but could be extended to detect PowerShell
            return Platform.WINDOWS_CMD
        else:
            return Platform.MACOS_LINUX

    def scan_documentation(self) -> list[Command]:
        """Scan all documentation files for commands."""
        commands = []

        for doc_file in self.doc_files:
            file_path = self.project_root / doc_file
            if not file_path.exists():
                self.logger.warning(f"Documentation file not found: {file_path}")
                continue

            self.logger.info(f"Scanning {doc_file}...")
            file_commands = self._extract_commands_from_file(file_path)
            commands.extend(file_commands)
            self.logger.debug(f"Found {len(file_commands)} commands in {doc_file}")

        self.logger.info(f"Total commands found: {len(commands)}")
        return commands

    def _extract_commands_from_file(self, file_path: Path) -> list[Command]:
        """Extract commands from a single documentation file."""
        commands = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            return commands

        lines = content.split("\n")

        # Extract commands for each platform
        for platform, patterns in self.command_patterns.items():
            for pattern, flags in patterns:
                matches = re.finditer(pattern, content, flags)

                for match in matches:
                    command_block = match.group(1).strip()
                    if not command_block:
                        continue

                    # Find line number for context
                    line_num = content[: match.start()].count("\n") + 1

                    # Split command block into individual commands
                    individual_commands = self._split_command_block(command_block)

                    for i, cmd in enumerate(individual_commands):
                        if cmd.strip():
                            # Look for expected output after the command block
                            expected_output = self._find_expected_output(content, match.end())

                            command = Command(
                                content=cmd.strip(),
                                platform=platform,
                                file_path=str(file_path),
                                line_number=line_num + i,
                                expected_output=expected_output,
                                context=self._get_context(lines, line_num, 3),
                            )
                            commands.append(command)

        return commands

    def _split_command_block(self, command_block: str) -> list[str]:
        """Split a command block into individual commands."""
        commands = []

        # Handle different command separators
        lines = command_block.split("\n")
        current_command = []

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Skip lines that look like markdown formatting or explanations
            if (
                line.startswith("**")
                or (line.startswith("*") and not line.startswith("* "))
                or line.startswith(">")
                or (line.startswith("-") and not line.startswith("- "))
                or line.startswith("```")
                or line.startswith("For ")
                or line.startswith("All ")
                or line.startswith("This ")
                or line.startswith("The ")
                or "(CMD)" in line
                or "(PowerShell)" in line
                or "(Bash)" in line
            ):
                continue

            # Check if this is a continuation line
            if line.endswith("\\"):
                current_command.append(line[:-1].strip())
                continue

            current_command.append(line)

            # Join and add the complete command
            if current_command:
                full_command = " ".join(current_command).strip()
                if full_command and self._looks_like_command(full_command):
                    commands.append(full_command)
                current_command = []

        # Handle any remaining command
        if current_command:
            full_command = " ".join(current_command).strip()
            if full_command and self._looks_like_command(full_command):
                commands.append(full_command)

        return commands

    def _looks_like_command(self, text: str) -> bool:
        """Check if text looks like an actual command."""
        # Skip if it's too short or too long to be a reasonable command
        if len(text) < 2 or len(text) > 500:
            return False

        # Skip if it contains markdown or formatting characters
        if (
            "**" in text
            or text.count("`") > 0
            or text.startswith("Note:")
            or text.startswith("Tip:")
            or text.startswith("Example:")
            or text.startswith("Important:")
        ):
            return False

        # Skip descriptive text
        descriptive_starters = [
            "for",
            "this",
            "the",
            "all",
            "ensure",
            "make sure",
            "you can",
            "you should",
            "it will",
            "here is",
            "as you can see",
            "note that",
            "remember that",
        ]

        text_lower = text.lower()
        for starter in descriptive_starters:
            if text_lower.startswith(starter + " "):
                return False

        # Must contain at least one typical command pattern
        command_patterns = [
            r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9]+)*\s+",  # executable_name args
            r"^(cd|ls|dir|echo|cat|mkdir|cp|mv|rm|del|copy|move|xcopy)\s+",  # common commands
            r"^(python|node|npm|git|pip|docker)\s+",  # common tools
            r"^[a-zA-Z]:.*",  # Windows path
            r"^[./~].*",  # Unix path
        ]

        return any(re.match(pattern, text, re.IGNORECASE) for pattern in command_patterns)

    def _find_expected_output(self, content: str, start_pos: int) -> str | None:
        """Find expected output after a command block."""
        # Look for the next code block that might be output
        remaining_content = content[start_pos:]

        # Look for "Expected Output" or similar text followed by a code block
        output_intro_pattern = r"(?i)\*\*expected\s+output\*\*.*?\n"
        match = re.search(output_intro_pattern, remaining_content)

        if match:
            # Look for the next code block
            code_block_start = match.end()
            remaining_after_intro = remaining_content[code_block_start:]

            output_match = re.search(self.output_pattern, remaining_after_intro, re.DOTALL)
            if output_match:
                return output_match.group(1).strip()

        return None

    def _get_context(self, lines: list[str], line_num: int, context_lines: int) -> str:
        """Get context around a line number."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)

        context_block = [
            f"{'>>> ' if i == line_num - 1 else '    '}{lines[i]}" for i in range(start, end)
        ]

        return "\n".join(context_block)

    def validate_commands(self, commands: list[Command]) -> ValidationSummary:
        """Validate all extracted commands."""
        summary = ValidationSummary()
        summary.total_commands = len(commands)

        # Initialize counters
        for platform in Platform:
            summary.platform_counts[platform] = 0
        for cmd_type in CommandType:
            summary.type_counts[cmd_type] = 0

        for command in commands:
            # Update counters
            summary.platform_counts[command.platform] += 1
            summary.type_counts[command.command_type] += 1

            # Validate the command
            result = self._validate_single_command(command)
            summary.results.append(result)

            if result.skipped:
                summary.skipped += 1
            elif result.success:
                summary.successful += 1
            else:
                summary.failed += 1

            # Progress reporting
            if self.verbose:
                status = "SKIP" if result.skipped else ("PASS" if result.success else "FAIL")
                self.logger.info(f"[{status}] {command.content[:60]}...")

        return summary

    def _validate_single_command(self, command: Command) -> ValidationResult:
        """Validate a single command."""
        result = ValidationResult(command=command, success=False)

        # Check if we should skip this command
        skip_reason = self._should_skip_command(command)
        if skip_reason:
            result.skipped = True
            result.skip_reason = skip_reason
            return result

        # Create sandbox environment if needed
        sandbox_dir = None
        original_cwd = os.getcwd()

        try:
            # Create sandbox for SANDBOX commands and optionally for SAFE commands
            if command.command_type == CommandType.SANDBOX or (
                command.command_type == CommandType.SAFE and self.sandbox_safe_commands
            ):
                sandbox_dir = self._create_sandbox()
                os.chdir(sandbox_dir)
                self.logger.debug(
                    f"Created sandbox for {command.command_type.value} command: {sandbox_dir}"
                )

            # Execute the command
            start_time = time.time()
            result.return_code, result.stdout, result.stderr = self._execute_command(command)
            result.execution_time = time.time() - start_time

            # Check if command was successful
            result.success = result.return_code == 0

            if not result.success:
                result.error_message = f"Command failed with return code {result.return_code}"
                if result.stderr:
                    result.error_message += f": {result.stderr}"

            # Validate expected output if provided
            if command.expected_output and result.success:
                output_match = self._validate_output(result.stdout, command.expected_output)
                if not output_match:
                    result.success = False
                    result.error_message = "Output does not match expected result"

        except Exception as e:
            result.error_message = f"Exception during execution: {e!s}"
            self.logger.error(f"Error executing command '{command.content}': {e}")

        finally:
            # Cleanup
            os.chdir(original_cwd)
            if sandbox_dir and os.path.exists(sandbox_dir):
                try:
                    shutil.rmtree(sandbox_dir)
                    self.logger.debug(f"Cleaned up sandbox: {sandbox_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup sandbox {sandbox_dir}: {e}")

        return result

    def _should_skip_command(self, command: Command) -> str | None:
        """Determine if a command should be skipped."""
        # Skip destructive commands if requested
        if self.skip_destructive and command.command_type == CommandType.DESTRUCTIVE:
            return "Destructive command skipped for safety"

        # Skip commands for different platforms
        if command.platform != self.current_platform:
            return f"Platform mismatch: {command.platform.value} vs {self.current_platform.value}"

        # Skip network commands unless explicitly allowed
        if command.command_type == CommandType.NETWORK and not self.allow_network:
            return "Network command skipped for safety (use --allow-network to enable)"

        # Skip commands that require specific tools
        required_tools = self._get_required_tools(command)
        for tool in required_tools:
            if not self._check_tool_available(tool):
                return f"Required tool not available: {tool}"

        return None

    def _get_required_tools(self, command: Command) -> list[str]:
        """Get list of tools required by a command."""
        tools = []
        content_lower = command.content.lower()

        # Common tools
        tool_patterns = {
            "git": r"\bgit\s+",
            "python": r"\bpython\d*\s+",
            "pip": r"\bpip\d*\s+",
            "node": r"\bnode\s+",
            "npm": r"\bnpm\s+",
            "docker": r"\bdocker\s+",
        }

        for tool, pattern in tool_patterns.items():
            if re.search(pattern, content_lower):
                tools.append(tool)

        return tools

    def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available on the system."""
        try:
            # Try to run the tool with a version or help flag
            if tool == "python":
                # Try both python and python3
                for py_cmd in ["python", "python3", "py"]:
                    try:
                        subprocess.run(  # noqa: S603  # Tool version check - safe command
                            [py_cmd, "--version"], capture_output=True, check=True, timeout=5
                        )
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                return False
            else:
                subprocess.run(  # noqa: S603  # Tool version check - safe command
                    [tool, "--version"], capture_output=True, check=True, timeout=5
                )
                return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _create_sandbox(self) -> str:
        """Create a temporary sandbox directory."""
        sandbox = tempfile.mkdtemp(prefix="aibugbench_validation_")

        # Copy essential project files to sandbox
        essential_files = [
            "setup.py",
            "requirements.txt",
            "run_benchmark.py",
        ]

        for file_name in essential_files:
            src_path = self.project_root / file_name
            if src_path.exists():
                dst_path = Path(sandbox) / file_name
                shutil.copy2(src_path, dst_path)

        # Copy essential directories
        essential_dirs = [
            "benchmark",
            "prompts",
            "submissions/template",
        ]

        for dir_name in essential_dirs:
            src_path = self.project_root / dir_name
            if src_path.exists():
                dst_path = Path(sandbox) / dir_name
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path)
                else:
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

        return sandbox

    def _execute_command(self, command: Command) -> tuple[int, str, str]:
        """Execute a command and return (return_code, stdout, stderr)."""
        # Prepare the command for execution
        if command.platform == Platform.WINDOWS_CMD:
            shell_cmd = ["cmd", "/c", command.content]
        elif command.platform == Platform.WINDOWS_POWERSHELL:
            shell_cmd = ["powershell", "-Command", command.content]
        else:  # macOS/Linux
            shell_cmd = ["bash", "-c", command.content]

        try:
            process = subprocess.run(  # noqa: S603  # Shell command execution for docs validation
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30-second timeout
                cwd=os.getcwd(),
            )

            return process.returncode, process.stdout, process.stderr

        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return -1, "", f"Execution error: {e!s}"

    def _validate_output(self, actual_output: str, expected_output: str) -> bool:
        """Validate that actual output matches expected output."""
        # Normalize whitespace and line endings
        actual_normalized = re.sub(r"\s+", " ", actual_output.strip())
        expected_normalized = re.sub(r"\s+", " ", expected_output.strip())

        # Check for exact match
        if actual_normalized == expected_normalized:
            return True

        # Check for partial match (expected output is substring)
        if expected_normalized in actual_normalized:
            return True

        # Check for pattern match if expected output looks like a pattern
        if expected_output.startswith("regex:"):
            pattern = expected_output[6:]  # Remove "regex:" prefix
            return bool(re.search(pattern, actual_output, re.MULTILINE))

        return False

    def generate_report(
        self, summary: ValidationSummary, output_file: Path | None = None
    ) -> str:
        """Generate a detailed validation report."""
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append("AIBugBench Documentation Validation Report")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Summary statistics
        report_lines.append("SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Commands:     {summary.total_commands}")
        report_lines.append(f"Successful:         {summary.successful}")
        report_lines.append(f"Failed:             {summary.failed}")
        report_lines.append(f"Skipped:            {summary.skipped}")

        if summary.total_commands > 0:
            success_rate = (summary.successful / summary.total_commands) * 100
            report_lines.append(f"Success Rate:       {success_rate:.1f}%")

        report_lines.append("")

        # Platform breakdown
        report_lines.append("PLATFORM BREAKDOWN")
        report_lines.append("-" * 40)
        for platform, count in summary.platform_counts.items():
            if count > 0:
                report_lines.append(f"{platform.value:20} {count:4d} commands")
        report_lines.append("")

        # Command type breakdown
        report_lines.append("COMMAND TYPE BREAKDOWN")
        report_lines.append("-" * 40)
        for cmd_type, count in summary.type_counts.items():
            if count > 0:
                report_lines.append(f"{cmd_type.value:20} {count:4d} commands")
        report_lines.append("")

        # Failed commands
        failed_results = [r for r in summary.results if not r.success and not r.skipped]
        if failed_results:
            report_lines.append("FAILED COMMANDS")
            report_lines.append("-" * 40)

            for result in failed_results:
                report_lines.append(f"File: {result.command.file_path}")
                report_lines.append(f"Line: {result.command.line_number}")
                report_lines.append(f"Command: {result.command.content}")
                report_lines.append(f"Platform: {result.command.platform.value}")
                report_lines.append(f"Error: {result.error_message}")
                if result.stderr:
                    report_lines.append(f"Stderr: {result.stderr}")
                report_lines.append("")

        # Skipped commands
        skipped_results = [r for r in summary.results if r.skipped]
        if skipped_results:
            report_lines.append("SKIPPED COMMANDS")
            report_lines.append("-" * 40)

            skip_reasons = {}
            for result in skipped_results:
                reason = result.skip_reason
                if reason not in skip_reasons:
                    skip_reasons[reason] = []
                skip_reasons[reason].append(result)

            for reason, results in skip_reasons.items():
                report_lines.append(f"Reason: {reason} ({len(results)} commands)")
                for result in results[:3]:  # Show first 3 examples
                    report_lines.append(f"  - {result.command.content[:60]}...")
                if len(results) > 3:
                    report_lines.append(f"  ... and {len(results) - 3} more")
                report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)

        if failed_results:
            report_lines.append("• Review and fix failed commands in documentation")
            report_lines.append("• Ensure all documented commands work as expected")

        if summary.successful > 0:
            report_lines.append("• Successfully validated commands can be trusted")

        if any(r.command.command_type == CommandType.DESTRUCTIVE for r in summary.results):
            report_lines.append("• Consider removing or clearly marking destructive commands")

        report_lines.append("")
        report_lines.append("Validation completed at: " + time.strftime("%Y-%m-%d %H:%M:%S"))

        report_content = "\n".join(report_lines)

        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report_content)
                self.logger.info(f"Report saved to: {output_file}")
            except Exception as e:
                self.logger.error(f"Failed to save report to {output_file}: {e}")

        return report_content


def main():
    """Main entry point for the documentation validator."""
    parser = argparse.ArgumentParser(description="Validate all documented commands in AIBugBench")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--docs-only", action="store_true", help="Only scan for commands, don't execute them"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List extracted commands (no execution). Alias of --docs-only with concise output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Alias for --docs-only (deprecated name will be kept for user familiarity)",
    )
    parser.add_argument(
        "--skip-destructive",
        action="store_true",
        default=True,
        help="Skip potentially destructive commands (default: True)",
    )
    parser.add_argument(
        "--no-skip-destructive",
        action="store_true",
        help="Run destructive commands (use with extreme caution)",
    )
    parser.add_argument("--output", "-o", type=str, help="Output file for the validation report")
    parser.add_argument(
        "--project-root", type=str, help="Project root directory (default: auto-detect)"
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow execution of network commands (default: False for safety)",
    )
    parser.add_argument(
        "--platform",
        type=str,
        choices=["windows_cmd", "windows_powershell", "macos_linux"],
        help="Override platform detection (useful for testing PowerShell on Windows)",
    )
    parser.add_argument(
        "--no-sandbox-safe",
        action="store_true",
        help="Disable sandboxing for SAFE commands (reduces security but may improve performance)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit JSON summary to stdout (machine-readable). Use with --output to save text report "
            "separately."
        ),
    )
    parser.add_argument(
        "--json-file",
        type=str,
        help="Write JSON summary to specified path (implies --json).",
    )

    args = parser.parse_args()

    # Handle destructive command flag
    if args.no_skip_destructive:
        args.skip_destructive = False

    # Normalize alias flags
    if args.dry_run:
        args.docs_only = True
    if args.list:
        args.docs_only = True
    if args.json_file:
        args.json = True

    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Auto-detect project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent

        # Verify this looks like the AIBugBench project
        if not (project_root / "run_benchmark.py").exists():
            print("Error: Could not auto-detect project root. Use --project-root.")
            sys.exit(1)

    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}")
        sys.exit(1)

    print("AIBugBench Documentation Validator")
    print(f"Project root: {project_root}")
    print(f"System platform: {platform_module.system()}")
    if args.platform:
        print(f"Platform override: {args.platform}")
    if args.allow_network:
        print("Network commands: ENABLED")
    else:
        print("Network commands: DISABLED (use --allow-network to enable)")
    if args.no_sandbox_safe:
        print("SAFE command sandboxing: DISABLED")
    else:
        print("SAFE command sandboxing: ENABLED")
    print("")

    # Create validator
    validator = DocumentationValidator(
        project_root=project_root,
        verbose=args.verbose,
        skip_destructive=args.skip_destructive,
        allow_network=args.allow_network,
        platform_override=args.platform,
        sandbox_safe_commands=not args.no_sandbox_safe,
    )

    # Scan for commands
    print("Scanning documentation files for commands...")
    commands = validator.scan_documentation()

    if not commands:
        print("No commands found in documentation files.")
        return

    print(f"Found {len(commands)} commands across {len(validator.doc_files)} files")

    # Show command breakdown
    platform_counts = {}
    type_counts = {}

    for command in commands:
        platform_counts[command.platform] = platform_counts.get(command.platform, 0) + 1
        type_counts[command.command_type] = type_counts.get(command.command_type, 0) + 1

    print("\nCommand breakdown:")
    print("Platforms:")
    for platform, count in platform_counts.items():
        print(f"  {platform.value}: {count}")

    print("Types:")
    for cmd_type, count in type_counts.items():
        print(f"  {cmd_type.value}: {count}")

    if args.docs_only:
        if args.list:
            for c in commands[:50]:  # limit list for brevity
                print(f"[{c.platform.value}] {c.content}")
            if len(commands) > 50:
                print(f"... and {len(commands)-50} more")
        else:
            print("\n--docs-only specified, skipping command execution.")
        if args.json:
            summary_stub = {
                "total_commands": len(commands),
                "by_platform": {p.value: 0 for p in Platform},
                "by_type": {t.value: 0 for t in CommandType},
            }
            for c in commands:
                summary_stub["by_platform"][c.platform.value] = (
                    summary_stub["by_platform"].get(c.platform.value, 0) + 1
                )
                summary_stub["by_type"][c.command_type.value] = (
                    summary_stub["by_type"].get(c.command_type.value, 0) + 1
                )
            json_payload = {
                "mode": "list" if args.list else "scan",
                "summary": summary_stub,
            }
            if args.json_file:
                try:
                    Path(args.json_file).write_text(
                        json.dumps(json_payload, indent=2), encoding="utf-8"
                    )
                    print(f"JSON summary written to {args.json_file}")
                except Exception as e:  # pragma: no cover
                    print(f"Failed writing JSON file: {e}")
            print(json.dumps(json_payload, indent=2))
        return

    # Validate commands
    print("\nValidating commands...")
    if args.skip_destructive:
        print("(Skipping destructive commands for safety)")

    summary = validator.validate_commands(commands)

    # Generate and display report
    output_file = Path(args.output) if args.output else None
    report = validator.generate_report(summary, output_file)

    if args.json:
        json_summary = {
            "mode": "validate",
            "total": summary.total_commands,
            "successful": summary.successful,
            "failed": summary.failed,
            "skipped": summary.skipped,
            "platform_counts": {k.value: v for k, v in summary.platform_counts.items()},
            "type_counts": {k.value: v for k, v in summary.type_counts.items()},
        }
        if args.json_file:
            try:
                Path(args.json_file).write_text(
                    json.dumps(json_summary, indent=2), encoding="utf-8"
                )
                print(f"JSON summary written to {args.json_file}")
            except Exception as e:  # pragma: no cover
                print(f"Failed writing JSON file: {e}")
        print(json.dumps(json_summary, indent=2))

    print("\n" + report)

    # Exit with appropriate code
    if summary.failed > 0:
        print(f"\nValidation completed with {summary.failed} failures.")
        sys.exit(1)
    else:
        print(f"\nValidation completed successfully! All {summary.successful} commands passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
