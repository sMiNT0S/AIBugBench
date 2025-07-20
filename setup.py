#!/usr/bin/env python3
"""
Setup script for RealityCheckBench
Creates necessary directories and initializes test data.
"""

import os
import json
from pathlib import Path


def create_directory_structure():
    """Create the required directory structure."""
    directories = [
        "benchmark",
        "test_data",
        "submissions",
        "submissions/template",
        "results",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def create_test_data():
    """Create the test data files."""
    test_data_dir = Path("test_data")

    # Create process_records.py (the broken script)
    process_records_content = """# process_records.py: A script for processing user records from various sources
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
    print("✅ Created test_data/process_records.py")

    # Create config.yaml (the broken YAML)
    config_yaml_content = """# Configuration file for the data processor script
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
    print("✅ Created test_data/config.yaml")

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
    print("✅ Created test_data/user_data.json")


def create_template_files():
    """Create template submission files."""
    template_dir = Path("submissions/template")

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

    for filename, content in templates.items():
        filepath = template_dir / filename
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✅ Created template: {filename}")


def create_requirements_txt():
    """Create requirements.txt file."""
    requirements = """# AI Code Benchmark Requirements
pyyaml>=6.0
requests>=2.31.0
"""

    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created requirements.txt")


def main():
    """Run the setup process."""
    print("🚀 AI Code Benchmark Setup")
    print("=" * 40)

    # Create directory structure
    print("\n📁 Creating directory structure...")
    create_directory_structure()

    # Create test data
    print("\n📄 Creating test data files...")
    create_test_data()

    # Create template files
    print("\n📝 Creating submission templates...")
    create_template_files()

    # Create requirements file
    print("\n📋 Creating requirements.txt...")
    create_requirements_txt()

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print(
        "2. Copy template to create a submission: cp -r submissions/template submissions/your_model"
    )
    print("3. Run benchmark: python run_benchmark.py")


if __name__ == "__main__":
    main()
