#!/usr/bin/env python3
"""Base class for Abstract scripts with common functionality.

Centralize import handling, file discovery, and frontmatter operations.

This module offers two usage patterns:

1. Class-based (for complex scripts needing state):
   ```python
   from abstract.base import AbstractScript

   class MyScript(AbstractScript):
       def run(self):
           files = self.find_markdown_files(Path("."))
           ...
   ```

2. Function-based (for simple scripts):
   ```python
   from abstract.base import setup_imports, has_frontmatter_file, find_markdown_files

   setup_imports()  # Call once at module load
   files = find_markdown_files(Path("skills"))
   ```
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

# Import implementations
from .errors import ErrorHandler
from .frontmatter import FrontmatterProcessor
from .utils import find_project_root, load_config_with_defaults

if TYPE_CHECKING:
    from .config import AbstractConfig

# =============================================================================
# Module-level helper functions (for simple scripts)
# =============================================================================


def setup_imports() -> None:
    """Set up import paths for scripts run from any location.

    This is a no-op kept for backwards compatibility.
    All imports are now handled at the module level.
    """


def has_frontmatter_file(file_path: Path) -> bool:
    """Check if a file has valid YAML frontmatter.

    Args:
        file_path: Path to the markdown file.

    Returns:
        True if the file has valid frontmatter, False otherwise.

    """
    try:
        content = file_path.read_text(encoding="utf-8")
        return FrontmatterProcessor.has_frontmatter(content)
    except (OSError, UnicodeDecodeError):
        return False


def find_markdown_files(directory: Path) -> list[Path]:
    """Find all markdown files in a directory recursively.

    Args:
        directory: Directory to search.

    Returns:
        List of paths to markdown files, sorted by path.

    """
    if not directory.exists():
        return []
    return sorted(directory.rglob("*.md"))


# =============================================================================
# AbstractScript class (for complex scripts needing state)
# =============================================================================


class AbstractScript:
    """Base class for Abstract scripts with common functionality.

    Centralizes import handling, markdown file discovery, frontmatter checking,
    and configuration setup for scripts that can run from any location.
    """

    def __init__(self, script_name: str) -> None:
        """Initialize the script with common setup.

        Args:
            script_name: Name of the script for logging and error reporting.

        """
        self.script_name = script_name
        self._setup_imports()

        # Lazy-loaded attributes
        self._config: AbstractConfig | None = None
        self._error_handler: ErrorHandler | None = None

    def _setup_imports(self) -> None:
        """Set up import paths for running from any location.

        This is a no-op kept for backwards compatibility.
        All imports are now handled at the module level.
        """

    def find_markdown_files(self, directory: Path) -> list[Path]:
        """Find all markdown files in a directory recursively.

        Args:
            directory: Directory to search.

        Returns:
            List of paths to markdown files, sorted by path.

        """
        if not directory.exists():
            return []

        md_files = list(directory.rglob("*.md"))
        return sorted(md_files)

    def check_frontmatter_exists(self, content: str) -> bool:
        """Check if content has valid frontmatter delimiters.

        Delegates to FrontmatterProcessor.has_frontmatter() for consistent behavior.

        Args:
            content: File content to check.

        Returns:
            True if valid frontmatter exists, False otherwise.

        """
        return FrontmatterProcessor.has_frontmatter(content)

    def extract_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract frontmatter and body from content.

        Delegates to FrontmatterProcessor.extract_raw() for consistent behavior.

        Args:
            content: Full file content.

        Returns:
            Tuple of (frontmatter, body). Frontmatter includes delimiters.
            Returns ("", content) if no frontmatter found.

        """
        return FrontmatterProcessor.extract_raw(content)

    @property
    def config(self) -> "AbstractConfig":
        """Get the configuration, loading it lazily.

        Returns:
            AbstractConfig instance.

        """
        if self._config is None:
            self._config = load_config_with_defaults()
        return self._config

    @config.setter
    def config(self, value: "AbstractConfig") -> None:
        """Set the configuration manually.

        Args:
            value: AbstractConfig instance to use.

        """
        self._config = value

    @property
    def error_handler(self) -> "ErrorHandler":
        """Get the error handler, creating it lazily.

        Returns:
            ErrorHandler instance.

        """
        if self._error_handler is None:
            self._error_handler = ErrorHandler(self.script_name)
        return self._error_handler

    @error_handler.setter
    def error_handler(self, value: "ErrorHandler") -> None:
        """Set the error handler manually.

        Args:
            value: ErrorHandler instance to use.

        """
        self._error_handler = value

    def find_project_root(self, start_path: Path | None = None) -> Path:
        """Find the project root directory.

        Args:
            start_path: Path to start searching from. Defaults to cwd.

        Returns:
            Path to project root directory.

        """
        return find_project_root(start_path or Path.cwd())

    def read_file_safe(self, file_path: Path) -> str | None:
        """Read a file safely, returning None on error.

        Args:
            file_path: Path to file to read.

        Returns:
            File content or None if read fails.

        """
        try:
            return file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
