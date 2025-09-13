# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
# Your sync_users_to_crm function
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
