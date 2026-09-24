"""Abstract plugin - meta-skills infrastructure for Claude Code.

Nothing here is imported eagerly. ``base`` reaches PyYAML through
``frontmatter``, and importing any submodule executes this file first,
so an eager re-export here put that dependency in front of every leaf
module. Hooks import ``abstract.paths`` and run under whatever
``python3`` the operator's PATH resolves, which carries the standard
library and nothing else.

Resolving each export on first attribute access keeps the stdlib-only
modules reachable on their own. ``from abstract import AbstractScript``
still works wherever the dependency is present.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import AbstractScript, find_markdown_files, has_frontmatter_file
    from .cli_framework import AbstractCLI, CLIResult, OutputFormatter, cli_main
    from .config import AbstractConfig, ConfigFactory
    from .errors import ErrorHandler, ErrorSeverity, ToolError
    from .frontmatter import FrontmatterProcessor, FrontmatterResult
    from .tasks_manager_base import TasksManager, TasksManagerConfig
    from .tokens import TokenAnalyzer, estimate_text_tokens, estimate_tokens

__version__ = "1.9.21"

__all__ = [
    "AbstractCLI",
    "AbstractConfig",
    "AbstractScript",
    "CLIResult",
    "ConfigFactory",
    "ErrorHandler",
    "ErrorSeverity",
    "FrontmatterProcessor",
    "FrontmatterResult",
    "OutputFormatter",
    "TasksManager",
    "TasksManagerConfig",
    "TokenAnalyzer",
    "ToolError",
    "cli_main",
    "estimate_text_tokens",
    "estimate_tokens",
    "find_markdown_files",
    "has_frontmatter_file",
]

#: The module each exported name is resolved from on first access.
_EXPORT_SOURCES = {
    "AbstractCLI": ".cli_framework",
    "AbstractConfig": ".config",
    "AbstractScript": ".base",
    "CLIResult": ".cli_framework",
    "ConfigFactory": ".config",
    "ErrorHandler": ".errors",
    "ErrorSeverity": ".errors",
    "FrontmatterProcessor": ".frontmatter",
    "FrontmatterResult": ".frontmatter",
    "OutputFormatter": ".cli_framework",
    "TasksManager": ".tasks_manager_base",
    "TasksManagerConfig": ".tasks_manager_base",
    "TokenAnalyzer": ".tokens",
    "ToolError": ".errors",
    "cli_main": ".cli_framework",
    "estimate_text_tokens": ".tokens",
    "estimate_tokens": ".tokens",
    "find_markdown_files": ".base",
    "has_frontmatter_file": ".base",
}


def __getattr__(name: str) -> Any:
    """Resolve an export from the module that defines it."""
    source = _EXPORT_SOURCES.get(name)
    if source is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(source, __name__), name)


def __dir__() -> list[str]:
    """List the exports alongside this module's own globals."""
    return sorted({*globals(), *__all__})
