"""Plugin loader for pensive."""

from __future__ import annotations

from typing import Any


class PluginLoader:
    """Loads and manages pensive plugins."""

    def __init__(self) -> None:
        """Initialize plugin loader."""
        self._plugins: dict[str, Any] = {}

    def load(self, name: str) -> Any:
        """Load a plugin by name."""
        return None

    def register(self, name: str, plugin: Any) -> None:
        """Register a plugin."""
        self._plugins[name] = plugin

    def get_all(self) -> dict[str, Any]:
        """Get all loaded plugins."""
        return self._plugins
