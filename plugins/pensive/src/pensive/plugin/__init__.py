"""Pensive plugin module."""

from __future__ import annotations

from typing import Any

from pensive.plugin.base import run_code_review
from pensive.plugin.loader import discover_plugins


# Backward-compatible aliases
class PensivePlugin:
    """Deprecated: use run_code_review() directly."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def cleanup(self) -> None:
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def execute_review(self, repo_path: str) -> dict[str, Any]:
        return run_code_review(repo_path, self.config)

    def analyze(self, _context: Any) -> dict[str, Any]:
        return {}


class PluginLoader:
    """Deprecated: use discover_plugins() directly."""

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    def register(self, name: str, plugin: Any) -> None:
        self._plugins[name] = plugin

    def get_all(self) -> dict[str, Any]:
        return self._plugins

    def discover_plugins(self, path: str) -> list[Any]:
        return discover_plugins(path)


__all__ = ["PensivePlugin", "PluginLoader", "discover_plugins", "run_code_review"]
