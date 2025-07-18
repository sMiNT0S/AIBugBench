# Prompt 3: Large file reasoning and bulk transformation transform (Da Big 'Un)

Using the refactored Python script from Prompt 1 as a base, you need to write a new data transformation function. This function will process the list of users from user_data.json.

Write a Python function called transform_and_enrich_users(user_list) that takes the list of user dictionaries and performs the following operations on each user record:

    Standardize IDs: Ensure every user id is an integer.

    Graceful Error Handling: The function must not crash. If a user record is missing a required key for an operation (e.g., contact or email), it should skip that specific transformation for that user and, if possible, log a warning. For example, if email is null, the email_provider field cannot be created.

    Enrich Data: Add a new key, email_provider, to the contact dictionary. Its value should be the domain part of the email address (e.g., for jane.d@example.com, the provider is example.com).

    Complex Conditional Logic: Add a new top-level key, account_tier. The logic is as follows:

        If total_posts > 100 and total_comments > 300, the tier is "Gold".

        If total_posts > 50, the tier is "Silver".

        Otherwise, the tier is "Bronze".

    Type Correction: Ensure the age value in the stats dictionary is always an integer.

    Return Value: The function should return the list of fully transformed and enriched user records.

Demonstrate how you would call this function after loading the data from user_data.json and print the final result.
