"""Root pytest configuration for the claude-night-market ecosystem.

Each plugin sets ``pythonpath = [".", "src"]`` in its own ``pyproject.toml``.
That file is the rootdir when pytest runs inside the plugin, which is what
makes ``import pensive`` resolve there.

Hand pytest two plugin paths from the repo root and only one ini file wins:
the root ``pyproject.toml``, which has no ``pythonpath``. Every plugin test
importing its own package then dies at collection with ``ModuleNotFoundError``,
so the natural command for "test the two plugins I touched" was the one command
that could not work. This module puts each ``plugins/*/src`` on ``sys.path`` so
the import resolves whichever rootdir pytest picked.

What this does NOT do: apply each plugin's ``addopts``. Coverage flags and the
85% threshold live in the plugin's own config and are ignored under a
root-level run. A green root run is an import-and-assertion check, not a gate.
``make test`` (``scripts/run-plugin-tests.sh``, one pytest process per plugin)
remains the gate of record.

Usage:
    make test                          # all plugins, gated
    cd plugins/pensive && uv run pytest # one plugin, gated
    uv run pytest plugins/a/tests plugins/b/tests  # quick cross-plugin, ungated
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent


def _add_plugin_src_dirs_to_sys_path() -> None:
    """Put every ``plugins/*/src`` on ``sys.path``.

    Globbed rather than listed so a new plugin is picked up without editing
    this file. Every plugin's src holds exactly one top-level package named
    after the plugin, so there is nothing here to shadow anything else.

    Only ``src`` goes on the path, never the plugin root. Plugin roots hold
    ``scripts/`` and ``hooks/`` directories whose names repeat across plugins,
    and putting those on a shared path is what makes one plugin's ``scripts``
    import resolve to another's.
    """
    for src_dir in sorted(REPO_ROOT.glob("plugins/*/src")):
        if not src_dir.is_dir():
            continue
        entry = str(src_dir)
        if entry not in sys.path:
            sys.path.insert(0, entry)


_add_plugin_src_dirs_to_sys_path()


def pytest_configure(config) -> None:
    """Configure pytest for root-level execution.

    Adds custom markers and configures collection to avoid conflicts.
    """
    # Register ecosystem-wide markers
    config.addinivalue_line(
        "markers", "plugin(name): Mark test as belonging to a specific plugin"
    )
    config.addinivalue_line(
        "markers", "ecosystem: Mark test as ecosystem-level integration test"
    )


def pytest_collection_modifyitems(config, items) -> None:
    """Modify collected test items.

    Adds plugin markers based on test location for filtering.
    """
    for item in items:
        # Extract plugin name from path
        path_parts = Path(item.fspath).parts
        if "plugins" in path_parts:
            try:
                plugin_idx = path_parts.index("plugins")
                if plugin_idx + 1 < len(path_parts):
                    plugin_name = path_parts[plugin_idx + 1]
                    item.add_marker(pytest.mark.plugin(plugin_name))
            except (ValueError, IndexError):
                pass


# Ignore patterns for plugin-specific conftest files when running from root
collect_ignore_glob = [
    # Ignore virtual environment test files
    "**/.*venv/**",
    "**/.venv/**",
    # Ignore cache directories
    "**/.uv-cache/**",
    "**/__pycache__/**",
    # Ignore worktrees (separate git worktree directories)
    ".worktrees/**",
]


def pytest_ignore_collect(collection_path: Path, config) -> bool | None:
    """Ignore certain paths during collection.

    Returns True to ignore, None to let pytest decide.
    """
    path_str = str(collection_path)

    # Always ignore virtual environments and caches
    ignore_patterns = [".venv", ".uv-cache", "__pycache__", ".worktrees"]
    if any(pattern in path_str for pattern in ignore_patterns):
        return True

    return None
