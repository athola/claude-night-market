"""Configuration management for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pensive.exceptions import ConfigurationError


class Configuration:
    """Configuration class for pensive plugin."""

    def __init__(self, config_dict: dict[str, Any] | None = None) -> None:
        """Initialize configuration."""
        self._config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    @property
    def enabled_skills(self) -> list[str]:
        """Get list of enabled skills.

        Returns:
            List of skill names that are enabled
        """
        pensive_config = self._config.get("pensive", {})
        return pensive_config.get("skills", [])

    @property
    def exclude_patterns(self) -> list[str]:
        """Get list of exclude patterns.

        Returns:
            List of glob patterns to exclude from analysis
        """
        pensive_config = self._config.get("pensive", {})
        return pensive_config.get("exclude", [])

    @property
    def thresholds(self) -> dict[str, Any]:
        """Get threshold configuration.

        Returns:
            Dictionary of threshold settings
        """
        pensive_config = self._config.get("pensive", {})
        return pensive_config.get("thresholds", {})

    @property
    def output_settings(self) -> dict[str, Any]:
        """Get output configuration.

        Returns:
            Dictionary of output settings
        """
        pensive_config = self._config.get("pensive", {})
        return pensive_config.get("output", {})

    @property
    def custom_rules(self) -> list[dict[str, Any]]:
        """Get custom rules.

        Returns:
            List of custom rule definitions
        """
        return self._config.get("custom_rules", [])

    @classmethod
    def from_file(cls, path: str | Path) -> Configuration:
        """Load configuration from file."""
        path = Path(path)
        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise ConfigurationError(msg)
        try:
            with path.open() as f:
                config = yaml.safe_load(f)
            return cls(config)
        except yaml.YAMLError as e:
            msg = f"YAML syntax error in configuration: {e}"
            raise ConfigurationError(msg) from e

    @classmethod
    def load_from_file(cls, path: str | Path) -> Configuration:
        """Load configuration from file (alias for from_file)."""
        return cls.from_file(path)

    def validate(self) -> bool:
        """Validate configuration."""
        return True

    def merge(self, other: Configuration) -> Configuration:
        """Merge another configuration into this one.

        Args:
            other: Configuration to merge

        Returns:
            New Configuration with merged values
        """
        merged = {**self._config}
        for key, value in other._config.items():
            if key in merged and isinstance(merged[key], dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return Configuration(merged)
