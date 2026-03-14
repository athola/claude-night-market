"""Plugin discovery for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def discover_plugins(path: str | Path) -> list[dict[str, Any]]:
    """Discover plugins in a directory."""
    path = Path(path)
    if not path.exists() or not path.is_dir():
        return []
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
        return []
    return plugins
