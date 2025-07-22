"""
Configuration manager for AWS Assistant.
Handles loading and validating configuration settings.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """Manages configuration settings for the AWS Assistant."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}"
                )

            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)

            if not config:
                raise ValueError("Configuration file is empty")

            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

    def _validate_config(self) -> None:
        """Validate required configuration sections."""
        required_sections = ["app", "openai", "aws", "logging", "agent", "services"]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'openai.model')."""
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return self.config.get("openai", {})

    def get_aws_config(self) -> Dict[str, Any]:
        """Get AWS configuration."""
        return self.config.get("aws", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get("logging", {})

    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config.get("agent", {})

    def get_services_config(self) -> Dict[str, Any]:
        """Get services configuration."""
        return self.config.get("services", {})

    def is_service_enabled(self, service: str) -> bool:
        """Check if a specific AWS service is enabled."""
        services = self.get_services_config()
        return services.get(service, False)

    def validate_environment(self) -> None:
        """Validate required environment variables."""
        missing_vars = []

        if not os.environ.get("OPENAI_API_KEY"):
            missing_vars.append("OPENAI_API_KEY")

        if not (
            os.environ.get("AWS_ACCESS_KEY_ID")
            or os.environ.get("AWS_PROFILE")
            or Path.home() / ".aws" / "credentials"
        ):
            missing_vars.append(
                "AWS credentials (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or AWS_PROFILE)"
            )

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )


config = ConfigManager()
