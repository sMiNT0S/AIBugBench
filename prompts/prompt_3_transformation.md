# Prompt 3: Data Transformation & Business Logic

**IMPORTANT: Provide ONE COMPLETE PYTHON SCRIPT that can be saved as a single .py file and executed directly.**

## Task Overview

Using the refactored Python script from Prompt 1 as a base, you need to create a complete Python script that includes a data transformation function. This script will process the list of users from `user_data.json`.

## Function Requirements

Your complete script must include a Python function called `transform_and_enrich_users(user_list)` that takes the list of user dictionaries and performs the following operations on each user record:

1. **Standardize IDs**: Ensure every user id is an integer.

2. **Graceful Error Handling**: The function must not crash. If a user record is missing a required key for an operation (e.g., contact or email), it should skip that specific transformation for that user and, if possible, log a warning. For example, if email is null, the email_provider field cannot be created.

3. **Input Validation**: Validate incoming data to ensure data integrity before transformation.

4. **Enrich Data**: Add a new key, `email_provider`, to the contact dictionary. Its value should be the domain part of the email address (e.g., for jane.d@example.com, the provider is example.com).

5. **Complex Conditional Logic**: Add a new top-level key, `account_tier`. The logic is as follows:
   - If total_posts > 100 and total_comments > 300, the tier is "Gold".
   - If total_posts > 50, the tier is "Silver".
   - Otherwise, the tier is "Bronze".

6. **Type Correction**: Ensure the age value in the stats dictionary is always an integer.

7. **Return Value**: The function should return the list of fully transformed and enriched user records.

## Implementation Requirements

**Submit as a single, complete Python script** that can be saved as `prompt_3_transform.py` and executed directly. Include:

- All necessary imports
- The `transform_and_enrich_users()` function with complete logic
- Example usage code that loads `user_data.json`, calls your function, and displays results

**Example structure:**
```python
import json
# ... other imports

def transform_and_enrich_users(user_list):
    # Your transformation logic here
    pass

if __name__ == "__main__":
    # Load data, call function, print results
    pass
```
