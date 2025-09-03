#!/usr/bin/env python3
"""User data transformation and enrichment utilities (reference implementation).

Applies normalization and derives additional attributes (email provider, account
tier) while keeping transformations side-effect free (records are copied).
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any, cast

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def transform_and_enrich_users(user_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform and enrich user records.

    Operations performed:
    1. Standardizes IDs to integers
    2. Extracts email providers from email addresses
    3. Calculates account tiers based on activity
    4. Ensures age values are integers

    Args:
        user_list: List of user dictionaries to transform

    Returns:
        List of transformed and enriched user records
    """
    transformed_users: list[dict[str, Any]] = []
    for idx, user in enumerate(user_list):
        try:
            # Create a deep copy to avoid modifying the original
            # Efficient deep copy (structural - user records expected to be JSON compatible)
            transformed_user = copy.deepcopy(user)

            # 1. Standardize IDs - ensure it's an integer
            user_id = user.get("id")
            if user_id is not None:
                try:
                    transformed_user["id"] = int(user_id)
                except (ValueError, TypeError) as exc:
                    logger.warning(
                        "User at index %s: Could not convert ID '%s' to integer: %s",
                        idx,
                        user_id,
                        exc,
                    )
                    # Keep original value if conversion fails
            else:
                logger.warning(f"User at index {idx}: Missing 'id' field")

            # 2. Enrich data - add email_provider to contact dictionary
            if "contact" in transformed_user and isinstance(transformed_user["contact"], dict):
                email = transformed_user["contact"].get("email")

                if email and isinstance(email, str) and "@" in email:
                    try:
                        # Extract domain from email
                        domain = email.split("@")[1]
                        transformed_user["contact"]["email_provider"] = domain
                        logger.debug(
                            "User %s: Added email provider '%s'", transformed_user.get("id"), domain
                        )
                    except IndexError:
                        logger.warning(
                            "User %s: Invalid email format '%s'", transformed_user.get("id"), email
                        )
                else:
                    if email is None:
                        logger.warning(
                            "User %s: Email is null, cannot extract provider",
                            transformed_user.get("id"),
                        )
                    elif not isinstance(email, str):
                        logger.warning(
                            "User %s: Email is not a string: %s",
                            transformed_user.get("id"),
                            type(email),
                        )
                    else:
                        logger.warning(
                            "User %s: Invalid email format '%s'", transformed_user.get("id"), email
                        )
            else:
                logger.warning(
                    "User %s: Missing or invalid 'contact' field",
                    transformed_user.get("id"),
                )

            # 3. Add account_tier based on activity
            transformed_user["account_tier"] = calculate_account_tier(transformed_user)

            # 4. Type correction - ensure age is always an integer
            if "stats" in transformed_user and isinstance(transformed_user["stats"], dict):
                age = transformed_user["stats"].get("age")
                if age is not None:
                    try:
                        transformed_user["stats"]["age"] = int(age)
                    except (ValueError, TypeError) as exc:
                        logger.warning(
                            "User %s: Could not convert age '%s' to integer: %s",
                            transformed_user.get("id"),
                            age,
                            exc,
                        )
                        # Remove invalid age rather than keeping bad data
                        del transformed_user["stats"]["age"]
                else:
                    logger.warning("User %s: Age is missing in stats", transformed_user.get("id"))
            else:
                logger.warning(
                    "User %s: Missing or invalid 'stats' field", transformed_user.get("id")
                )

            transformed_users.append(transformed_user)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("User at index %s: Unexpected error during transformation: %s", idx, exc)
            # Still add the user even if transformation partially failed
            transformed_users.append(user)
    logger.info(f"Successfully transformed {len(transformed_users)} users")
    return transformed_users


def calculate_account_tier(user: dict[str, Any]) -> str:
    """Calculate account tier based on user activity.

    Tier logic:
    - Gold: total_posts > 100 AND total_comments > 300
    - Silver: total_posts > 50
    - Bronze: Otherwise

    Args:
        user: User dictionary containing stats

    Returns:
        Account tier as string: "Gold", "Silver", or "Bronze"
    """
    try:
        stats = user.get("stats", {})

        # Safely get posts and comments, converting to int if needed
        total_posts = stats.get("total_posts", 0)
        total_comments = stats.get("total_comments", 0)

        # Handle string values
        if isinstance(total_posts, str):
            total_posts = int(total_posts)
        if isinstance(total_comments, str):
            total_comments = int(total_comments)

        # Apply tier logic
        if total_posts > 100 and total_comments > 300:
            return "Gold"
        elif total_posts > 50:
            return "Silver"
        else:
            return "Bronze"

    except (ValueError, TypeError) as exc:
        logger.warning(
            "User %s: Error calculating tier, defaulting to Bronze: %s", user.get("id"), exc
        )
    return "Bronze"


def load_user_data(file_path: str) -> list[dict[str, Any]]:
    """Load user data from JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of user dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with path.open("r") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object with a 'users' key")

    users_obj = data.get("users")
    if not isinstance(users_obj, list):
        raise ValueError("'users' must be a list")

    return cast(list[dict[str, Any]], users_obj)


def main():
    """
    Demonstrate the transformation function with the provided user_data.json.
    """
    try:
        # Load the user data
        logger.info("Loading user data from user_data.json...")
        users = load_user_data("user_data.json")
        logger.info(f"Loaded {len(users)} users")

        # Transform and enrich the users
        logger.info("Transforming and enriching user data...")
        transformed_users = transform_and_enrich_users(users)

        # Print the results
        print("\n" + "=" * 60)
        print("TRANSFORMED AND ENRICHED USER DATA")
        print("=" * 60 + "\n")

        for user in transformed_users:
            print(f"User ID: {user.get('id')} ({type(user.get('id')).__name__})")
            print(f"  Name: {user.get('first_name')} {user.get('last_name')}")
            print(f"  Account Tier: {user.get('account_tier')}")

            contact = user.get("contact", {})
            print(f"  Email: {contact.get('email')}")
            print(f"  Email Provider: {contact.get('email_provider', 'N/A')}")

            stats = user.get("stats", {})
            age = stats.get("age")
            print(f"  Age: {age} ({type(age).__name__ if age is not None else 'None'})")
            print(f"  Posts: {stats.get('total_posts')}")
            print(f"  Comments: {stats.get('total_comments')}")
            print("-" * 40)

        # Also output as formatted JSON
        print("\nComplete JSON output:")
        print(json.dumps(transformed_users, indent=2))

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
    except json.JSONDecodeError as exc:
        logger.error("JSON parsing error: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unexpected error: %s", exc)


if __name__ == "__main__":
    main()
