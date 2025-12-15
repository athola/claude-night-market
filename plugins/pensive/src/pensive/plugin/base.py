"""Base plugin class for pensive."""

from __future__ import annotations

from typing import Any


class PensivePlugin:
    """Base class for pensive plugins."""

    name: str = "base"
    version: str = "1.0.0"

    def __init__(self, config: Any = None) -> None:
        """Initialize plugin."""
        self.config = config or {}

    def initialize(self) -> None:
        """Initialize the plugin."""

    def analyze(self, context: Any) -> dict[str, Any]:
        """Run analysis."""
        return {}

    def cleanup(self) -> None:
        """Cleanup resources."""
