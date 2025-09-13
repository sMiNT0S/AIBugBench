#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""
Setup script for AIBugBench
Creates necessary directories and initializes test data.
"""

import json
import os
from pathlib import Path
import sys


def use_safe_unicode() -> bool:
    """Check if Unicode emojis can be safely displayed."""
    try:
        # Check if output is being piped or redirected
        if not sys.stdout.isatty():
            return True  # Use safe fallback for piped output

        # Test if current encoding supports emojis
        encoding = sys.stdout.encoding or "utf-8"
        if encoding.lower() in ["cp1252", "ascii"]:
            return True  # Use safe fallback for limited encodings

        "🚀".encode(encoding)
        return False  # Unicode is safe
    except (UnicodeEncodeError, LookupError, AttributeError):
        return True  # Use safe fallback


def create_ai_prompt_file():
    """Create the AI prompt message markdown file for easy reference.

    Canonical file name: prompts/ai_prompt.md (versioned).
    """
    prompts_dir = Path("prompts")
    prompt_file_path = prompts_dir / "ai_prompt.md"
    safe_mode = use_safe_unicode()
    checkmark = "✅" if not safe_mode else "[OK]"

    # Check if file already exists
    if prompt_file_path.exists():
        print(f"{checkmark} prompts/ai_prompt.md exists")
        # Read and return existing content
        with open(prompt_file_path, encoding="utf-8") as f:
            return f.read()

    # Canonical content written to ai_prompt.md (safe mode version shown if emojis unsafe)
    ai_prompt_content = """Welcome to AIBugBench!

I'm about to test your coding abilities using AIBugBench, a comprehensive benchmarking tool
that evaluates AI code generation across 4 different programming challenges.

Here's what you need to know:

[TARGET] WHAT IS AIBUGBENCH?
AIBugBench is a scoring system that tests your ability to:
- Fix and refactor broken Python code
- Convert between YAML and JSON formats correctly
- Transform and enrich data structures
- Implement secure API integrations with proper error handling

[CHART] SCORING SYSTEM:
You'll be scored across 7 categories (100 points total):
- Syntax correctness
- Code structure and organization
- Execution and functionality
- Code quality and best practices
- Security considerations
- Performance optimization
- Code maintainability

[WRENCH] THE CHALLENGES:
1. **Code Refactoring**: Fix a broken Python script with style, logic, and efficiency issues
2. **Data Format Conversion**: Correct malformed YAML and convert it to proper JSON
3. **Data Transformation**: Implement complex data processing with business rules
4. **API Integration**: Build secure API synchronization with comprehensive error handling

[BULB] SUCCESS TIPS:
- Read requirements carefully - each challenge has specific criteria
- Focus on clean, secure, and efficient code
- Handle edge cases and errors properly
- Follow Python best practices (PEP 8)
- Test your solutions mentally before submitting

Ready to showcase your coding skills? Let's begin with the AIBugBench challenges!

---
Copy this message to your AI/LLM, then proceed with the benchmark prompts.
"""

    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(ai_prompt_content)

    print(f"{checkmark} Created prompts/ai_prompt.md")
    return ai_prompt_content


def display_ai_prompt():
    """Display the AI prompt message during setup."""
    # Skip entirely in non-interactive environments or if explicitly disabled.
    if (
        os.environ.get("AIBUGBENCH_NONINTERACTIVE") == "1"
        or not sys.stdout.isatty()
        or not sys.stdin.isatty()
    ):
        return  # Silent skip during pip builds / CI

    safe_mode = use_safe_unicode()

    print("\n" + "=" * 60)
    robot_icon = "🤖" if not safe_mode else "[AI]"
    print(f"{robot_icon} AI PREPARATION PROMPT")
    print("=" * 60)
    print("\nBefore starting the benchmark, copy and paste this message")
    print("to your AI/LLM to prepare it for the coding challenges:\n")

    print("-" * 60)

    if safe_mode:
        ai_prompt_content = """Welcome to AIBugBench!

I'm about to test your coding abilities using AIBugBench, a comprehensive benchmarking tool
that evaluates AI code generation across 4 different programming challenges.

Here's what you need to know:

[TARGET] WHAT IS AIBUGBENCH?
AIBugBench is a scoring system that tests your ability to:
- Fix and refactor broken Python code
- Convert between YAML and JSON formats correctly
- Transform and enrich data structures
- Implement secure API integrations with proper error handling

[CHART] SCORING SYSTEM:
You'll be scored across 7 categories (100 points total):
- Syntax correctness
- Code structure and organization
- Execution and functionality
- Code quality and best practices
- Security considerations
- Performance optimization
- Code maintainability

[WRENCH] THE CHALLENGES:
1. **Code Refactoring**: Fix a broken Python script with style, logic, and efficiency issues
2. **Data Format Conversion**: Correct malformed YAML and convert it to proper JSON
3. **Data Transformation**: Implement complex data processing with business rules
4. **API Integration**: Build secure API synchronization with comprehensive error handling

[BULB] SUCCESS TIPS:
- Read requirements carefully - each challenge has specific criteria
- Focus on clean, secure, and efficient code
- Handle edge cases and errors properly
- Follow Python best practices (PEP 8)
- Test your solutions mentally before submitting

Ready to showcase your coding skills? Let's begin with the AIBugBench challenges!"""
    else:
        ai_prompt_content = """Welcome to AIBugBench!

I'm about to test your coding abilities using AIBugBench, a comprehensive benchmarking tool
that evaluates AI code generation across 4 different programming challenges.

Here's what you need to know:

🎯 WHAT IS AIBUGBENCH?
AIBugBench is a scoring system that tests your ability to:
- Fix and refactor broken Python code
- Convert between YAML and JSON formats correctly
- Transform and enrich data structures
- Implement secure API integrations with proper error handling

📊 SCORING SYSTEM:
You'll be scored across 7 categories (100 points total):
- Syntax correctness
- Code structure and organization
- Execution and functionality
- Code quality and best practices
- Security considerations
- Performance optimization
- Code maintainability

🔧 THE CHALLENGES:
1. **Code Refactoring**: Fix a broken Python script with style, logic, and efficiency issues
2. **Data Format Conversion**: Correct malformed YAML and convert it to proper JSON
3. **Data Transformation**: Implement complex data processing with business rules
4. **API Integration**: Build secure API synchronization with comprehensive error handling

💡 SUCCESS TIPS:
- Read requirements carefully - each challenge has specific criteria
- Focus on clean, secure, and efficient code
- Handle edge cases and errors properly
- Follow Python best practices (PEP 8)
- Test your solutions mentally before submitting

Ready to showcase your coding skills? Let's begin with the AIBugBench challenges!"""

    print(ai_prompt_content)
    print("-" * 60)
    file_icon = "📝" if not safe_mode else "[FILE]"
    timer_icon = "⏳" if not safe_mode else "[WAIT]"
    print(f"\n{file_icon} This prompt has been saved to 'prompts/ai_prompt.md' for easy access.")
    print(f"\n{timer_icon} Please copy this message to your AI/LLM before proceeding...")
    print("Press Enter when you've prepared your AI and are ready to continue...")
    # Extra defensive guard: even though we earlier returned for non-interactive
    # contexts, pip build wrappers can produce edge cases; double-check.
    if (
        sys.stdin is not None
        and hasattr(sys.stdin, "isatty")
        and sys.stdin.isatty()
        and sys.stdout.isatty()
        and not os.environ.get("CI")
    ):
        try:  # pragma: no cover - purely interactive branch
            input()
        except EOFError:  # Fallback if environment flips mid-run
            print("[Non-interactive] Skipping input pause (EOF).")
    else:
        print("[Non-interactive] Skipping input pause.")


def create_directory_structure():
    """Create the required directory structure (Phase 1 canonical layout only)."""
    directories = [
        "benchmark",
        "test_data",
        "prompts",
        "submissions",
        # Tiered structure (canonical)
        "submissions/reference_implementations",
        "submissions/templates",
        "submissions/templates/template",
        "submissions/user_submissions",
        # Results directory retained
        "results",
    ]

    safe_mode = use_safe_unicode()
    checkmark = "✅" if not safe_mode else "[OK]"

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"{checkmark} Created directory: {directory}")


def create_test_data():
    """Create the test data files."""
    test_data_dir = Path("test_data")
    safe_mode = use_safe_unicode()
    checkmark = "✅" if not safe_mode else "[OK]"

    # Create process_records.py (the broken script)
    process_records_content = """# process_records.py: A script for processing user records from
# various sources
# Author: A. Novice Developer

import json, yaml, sys, os
from datetime import datetime

class  Processor:
  def __init__(self, config_path):
    self.configs = self.load_config (config_path)
    if self.configs['use_legacy_paths'] == 'true':
        self.data_path = self.configs['paths']['legacy_data_source']
    else:
        self.data_path = self.configs['paths']['data_source']
    self.all_records = []

  # config loader
  def load_config(self,   path):
    with open(path) as file:
      configuration = yaml.load(file, Loader=yaml.FullLoader)
      return configuration

  def get_data_from_json_file(self):
    # This function gets data and puts it into all_records
    f = open(self.data_path)
    raw_data = json.load(f)
    self.all_records = raw_data['users']
    f.close()
    return self.all_records

  def process_all_records(self, filter_by_country=None):
    # Primary processing function, does a lot of things
    # It filters, validates, and transforms records.
    processed = []
    for i in range(len(self.all_records)):
      record = self.all_records[i]
      # country filter logic
      if filter_by_country:
        if record['profile']['country'] != filter_by_country:
          continue

      # Validate record based on config thresholds
      is_valid = False
      if 'validation_rules' in self.configs:
          min_age = self.configs['validation_rules']['min_age_years']
          min_posts = self.configs['validation_rules']['minimum_posts']
          if record['stats']['age'] > min_age and record['stats']['total_posts'] > min_posts:
              is_valid = True

      if is_valid == True:
        # data transformation
        new_record = {}
        new_record['user_id'] = "user_" + str(record['id'])
        full_name = record['first_name'] + " " + record['last_name']
        new_record['full_name'] = full_name
        new_record['email'] = record['contact']['email']
        new_record['status'] = self.determine_status(record['metadata']['last_login'])
        processed.append(new_record)

    # Some final manipulation
    for p in processed:
        p['processed_timestamp'] = datetime.now()

    return processed

  def determine_status(self, last_login_str):
    # determine user status based on last login.
    # very important business logic!
    last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d")
    delta = datetime.now() - last_login_date
    if delta.days < 30:
        return 'active'
    elif delta.days < 90:
        return 'inactive'
    else:
        return "archived" # this should be a different status maybe?

# main execution block
if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_file_path = sys.argv[1]
    else:
        config_file_path = 'config.yaml' # default path

    processor_instance = Processor(config_file_path)
    processor_instance.get_data_from_json_file()
    final_data = processor_instance.process_all_records('USA')
    print("Processed Records:")
    print(json.dumps(final_data, indent=4, default=str))
"""

    with open(test_data_dir / "process_records.py", "w") as f:
        f.write(process_records_content)
    print(f"{checkmark} Created test_data/process_records.py")

    # Create config.yaml (the broken YAML)
    config_yaml_content = """# yaml-language-server: $schema=
# yamllint disable
# Configuration file for the data processor script
# Contains paths, rules, and feature flags.

use_legacy_paths: 'true'

paths:
    data_source: /srv/data/production/users.json
 legacy_data_source: ./user_data.json  # Note: This is a relative path
    log_file: /var/log/processor.log

# Validation rules for user records
validation_rules:
    min_age_years: "21" # Must be of legal age
    minimum_posts: 5
    # a required_fields section was here, but removed for now
    required_fields:
     - id
     - first_name
      - last_name
     - contact.email # this format is tricky

api_keys:
  - service: 'geolocator'
    key: 'xyz-123-abc'
  - service: 'notifier'
    key: 'def-456-ghi'

# feature flags section
feature_flags:
    enable_email_notifications: false
    beta_processor_active: true
    user_segmentation_enabled: 'false'
server_settings:
  port: 8080
  timeout_seconds: '60'
  retry_attempts: 3
    # Bad indentation below
   max_connections: 100
"""

    with open(test_data_dir / "config.yaml", "w") as f:
        f.write(config_yaml_content)
    print(f"{checkmark} Created test_data/config.yaml")

    # Create user_data.json
    user_data = {
        "export_date": "2025-07-16T22:00:00Z",
        "source_system": "Mainframe-Export-v3",
        "users": [
            {
                "id": "101",
                "first_name": "Jane",
                "last_name": "Doe",
                "contact": {"email": "jane.d@example.com", "phone": None},
                "profile": {"country": "USA", "timezone": "America/New_York"},
                "metadata": {"created_at": "2022-01-15", "last_login": "2025-07-15"},
                "stats": {"age": 34, "total_posts": 150, "total_comments": 450},
            },
            {
                "id": "102",
                "first_name": "John",
                "last_name": "Smith",
                "contact": {"email": "j.smith@workplace.net"},
                "profile": {"country": "UK", "timezone": "Europe/London"},
                "metadata": {"created_at": "2021-11-20", "last_login": "2025-06-20"},
                "stats": {"age": "28", "total_posts": 4, "total_comments": 20},
            },
            {
                "id": 103,
                "first_name": "Pierre",
                "last_name": "Dupont",
                "contact": {"email": None, "phone": "33-123456789"},
                "profile": {"country": "France", "timezone": "Europe/Paris"},
                "metadata": {"created_at": "2023-05-10", "last_login": "2024-01-10"},
                "stats": {"age": 45, "total_posts": 88, "total_comments": 192},
            },
            {
                "id": "104",
                "first_name": "Klaus",
                "last_name": "Müller",
                "contact": {"email": "klaus.m@example.de"},
                "profile": {"country": "Germany", "timezone": "Europe/Berlin"},
                "metadata": {"created_at": "2020-02-02", "last_login": "2025-05-01"},
                "stats": {"age": 20, "total_posts": 42, "total_comments": 130},
            },
            {
                "id": "105",
                "first_name": "Emily",
                "last_name": "White",
                "contact": {"email": "emily.w@example.com"},
                "profile": {"country": "USA", "timezone": "America/Chicago"},
                "metadata": {"created_at": "2024-03-18", "last_login": "2025-07-02"},
                "stats": {"age": 29, "total_posts": 25, "total_comments": 78},
            },
        ],
    }

    with open(test_data_dir / "user_data.json", "w") as f:
        json.dump(user_data, f, indent=2)
    print(f"{checkmark} Created test_data/user_data.json")


def create_template_files():
    """Create template submission files (tier-aware)."""
    # Prefer new tiered path
    template_dir = Path("submissions/templates/template")
    template_dir.mkdir(parents=True, exist_ok=True)

    # Template files with helpful comments
    templates = {
        "prompt_1_solution.py": """# Your refactored version of process_records.py
# TODO: Implement your solution here

# Requirements:
# 1. Fix all style issues (PEP 8)
# 2. Add proper error handling
# 3. Improve efficiency
# 4. Fix logical errors
# 5. Follow modern Python best practices

import json
import yaml
# Add other imports as needed

# Your refactored code here
""",
        "prompt_2_config_fixed.yaml": """# Your corrected version of config.yaml
# TODO: Fix all YAML syntax and structure issues

# Requirements:
# 1. Fix all indentation errors
# 2. Ensure consistent formatting
# 3. Preserve all original data
# 4. Convert string booleans to actual booleans
# 5. Convert string numbers to actual numbers
""",
        "prompt_2_config.json": """{
  "comment": "JSON conversion of the corrected config",
  "TODO": "Convert the corrected YAML to JSON with proper data types"
}
""",
        "prompt_3_transform.py": '''# Your transform_and_enrich_users function
# TODO: Implement data transformation logic

def transform_and_enrich_users(user_list):
    """
    Transform and enrich user records.
    Requirements:
    1. Standardize IDs to integers
    2. Add email_provider to contact dict
    3. Add account_tier based on activity
    4. Ensure age is always an integer
    5. Handle missing data gracefully
    Args:
        user_list: List of user dictionaries
    Returns:
        List of transformed user dictionaries
    """
    # Your implementation here
    pass
''',
        "prompt_4_api_sync.py": '''# Your sync_users_to_crm function
# TODO: Implement API synchronization with error handling

import requests

def sync_users_to_crm(user_data, api_token):
    """
    Synchronize users with CRM system.
    Requirements:
    1. POST to https://api.crm-system.com/v2/users/sync
    2. Include proper headers (Content-Type, Authorization)
    3. Send users in {"users": [...]} format
    4. Handle all specified error cases
    5. Return job_id on success
    Args:
        user_data: List of user records
        api_token: Bearer token for authentication
    Returns:
        job_id on success, None on failure
    """
    # Your implementation here
    pass
''',
    }

    safe_mode = use_safe_unicode()
    checkmark = "✅" if not safe_mode else "[OK]"

    for filename, content in templates.items():
        filepath = template_dir / filename
        with open(filepath, "w") as f:
            f.write(content)
        print(f"{checkmark} Created template: {filename}")


def create_requirements_txt():
    """Create requirements.txt file."""
    requirements = """# AI Code Benchmark Requirements
pyyaml>=6.0
requests>=2.31.0
"""

    with open("requirements.txt", "w") as f:
        f.write(requirements)

    safe_mode = use_safe_unicode()
    checkmark = "✅" if not safe_mode else "[OK]"
    print(f"{checkmark} Created requirements.txt")


def main():
    """Run the setup process."""
    safe_mode = use_safe_unicode()

    rocket_icon = "🚀" if not safe_mode else "[SETUP]"
    print(f"{rocket_icon} AIBugBench Setup")
    print("=" * 40)

    # Create directory structure
    folder_icon = "📁" if not safe_mode else "[DIR]"
    print(f"\n{folder_icon} Creating directory structure...")
    create_directory_structure()

    # Create test data
    file_icon = "📄" if not safe_mode else "[FILES]"
    print(f"\n{file_icon} Creating test data files...")
    create_test_data()

    # Create template files
    doc_icon = "📝" if not safe_mode else "[TEMPLATES]"
    print(f"\n{doc_icon} Creating submission templates...")
    create_template_files()

    # Create requirements file
    list_icon = "📋" if not safe_mode else "[REQ]"
    print(f"\n{list_icon} Creating requirements.txt...")
    create_requirements_txt()

    # Create AI prompt file
    ai_icon = "🤖" if not safe_mode else "[AI]"
    print(f"\n{ai_icon} Creating AI preparation prompt...")
    create_ai_prompt_file()

    check_icon = "✅" if not safe_mode else "[DONE]"
    print(f"\n{check_icon} Setup complete!")

    # Sabotage notice
    warning_icon = "⚠️" if not safe_mode else "[INFO]"
    print(
        f"{warning_icon} Test fixtures contain intentional bugs for validation "
        f"- see SABOTAGE_NOTES.md for details"
    )

    # Display AI prompt for user to copy to their AI/LLM
    display_ai_prompt()

    rocket_ready = "🚀" if not safe_mode else "[READY]"
    print(f"\n{rocket_ready} Ready to start benchmarking!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy template to create a submission:")
    print("   • Windows CMD: xcopy /E /I submissions\\template submissions\\your_model")
    print(
        "   • Windows PowerShell: Copy-Item -Recurse submissions\\template submissions\\your_model"
    )
    print("   • macOS/Linux: cp -r submissions/template submissions/your_model")
    print("3. Run benchmark: python run_benchmark.py --model your_model")

    note_icon = "📝" if not safe_mode else "[NOTE]"
    print(f"\n{note_icon} The AI prompt is saved in 'prompts/ai_prompt.md' for future reference.")


if __name__ == "__main__":
    # Only run bootstrap when explicitly requested; otherwise do nothing so
    # that setuptools build backend handles metadata generation without side effects.
    if os.environ.get("AIBUGBENCH_BOOTSTRAP") == "1":  # pragma: no cover
        main()
