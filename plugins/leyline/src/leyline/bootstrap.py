"""Cross-plugin sys.path bootstrap helper (AR-15).

Twenty-five+ scripts and hooks open-code their own
``Path(__file__).resolve().parents[N] / "<plugin>" / "src"``
discovery before importing from a sibling plugin. This module
collapses that pattern to one tested helper. Rollout is incremental:
``plugins/imbue/scripts/imbue_validator.py`` is the first adopter;
remaining sites migrate as they are touched (see
``docs/refinement/2026-05-02/04-architecture.md``).

Note: this module cannot bootstrap leyline itself -- callers
that need leyline must still place ``plugins/leyline/src`` on
sys.path with their own snippet before they can ``from
leyline.bootstrap import add_plugin_src_to_path``. Once leyline
is on the path, every secondary cross-plugin lookup uses this
helper.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path


def _find_plugins_root(start: Path) -> Path | None:
    """Walk upward from ``start`` looking for a ``plugins/`` directory."""
    current = start.resolve()
    if current.is_file():
        current = current.parent
    while current != current.parent:
        candidate = current / "plugins"
        if candidate.is_dir():
            return candidate
        # Also accept ``current`` itself being named "plugins".
        if current.name == "plugins":
            return current
        current = current.parent
    return None


def add_plugin_src_to_path(
    plugin_name: str,
    *,
    caller: Path | str | None = None,
) -> Path:
    """Insert ``plugins/<plugin_name>/src`` on sys.path and return it.

    Args:
        plugin_name: Sibling plugin name (e.g. ``"abstract"``).
        caller: Optional caller location, used as the starting point
            for the upward plugins/ walk. Defaults to the importer's
            module file via ``inspect.stack()`` introspection. Tests
            should pass the path explicitly.

    Returns:
        The Path that was added to sys.path (the plugin's src dir).

    Raises:
        FileNotFoundError: If no ``plugins/<plugin_name>/src``
            directory can be found by walking upward from ``caller``.
    """
    if caller is not None:
        caller_path = Path(caller)
    else:
        # Use the immediate caller's frame via inspect (public API,
        # avoids the CPython-private sys._getframe). inspect.stack()[1]
        # is the caller's frame; .filename is its co_filename.
        caller_file = inspect.stack()[1].filename
        # Synthetic filenames (<stdin>, <string>, <frozen ...>) cannot be
        # used as a starting point for the upward plugins/ walk; fall
        # back to cwd in that case.
        if caller_file and not caller_file.startswith("<"):
            caller_path = Path(caller_file)
        else:
            caller_path = Path.cwd()

    plugins_root = _find_plugins_root(caller_path)
    if plugins_root is None:
        msg = (
            f"add_plugin_src_to_path({plugin_name!r}): no plugins/ "
            f"directory found above {caller_path}"
        )
        raise FileNotFoundError(msg)

    target = plugins_root / plugin_name / "src"
    if not target.is_dir():
        msg = f"add_plugin_src_to_path({plugin_name!r}): {target} does not exist"
        raise FileNotFoundError(msg)

    target_str = str(target)
    if target_str not in sys.path:
        sys.path.insert(0, target_str)
    return target


__all__ = ["add_plugin_src_to_path"]
