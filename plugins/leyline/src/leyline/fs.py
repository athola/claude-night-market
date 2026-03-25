"""File system utilities for walking source trees.

This module provides directory-walking helpers with sensible defaults
for skipping build artifacts and filtering to relevant source extensions.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

# Overhead tokens per file (for file path and metadata)
FILE_OVERHEAD_TOKENS = 6

# Directories to skip when walking file trees
SKIP_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        "node_modules",
        ".git",
        "venv",
        ".venv",
        "dist",
        "build",
        ".pytest_cache",
    }
)

# File extensions to include when walking directories
SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".rs",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    }
)


def iter_source_files(
    root_dir: Path,
    extensions: frozenset[str] | None = None,
    skip_dirs: frozenset[str] | None = None,
) -> Iterable[Path]:
    """Iterate over source files in a directory, skipping build artifacts.

    Args:
        root_dir: Directory path to walk.
        extensions: File extensions to include. Defaults to SOURCE_EXTENSIONS.
        skip_dirs: Directory names to skip. Defaults to SKIP_DIRS.

    Yields:
        Path objects for each matching source file.

    """
    effective_extensions = extensions if extensions is not None else SOURCE_EXTENSIONS
    effective_skip = skip_dirs if skip_dirs is not None else SKIP_DIRS

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in effective_skip]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in effective_extensions:
                yield file_path
