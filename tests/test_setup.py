# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""
Tests for setup.py functionality.

Tests the setup process, particularly AI prompt file creation and detection.
"""

from io import StringIO
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


class TestSetupFunctionality:
    """Test setup.py core functionality."""

    def test_create_ai_prompt_file_new(self, temp_dir):
        """Test that create_ai_prompt_file creates ai_prompt.md when it doesn't exist."""
        # Import setup module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        # Set up temp directory with prompts subdirectory
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()

        with (
            patch("pathlib.Path", return_value=prompts_dir.parent),
            patch("pathlib.Path.cwd", return_value=temp_dir),
        ):
            # Mock Path behavior for the specific paths we need
            def mock_path(path_str):
                if path_str == "prompts":
                    return prompts_dir
                return Path(path_str)

            with patch("setup.Path", side_effect=mock_path):
                # Run the function
                result = create_ai_prompt_file()

                # Verify file was created
                ai_prompt_path = prompts_dir / "ai_prompt.md"
                assert ai_prompt_path.exists(), "ai_prompt.md should be created"

                # Verify content is correct
                with open(ai_prompt_path, encoding="utf-8") as f:
                    content = f.read()

                assert "Welcome to AIBugBench!" in content
                assert "TARGET" in content
                assert "SCORING SYSTEM" in content
                assert "THE CHALLENGES" in content
                assert "SUCCESS TIPS" in content

                # Verify return value matches file content
                assert result == content

    def test_create_ai_prompt_file_exists(self, temp_dir):
        """Test that create_ai_prompt_file detects existing ai_prompt.md."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        ai_prompt_path = prompts_dir / "ai_prompt.md"

        existing_content = "Existing AI Prompt Content for Testing"
        ai_prompt_path.write_text(existing_content, encoding="utf-8")

        def mock_path(path_str):
            if path_str == "prompts":
                return prompts_dir
            return Path(path_str)

        with (
            patch("setup.Path", side_effect=mock_path),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            result = create_ai_prompt_file()
            assert result == existing_content
            output = mock_stdout.getvalue()
            assert "prompts/ai_prompt.md exists" in output

    def test_ai_prompt_content_structure(self, temp_dir):
        """Test that created ai_prompt.md has correct structure and content."""
        # Import setup module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        # Set up temp directory
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()

        def mock_path(path_str):
            if path_str == "prompts":
                return prompts_dir
            return Path(path_str)

        with patch("setup.Path", side_effect=mock_path):
            # Create the file
            result = create_ai_prompt_file()

            # Verify key sections are present
            required_sections = [
                "Welcome to AIBugBench!",
                "[TARGET] WHAT IS AIBUGBENCH?",
                "[CHART] SCORING SYSTEM:",
                "[WRENCH] THE CHALLENGES:",
                "[BULB] SUCCESS TIPS:",
                "Ready to showcase your coding skills?",
            ]

            for section in required_sections:
                assert section in result, f"Missing required section: {section}"

            # Verify challenge descriptions are present
            challenges = [
                "Code Refactoring",
                "Data Format Conversion",
                "Data Transformation",
                "API Integration",
            ]

            for challenge in challenges:
                assert challenge in result, f"Missing challenge: {challenge}"

    def test_ai_prompt_requires_prompts_directory(self, temp_dir):
        """Test that create_ai_prompt_file requires prompts directory to exist."""
        # Import setup module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        # Verify directory doesn't exist initially
        prompts_dir = temp_dir / "prompts"
        assert not prompts_dir.exists()

        def mock_path(path_str):
            if path_str == "prompts":
                return prompts_dir
            return Path(path_str)

        with patch("setup.Path", side_effect=mock_path):
            # This should fail because prompts directory doesn't exist
            with pytest.raises(FileNotFoundError):
                create_ai_prompt_file()

            # Now create the directory and verify function works
            prompts_dir.mkdir(parents=True, exist_ok=True)
            result = create_ai_prompt_file()

            # Verify the ai_prompt.md was created
            ai_prompt_path = prompts_dir / "ai_prompt.md"
            assert ai_prompt_path.exists()
            assert "Welcome to AIBugBench!" in result

    @patch("setup.use_safe_unicode")
    def test_unicode_fallback_modes(self, mock_safe_unicode, temp_dir):
        """Test that setup works in both Unicode and safe modes."""
        # Import setup module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()

        def mock_path(path_str):
            if path_str == "prompts":
                return prompts_dir
            return Path(path_str)

        # Test safe mode (Windows fallback)
        mock_safe_unicode.return_value = True
        with (
            patch("setup.Path", side_effect=mock_path),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            result = create_ai_prompt_file()

            # Verify safe mode output
            output = mock_stdout.getvalue()
            assert "[OK]" in output
            assert result is not None

        # Clean up for next test
        ai_prompt_path = prompts_dir / "ai_prompt.md"
        if ai_prompt_path.exists():
            ai_prompt_path.unlink()

        # Test Unicode mode
        mock_safe_unicode.return_value = False
        with (
            patch("setup.Path", side_effect=mock_path),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
        ):
            result = create_ai_prompt_file()

            # Verify Unicode mode output
            output = mock_stdout.getvalue()
            assert "✅" in output
            assert result is not None

    def test_prompts_ai_prompt_reliably_present(self, temp_dir):
        """Test that prompts/ai_prompt.md is reliably present after setup behavior."""
        # Import setup module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from setup import create_ai_prompt_file

        # Set up temp directory with prompts subdirectory
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()

        def mock_path(path_str):
            if path_str == "prompts":
                return prompts_dir
            return Path(path_str)

        with patch("setup.Path", side_effect=mock_path):
            # Run setup function (simulating setup behavior)
            create_ai_prompt_file()

            # Assert that prompts/ai_prompt.md is reliably present
            ai_prompt_path = prompts_dir / "ai_prompt.md"
            assert ai_prompt_path.exists(), "prompts/ai_prompt.md must be present after setup"
            assert ai_prompt_path.is_file(), "prompts/ai_prompt.md must be a file"

            # Verify file is not empty
            assert ai_prompt_path.stat().st_size > 0, "prompts/ai_prompt.md must not be empty"

            # Verify file can be read
            with open(ai_prompt_path, encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 100, "prompts/ai_prompt.md must contain substantial content"
            assert "AIBugBench" in content, "prompts/ai_prompt.md must contain AIBugBench reference"
