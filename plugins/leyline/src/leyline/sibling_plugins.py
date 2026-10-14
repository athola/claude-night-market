"""Locate a sibling night-market plugin from any file inside a plugin.

Two layouts hold the plugins side by side. The repository checkout keeps
them in ``plugins/<name>/``. Claude Code installs them as
``cache/<marketplace>/<name>/<version>/``. A fixed ``parents[2] / name``
only matches the first, so code that reached another plugin that way
found nothing in a real install and switched its feature off.

Standard library only and Python 3.9 compatible: hooks and scripts run
under the operator's bare ``python3``, and plugins that cannot import
leyline receive this module as a vendored copy (``scripts/sync_vendored.py``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_MANIFEST_DIR = ".claude-plugin"


def _plugin_root(start: Path) -> Path | None:
    """Nearest ancestor that holds a ``.claude-plugin`` manifest directory."""
    for candidate in (start, *start.parents):
        if (candidate / _MANIFEST_DIR).is_dir():
            return candidate
    return None


_LEADING_VERSION = re.compile(r"\d+(?:\.\d+)*")


def _version_key(path: Path) -> tuple[tuple[int, ...], bool, str]:
    """Order directory names as versions.

    ``1.10.0`` sorts after ``1.9.21``, and ``2.0.0-rc1`` after both but
    before ``2.0.0``. A name with no leading version (``latest``, a commit
    hash) sorts before every version, and such names sort by name.
    """
    match = _LEADING_VERSION.match(path.name)
    if match is None:
        return ((), False, path.name)
    numbers = tuple(int(part) for part in match.group().split("."))
    return (numbers, match.end() == len(path.name), path.name)


def sibling_plugin_dir(this_file: str | Path, name: str) -> Path | None:
    """Return plugin ``name`` installed beside the plugin holding ``this_file``.

    The repository layout is tried first, then the newest installed version
    in the plugin cache. Returns None when the sibling is not installed, so
    the caller can turn its feature off as ADR-0001 requires.
    """
    root = _plugin_root(Path(this_file).resolve())
    if root is None:
        return None
    beside = root.parent / name
    if (beside / _MANIFEST_DIR).is_dir():
        return beside
    versions = [
        d for d in (root.parent.parent / name).glob("*") if (d / _MANIFEST_DIR).is_dir()
    ]
    return max(versions, key=_version_key) if versions else None


def add_sibling_src_to_path(anchor_file: str | Path, plugin_name: str) -> Path:
    """Put ``<plugin_name>/src`` first on ``sys.path`` and return it.

    When the sibling is not installed, the path is still inserted, beside
    the caller's plugin, so the caller's ``except ImportError`` branch is
    what turns the feature off. The fallback follows the anchor's plugin
    root (or its nearest ``plugins`` ancestor) rather than a fixed
    ``parents[N]``, which scripts and ``src/<pkg>`` modules disagree on.
    """
    anchor = Path(anchor_file).resolve()
    sibling = sibling_plugin_dir(anchor, plugin_name)
    if sibling is None:
        root = _plugin_root(anchor)
        if root is not None:
            container = root.parent
        else:
            container = next(
                (p for p in anchor.parents if p.name == "plugins"), anchor.parent
            )
        sibling = container / plugin_name
    src = sibling / "src"
    sys.path.insert(0, str(src))
    return src
