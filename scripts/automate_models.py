#!/usr/bin/env python3
"""
DEPRECATED: This automation script is provided for reference only.
Current implementation: OFFLINE-ONLY - No live API calls supported.

AIBugBench automation script for AI model testing.
Originally designed for API-based automation but currently operates in offline mode only.

Usage:
    python scripts/automate_models.py --provider openai --model gpt-4
    python scripts/automate_models.py --provider anthropic --model claude-3-sonnet-20240229

Note: API calls are disabled. Manual copy-paste workflow is recommended.
"""

import argparse
import sys


def main():
    """Main automation entry point - OFFLINE MODE ONLY."""
    print("=" * 60)
    print("DEPRECATION NOTICE")
    print("=" * 60)
    print("This automation script is currently DEPRECATED and OFFLINE-ONLY.")
    print("No live API calls are supported in the current implementation.")
    print()
    print("Recommended workflow:")
    print("1. Use manual copy-paste approach from QUICKSTART.md")
    print(
        "2. Copy template: submissions/templates/template -> "
        "submissions/user_submissions/your_model"
    )
    print("3. Paste AI responses into each file manually")
    print("4. Run: python run_benchmark.py --model your_model")
    print()
    print("For detailed instructions, see QUICKSTART.md")
    print("=" * 60)

    parser = argparse.ArgumentParser(
        description="AI model automation (OFFLINE MODE - No API calls)"
    )
    parser.add_argument("--provider", choices=["openai", "anthropic"],
                       help="AI provider (reference only)")
    parser.add_argument("--model", help="Model name (reference only)")

    args = parser.parse_args()

    if args.provider or args.model:
        print(f"Provider: {args.provider or 'not specified'}")
        print(f"Model: {args.model or 'not specified'}")
        print("Note: These parameters are ignored in offline mode.")

    print("\nExiting - use manual workflow instead.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
