"""Plugin loader for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PluginLoader:
    """Loads and manages pensive plugins."""

    def __init__(self) -> None:
        """Initialize plugin loader."""
        self._plugins: dict[str, Any] = {}

    def load(self, _name: str) -> Any:
        """Load a plugin by name."""
        return None

    def register(self, name: str, plugin: Any) -> None:
        """Register a plugin."""
        self._plugins[name] = plugin

    def get_all(self) -> dict[str, Any]:
        """Get all loaded plugins."""
        return self._plugins

    def discover_plugins(self, path: Path | str) -> list[dict[str, Any]]:
        """Discover plugins in a directory.

        Args:
            path: Directory path to search for plugins

        Returns:
            List of discovered plugin info dicts (empty if path doesn't exist)
        """
        path = Path(path)

        # Return empty list for non-existent paths (graceful handling)
        if not path.exists():
            return []

        if not path.is_dir():
            return []

        # Look for plugin directories (contain plugin.json or __init__.py)
        plugins: list[dict[str, Any]] = []
        try:
            for item in path.iterdir():
                if item.is_dir():
                    plugin_json = item / "plugin.json"
                    init_py = item / "__init__.py"
                    if plugin_json.exists() or init_py.exists():
                        plugins.append(
                            {
                                "name": item.name,
                                "path": str(item),
                                "type": "json" if plugin_json.exists() else "python",
                            }
                        )
        except PermissionError:
            # Handle permission errors gracefully
            return []

        return plugins
