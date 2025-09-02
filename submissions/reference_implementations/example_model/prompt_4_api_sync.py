#!/usr/bin/env python3
"""
CRM Synchronization Module
Handles synchronization of processed user data with external CRM system via REST API.
"""

import json
import logging
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_users_to_crm(user_data: list[dict[str, Any]], api_token: str) -> str | None:
    """Synchronize user data with external CRM system via REST API.

    This function sends user data to the CRM system's sync endpoint and handles
    various error scenarios including network issues and HTTP errors.

    Args:
        user_data: List of user dictionaries to sync with the CRM
        api_token: Bearer token for API authentication

    Returns:
        job_id from successful response, or None if sync fails

    Raises:
        No exceptions are raised - all errors are handled internally
    """
    # API endpoint configuration
    api_url = "https://api.crm-system.com/v2/users/sync"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    # Prepare payload
    payload = {
        "users": user_data
    }

    try:
        # Log the sync attempt
        logger.info(f"Attempting to sync {len(user_data)} users to CRM system")
        logger.debug(f"API URL: {api_url}")

        # Make the POST request
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30  # 30 second timeout
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Success cases (200 OK or 202 Accepted)
        if response.status_code in [200, 202]:
            try:
                response_data = response.json()
                job_id = response_data.get('job_id')

                if job_id:
                    logger.info(f"Successfully synced users. Job ID: {job_id}")
                    print(f"✅ Sync successful! Job ID: {job_id}")
                    return job_id
                else:
                    logger.error("Success response missing 'job_id' field")
                    print("⚠️  Warning: Sync appeared successful but no job_id was returned")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                print("❌ Error: Could not parse response from CRM system")
                return None

    except ConnectionError as e:
        # Network connectivity issues
        logger.error(f"Network connection error: {e}")
        print("❌ Network Error: Unable to connect to CRM system")
        print("   Please check your internet connection and try again")
        return None

    except Timeout as e:
        # Request timeout
        logger.error(f"Request timeout: {e}")
        print("❌ Timeout Error: CRM system took too long to respond")
        print("   The server might be experiencing high load. Please try again later")
        return None

    except HTTPError:
        # HTTP error responses
        status_code = response.status_code

        if status_code == 401:
            # Unauthorized - Invalid token
            logger.error("Authentication failed - Invalid API token")
            print("❌ Authentication Error (401): Invalid API token")
            print("   Please verify your API token is correct and not expired")

        elif status_code == 400:
            # Bad Request - Invalid data
            logger.error("Bad request - Invalid data format")
            print("❌ Bad Request Error (400): Invalid data format")
            print("   The user data format is not acceptable to the CRM system")

            # Try to get more details from response
            try:
                error_details = response.json()
                if 'errors' in error_details:
                    print(f"   Details: {error_details['errors']}")
            except (ValueError, KeyError) as parse_error:
                logger.error(f"Failed to parse error details from response: {parse_error}")

        elif status_code == 503:
            # Service Unavailable
            logger.error("CRM service is temporarily unavailable")
            print("❌ Service Unavailable Error (503): CRM system is temporarily down")
            print("   The service is undergoing maintenance or is overloaded")
            print("   Please try again in a few minutes")

        elif 400 <= status_code < 500:
            # Other 4xx client errors
            logger.error(f"Client error occurred: {status_code}")
            print(f"❌ Client Error ({status_code}): Request failed")
            print("   There was an issue with the request. Please check your data and try again")

        elif 500 <= status_code < 600:
            # Other 5xx server errors
            logger.error(f"Server error occurred: {status_code}")
            print(f"❌ Server Error ({status_code}): CRM system encountered an error")
            print("   The CRM system is experiencing technical difficulties")
            print("   Please try again later or contact support if the issue persists")

        else:
            # Unexpected status code
            logger.error(f"Unexpected status code: {status_code}")
            print(f"❌ Unexpected Error ({status_code}): An unknown error occurred")

        return None

    except RequestException as e:
        # Catch-all for other requests exceptions
        logger.error(f"Request exception: {e}")
        print("❌ Request Error: An unexpected error occurred while contacting the CRM")
        print(f"   Technical details: {e!s}")
        return None

    except Exception as e:
        # Catch any other unexpected exceptions
        logger.error(f"Unexpected error: {e}")
        print("❌ Unexpected Error: Something went wrong")
        print(f"   Technical details: {e!s}")
        return None


def demo_sync():
    """
    Demonstrate the sync function with sample data and various scenarios.
    """
    # Sample user data (from previous transformations)
    sample_users = [
        {
            "id": 101,
            "user_id": "user_101",
            "full_name": "Jane Doe",
            "email": "jane.d@example.com",
            "status": "active",
            "account_tier": "Gold"
        },
        {
            "id": 102,
            "user_id": "user_102",
            "full_name": "John Smith",
            "email": "j.smith@workplace.net",
            "status": "active",
            "account_tier": "Bronze"
        }
    ]

    print("CRM Sync Demonstration")
    print("=" * 50)

    # Scenario 1: Successful sync
    print("\n1. Testing successful sync:")
    api_token = "demo-token-12345-fake"  # noqa: S105  # Test token for example code
    job_id = sync_users_to_crm(sample_users, api_token)
    print(f"   Returned job_id: {job_id}")

    # Scenario 2: Invalid token
    print("\n2. Testing with invalid token:")
    invalid_token = "fake-invalid-token"  # noqa: S105  # Test token for example code
    job_id = sync_users_to_crm(sample_users, invalid_token)
    print(f"   Returned job_id: {job_id}")

    # Scenario 3: Empty user data
    print("\n3. Testing with empty user data:")
    job_id = sync_users_to_crm([], api_token)
    print(f"   Returned job_id: {job_id}")

    # Scenario 4: Malformed user data
    print("\n4. Testing with malformed data:")
    malformed_users = [{"invalid": "data"}]
    job_id = sync_users_to_crm(malformed_users, api_token)
    print(f"   Returned job_id: {job_id}")


def main():
    """
    Main function showing integration with the transformation pipeline.
    """
    import sys

    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python sync_crm.py <api_token>")
        print("Example: python sync_crm.py your-api-token-here")
        sys.exit(1)

    api_token = sys.argv[1]

    # In a real scenario, you would:
    # 1. Load the user data from JSON
    # 2. Transform it using transform_and_enrich_users()
    # 3. Sync to CRM

    # For this example, we'll use sample data
    sample_transformed_users = [
        {
            "id": 101,
            "first_name": "Jane",
            "last_name": "Doe",
            "contact": {
                "email": "jane.d@example.com",
                "email_provider": "example.com"
            },
            "profile": {
                "country": "USA",
                "timezone": "America/New_York"
            },
            "stats": {
                "age": 34,
                "total_posts": 150,
                "total_comments": 450
            },
            "account_tier": "Gold",
            "status": "active"
        }
    ]

    print(f"Syncing {len(sample_transformed_users)} users to CRM...")
    job_id = sync_users_to_crm(sample_transformed_users, api_token)

    if job_id:
        print("\n✅ Sync completed successfully!")
        print(f"   You can track the progress using job ID: {job_id}")
    else:
        print("\n❌ Sync failed. Please check the error messages above.")


if __name__ == "__main__":
    # Uncomment the line below to run the demonstration
    # demo_sync()

    # Run the main sync process
    main()
