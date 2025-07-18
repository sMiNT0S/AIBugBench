# process_records.py: A script for processing user records from various sources
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