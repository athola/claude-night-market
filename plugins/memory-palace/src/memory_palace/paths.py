"""Resolve where this plugin's runtime data lives.

Shipped assets and user data have different lifetimes and belong in
different places. Assets ship with a version and are read-only, so
deriving them from ``__file__`` is correct. User data accumulates
across versions, so deriving it the same way is a slow data-loss bug:
hooks execute from ``~/.claude/plugins/cache/<marketplace>/<plugin>/
<version>/``, and each update starts a fresh tree whose predecessor
nobody reads again.

The cost has been measured twice. Issue #661 reported 200 staged
captures stranded under 1.9.16 on the machine that filed it; the
machine this was implemented on held 1,470 under 1.9.17 and 2,491
under 1.9.18. Every one carried ``status: pending_review``, so each was
an item in somebody's curation queue. Meanwhile
``~/.claude/plugins/data/memory-palace-claude-night-market/``, which
Claude Code provisions for exactly this, held nothing.

Why the persistent root contains ``data/`` rather than being it. Index
entries record ``stored_at`` relative to the plugin root and readers
resolve it as ``root / stored_at`` (``index_promoter``,
``index_analytics``). Keeping one level above ``data/`` means those
strings stay ``data/staging/<file>.md`` in both layouts, so no index
needs rewriting and migration is a directory move rather than a schema
change.

Nothing here moves data. Recovering an already-stranded tree merges
someone's pending review queue into their live one, which is a curation
decision for the operator; ``scripts/migrate_data_root.py`` makes it an
explicit step.
"""

from __future__ import annotations

import os
from pathlib import Path

#: An operator moving a palace, or the migration tool pointing at a
#: destination, needs one lever that does not depend on where the code
#: happens to be installed. It names the root that *contains* ``data/``.
ENV_OVERRIDE = "MEMORY_PALACE_DATA_DIR"

#: ``<plugins>/cache/<marketplace>/<plugin>/<version>`` is five segments
#: deep, so a shorter path cannot be an install and is not treated as one.
_INSTALL_DEPTH = 4


def persistent_root(plugin_root: Path) -> Path:
    """Return the root holding this plugin's user data across versions.

    ``plugin_root`` is the versioned root a hook derives from
    ``__file__``. When it sits inside an install tree the result is the
    version-independent sibling; otherwise it is ``plugin_root``
    unchanged, so a source checkout and its tests keep reading their own
    fixtures instead of the operator's real palace.
    """
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override)

    installed = _install_layout(plugin_root)
    if installed is None:
        return plugin_root

    plugins_dir, plugin, marketplace = installed
    return plugins_dir / "data" / f"{plugin}-{marketplace}"


def user_data_dir(plugin_root: Path) -> Path:
    """Return the ``data/`` directory under the persistent root."""
    return persistent_root(plugin_root) / "data"


def _install_layout(plugin_root: Path) -> tuple[Path, str, str] | None:
    """Match ``<plugins>/cache/<marketplace>/<plugin>/<version>``.

    Returns the plugins directory and the two names that form the data
    directory, or None when the path is not an install. Both anchor
    directories are checked by name: a path merely containing "cache"
    would otherwise donate whatever sits above it as a marketplace.
    """
    parents = plugin_root.parents
    if len(parents) < _INSTALL_DEPTH:
        return None

    plugin_dir, marketplace_dir, cache_dir, plugins_dir = parents[:_INSTALL_DEPTH]
    if cache_dir.name != "cache" or plugins_dir.name != "plugins":
        return None

    return plugins_dir, plugin_dir.name, marketplace_dir.name
