"""Shared constants for plugin update scripts."""

from __future__ import annotations

# Directories to exclude from recursive scans.
# Used by update_versions.py and update_plugin_registrations.py
# to skip cache, temp, build, and VCS directories.
CACHE_EXCLUDES: frozenset[str] = frozenset(
    {
        # Python
        ".venv",
        "venv",
        ".virtualenv",
        "virtualenv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
        ".uv-cache",
        # JavaScript/Node
        "node_modules",
        ".npm",
        ".yarn",
        ".pnp",
        ".cache",
        # Rust
        "target",
        ".cargo",
        ".rustup",
        # Build artifacts
        "dist",
        "build",
        "_build",
        "out",
        # Version control
        ".git",
        ".hg",
        ".svn",
        ".worktrees",
        # IDEs and editors
        ".vscode",
        ".idea",
        ".vs",
        # OS (note: .DS_Store and Thumbs.db are files, not dirs,
        # so they won't match with `in path.parts` checking)
    }
)
