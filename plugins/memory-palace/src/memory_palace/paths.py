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

import importlib
import os
import sys
from pathlib import Path
from typing import Any

#: An operator moving a palace, or the migration tool pointing at a
#: destination, needs one lever that does not depend on where the code
#: happens to be installed. It names the root that *contains* ``data/``.
ENV_OVERRIDE = "MEMORY_PALACE_DATA_DIR"

#: ``<plugins>/cache/<marketplace>/<plugin>/<version>`` is five segments
#: deep, so a shorter path cannot be an install and is not treated as one.
_INSTALL_DEPTH = 4


def _leyline_src(plugin_root: Path) -> Path | None:
    """Locate leyline's ``src`` in either layout, or None.

    A checkout puts sibling plugins next to each other
    (``plugins/leyline/src``). An install nests them under a version
    (``plugins/cache/<marketplace>/leyline/<version>/src``), which is why
    ``leyline.bootstrap.add_plugin_src_to_path`` cannot be used here: it
    resolves the checkout layout only, and its own docstring notes it
    cannot bootstrap leyline itself. That paradox is why this handful of
    lines is duplicated rather than shared.

    Without this, the guarded import below would always land in its
    except-branch inside an install, which is precisely where the bug
    being fixed lives -- the hoist would move code without moving
    behavior.
    """
    sibling = plugin_root.parent / "leyline" / "src"
    if sibling.is_dir():
        return sibling

    versions = sorted(
        (plugin_root.parent.parent / "leyline").glob("*/src"),
        key=lambda path: _numeric_version(path.parent.name),
    )
    return versions[-1] if versions else None


def _numeric_version(version: str) -> tuple[int, ...]:
    """Order versions numerically so 1.9.9 ranks below 1.9.17."""
    return tuple(int(part) if part.isdigit() else -1 for part in version.split("."))


def _load_shared_resolver() -> Any | None:
    """Return leyline's ``plugin_data_dir``, or None when unavailable.

    The rule is shared because the audit behind issue #661 found the same
    write shape in minister and oracle, and five false positives
    elsewhere. Stating the distinction once is the point; the local copy
    below exists only so a host without leyline still resolves, and
    ``TestFallbackMatchesLeyline`` asserts the two agree.
    """
    src = _leyline_src(Path(__file__).resolve().parents[2])
    if src is not None and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Loaded dynamically rather than imported at module scope: the
    # sys.path entry established just above is what makes leyline
    # reachable, and at module scope it would not exist yet.
    try:
        module = importlib.import_module("leyline.plugin_data")
    except ImportError:  # pragma: no cover - leyline genuinely absent
        return None
    return module.plugin_data_dir


def _local_plugin_data_dir(
    plugin_root: Path, *, env_override: str | None = None
) -> Path:
    """Resolve the data root without leyline. Mirrors ``plugin_data_dir``."""
    if env_override:
        override = os.environ.get(env_override)
        if override:
            return Path(override)

    # An exported-but-empty variable reads as unset, and Path("") is the
    # current directory, which would scatter captures wherever a hook ran.
    host = os.environ.get("CLAUDE_PLUGIN_DATA")
    if host:
        return Path(host)

    installed = _install_layout(plugin_root)
    if installed is None:
        return plugin_root

    plugins_dir, plugin, marketplace = installed
    return plugins_dir / "data" / f"{plugin}-{marketplace}"


def persistent_root(plugin_root: Path) -> Path:
    """Return the root holding this plugin's user data across versions.

    ``plugin_root`` is the versioned root a hook derives from
    ``__file__``. When it sits inside an install tree the result is the
    version-independent sibling; otherwise it is ``plugin_root``
    unchanged, so a source checkout and its tests keep reading their own
    fixtures instead of the operator's real palace.

    ``MEMORY_PALACE_DATA_DIR`` outranks the host's own
    ``CLAUDE_PLUGIN_DATA`` so an operator can relocate this palace
    without moving every plugin's data.
    """
    resolver = _load_shared_resolver() or _local_plugin_data_dir
    return Path(resolver(plugin_root, env_override=ENV_OVERRIDE))


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

    # Indexed one at a time rather than sliced: Path.parents only became
    # a full sequence in 3.10, and these plugins run on 3.9 in hooks. A
    # slice raises TypeError there, which no linter flags because the
    # syntax is valid at every version.
    plugin_dir = parents[0]
    marketplace_dir = parents[1]
    cache_dir = parents[2]
    plugins_dir = parents[3]
    if cache_dir.name != "cache" or plugins_dir.name != "plugins":
        return None

    return plugins_dir, plugin_dir.name, marketplace_dir.name
