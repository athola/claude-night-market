"""Abstract plugin - meta-skills infrastructure for Claude Code."""

from __future__ import annotations

from .base import AbstractScript, find_markdown_files, has_frontmatter_file
from .cli_framework import AbstractCLI, CLIResult, OutputFormatter, cli_main
from .config import AbstractConfig, ConfigFactory
from .errors import ErrorHandler, ErrorSeverity, ToolError
from .frontmatter import FrontmatterProcessor, FrontmatterResult
from .tasks_manager_base import TasksManager, TasksManagerConfig
from .tokens import TokenAnalyzer, estimate_text_tokens, estimate_tokens

__version__ = "1.6.1"

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
