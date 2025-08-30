#!/usr/bin/env python3
"""Refactored process_records implementation (reference model).

Processes user records from various sources applying validation and transformation
rules configured via a YAML file.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any

import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required fields."""


class DataValidationError(Exception):
    """Raised when data validation fails."""


class UserProcessor:
    """Processes user records based on configuration rules."""

    def __init__(self, config_path: str):
        """Initialize the processor with configuration.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            ConfigurationError: If config file is invalid or missing
        """
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.data_path = self._determine_data_path()
        self.records: list[dict[str, Any]] = []

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load and validate configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary containing configuration

        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        try:
            path = Path(config_path)
            if not path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {config_path}"
                )

            with path.open("r") as file:
                config = yaml.safe_load(file)

            # Validate required configuration sections
            required_sections = ["paths", "validation_rules"]
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(
                        f"Missing required config section: {section}"
                    )

            return config

        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Invalid YAML in configuration: {exc}") from exc
        except Exception as exc:  # pragma: no cover - unexpected edge path
            raise ConfigurationError(f"Error loading configuration: {exc}") from exc

    def _determine_data_path(self) -> Path:
        """Determine which data path to use based on configuration."""
        use_legacy_value = self.config.get("use_legacy_paths", False)
        if isinstance(use_legacy_value, bool):
            use_legacy = use_legacy_value
        else:
            use_legacy = str(use_legacy_value).lower() == "true"

        path_key = "legacy_data_source" if use_legacy else "data_source"
        data_path = self.config["paths"].get(path_key)
        if not data_path:
            raise ConfigurationError(f"Missing data path: {path_key}")
        return Path(data_path)

    def load_data(self) -> None:
        """Load user data from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        try:
            with self.data_path.open("r") as file:
                data = json.load(file)
            if "users" not in data:
                raise DataValidationError("JSON file missing 'users' key")
            self.records = data["users"]
            self.logger.info(
                f"Loaded {len(self.records)} records from {self.data_path}"
            )
        except json.JSONDecodeError as exc:
            raise DataValidationError(f"Invalid JSON in data file: {exc}") from exc

    def _validate_record(self, record: dict[str, Any]) -> bool:
        """Validate a single record against configuration rules."""
        try:
            rules = self.config.get("validation_rules", {})
            min_age = int(rules.get("min_age_years", 0))
            min_posts = int(rules.get("minimum_posts", 0))
            user_age = record.get("stats", {}).get("age", 0)
            user_posts = record.get("stats", {}).get("total_posts", 0)
            if isinstance(user_age, str):
                user_age = int(user_age)
            if isinstance(user_posts, str):
                user_posts = int(user_posts)
            required_fields = rules.get("required_fields", [])
            for field in required_fields:
                if not self._check_nested_field(record, field):
                    self.logger.debug(
                        f"Record missing required field: {field}"
                    )
                    return False
            return user_age >= min_age and user_posts >= min_posts
        except (ValueError, TypeError) as e:
            self.logger.warning(
                f"Validation error for record {record.get('id')}: {e}"
            )
            return False

    def _check_nested_field(
        self, record: dict[str, Any], field_path: str
    ) -> bool:
        """Check if a nested field exists and is not None."""
        current = record
        for part in field_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return current is not None

    def _transform_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Transform a record to the output format."""
        try:
            user_id = record.get("id", "unknown")
            first_name = record.get("first_name", "")
            last_name = record.get("last_name", "")
            email = record.get("contact", {}).get("email", "")
            last_login = record.get("metadata", {}).get("last_login", "")
            return {
                "user_id": f"user_{user_id}",
                "full_name": f"{first_name} {last_name}".strip(),
                "email": email or "no-email@example.com",
                "status": self._determine_status(last_login),
                "processed_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(
                f"Error transforming record {record.get('id')}: {e}"
            )
            raise

    def _determine_status(self, last_login_str: str) -> str:
        """Determine user status based on last login date."""
        if not last_login_str:
            return "unknown"
        try:
            last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d")
            days_since_login = (datetime.now() - last_login_date).days
            if days_since_login < 30:
                return "active"
            if days_since_login < 90:
                return "inactive"
            return "archived"
        except ValueError as e:
            self.logger.warning(
                f"Invalid date format '{last_login_str}': {e}"
            )
            return "unknown"

    def process_records(
        self, filter_by_country: str | None = None
    ) -> list[dict[str, Any]]:
        """Process all loaded records with filtering and validation."""
        if not self.records:
            self.logger.warning("No records to process")
            return []
        processed: list[dict[str, Any]] = []
        for record in self.records:
            if filter_by_country:
                country = record.get("profile", {}).get("country")
                if country != filter_by_country:
                    continue
            if not self._validate_record(record):
                self.logger.debug(
                    f"Record {record.get('id')} failed validation"
                )
                continue
            try:
                transformed = self._transform_record(record)
                processed.append(transformed)
            except Exception as e:  # pragma: no cover - defensive
                self.logger.error(
                    f"Failed to transform record {record.get('id')}: {e}"
                )
                continue
        self.logger.info(f"Processed {len(processed)} records successfully")
        return processed


def main() -> None:
    """CLI entry point."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    try:
        processor = UserProcessor(config_file)
        processor.load_data()
        results = processor.process_records()
        print("Processed Records:")
        print(json.dumps(results, indent=2))
    except (ConfigurationError, FileNotFoundError, DataValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # pragma: no cover - defensive
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover - CLI guard
    main()
