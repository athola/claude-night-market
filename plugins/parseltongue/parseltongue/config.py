"""Configuration utilities for parseltongue."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class ConfigLoader:
    """Load and validate configuration files."""

    def load_config(self, path: Path) -> dict[str, Any]:
        """Load configuration from a JSON file.

        Args:
            path: Path to the configuration file

        Returns:
            Parsed configuration dictionary

        Raises:
            json.JSONDecodeError: If JSON is malformed
            ValueError: If configuration is invalid
        """
        text = path.read_text()
        data = json.loads(text)
        if not isinstance(data, dict):
            msg = "Configuration must be a JSON object"
            raise ValueError(msg)

        # Validate known field types
        if "python_version" in data and not isinstance(data["python_version"], str):
            msg = (
                "python_version must be a string, "
                f"got {type(data['python_version']).__name__}"
            )
            raise ValueError(msg)

        return data
