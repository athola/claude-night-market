"""Resolve where a plugin's runtime data lives.

Shipped assets and user data have different lifetimes and belong in
different places. Assets ship with a version and are read-only, so
deriving their path from ``__file__`` is correct. User data accumulates
across versions, and deriving it the same way is a slow data-loss bug:
hooks execute from ``~/.claude/plugins/cache/<marketplace>/<plugin>/
<version>/``, so each update starts a fresh tree whose predecessor
nobody reads again.

Issue #661 measured the cost in memory-palace, the one plugin writing
user content at runtime: 200 staged captures stranded on the reporting
machine, 1,470 and 2,491 on the machine that fixed it, all of them
``status: pending_review`` and so awaiting curation at the moment they
were orphaned.

The audit that followed is the reason this module is worth its own file.
Ten hook files across seven plugins matched the pattern
``Path(__file__).resolve().parent.parent``, and five of those plugins
turned out to be correct: leyline reads a shipped blocklist, scribe and
gauntlet read tracked data files, abstract writes to
``~/.claude/skills/``, and tome and gauntlet write under the project's
own ``cwd``. Meanwhile two genuine instances were nowhere in that list
(minister's initiative tracker, oracle's model directory). Matching the
shape finds code that looks like the bug. Only asking what writes finds
the bug, so the distinction is recorded once, here, rather than
rediscovered per plugin.

Precedence:

1. A plugin's own named override, when it passes one. Relocating a
   single plugin's data must not move every plugin's.
2. ``CLAUDE_PLUGIN_DATA``. Claude Code 2.1.78+ provisions
   ``plugins/data/<plugin>-<marketplace>/`` per plugin and names it
   here, so when it is present it is authoritative.
3. Derivation from the install path, which reproduces the same location
   for hosts that do not set the variable. Agreeing with the variable
   matters: if the two disagreed, upgrading the host would silently
   relocate live data.
4. The plugin root unchanged, which is what keeps a source checkout and
   its tests reading their own fixtures instead of the operator's data.

Note on ADR-0009: its text shows ``${CLAUDE_PLUGIN_DATA}/<plugin-name>/``,
which does not match the observed layout -- the variable is already
per-plugin, as oracle's provisioner has assumed since 2.1.78. This
module implements the observed behavior. The ADR text needs a
correction, which is a documentation change rather than a code one.

Nothing here moves data. Recovering an already-stranded tree merges
someone's queue into their live one, which is a decision for the
operator; memory-palace's ``scripts/migrate_data_root.py`` makes that an
explicit step.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Set per plugin by Claude Code 2.1.78+.
HOST_ENV_VAR = "CLAUDE_PLUGIN_DATA"

#: ``<plugins>/cache/<marketplace>/<plugin>/<version>`` is five segments
#: deep, so a shorter path cannot be an install and is not treated as one.
_INSTALL_DEPTH = 4


def plugin_data_dir(plugin_root: Path, *, env_override: str | None = None) -> Path:
    """Return the directory holding this plugin's data across versions.

    Args:
        plugin_root: The versioned root a hook derives from ``__file__``.
        env_override: Optional environment variable naming a
            plugin-specific location, checked before the host's.

    Returns:
        The resolved root. When ``plugin_root`` sits inside an install
        tree this is the version-independent sibling; otherwise it is
        ``plugin_root`` unchanged, so a checkout keeps its own tree.
    """
    if env_override:
        override = os.environ.get(env_override)
        if override:
            return Path(override)

    # An exported-but-empty variable is indistinguishable from an unset
    # one, and Path("") is the current directory -- a plausible-looking
    # answer that would scatter data wherever the hook happened to run.
    host = os.environ.get(HOST_ENV_VAR)
    if host:
        return Path(host)

    installed = _install_layout(plugin_root)
    if installed is None:
        return plugin_root

    plugins_dir, plugin, marketplace = installed
    return plugins_dir / "data" / f"{plugin}-{marketplace}"


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


__all__ = ["HOST_ENV_VAR", "plugin_data_dir"]
