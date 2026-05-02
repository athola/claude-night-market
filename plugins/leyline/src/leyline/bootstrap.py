"""Cross-plugin sys.path bootstrap helper (AR-15).

Twenty-five+ scripts and hooks each open-coded their own
``Path(__file__).resolve().parents[N] / "<plugin>" / "src"``
discovery before importing from a sibling plugin. This module
collapses that pattern to one tested helper.

Note: this module cannot bootstrap leyline itself -- callers
that need leyline must still place ``plugins/leyline/src`` on
sys.path with their own snippet before they can ``from
leyline.bootstrap import add_plugin_src_to_path``. Once leyline
is on the path, every secondary cross-plugin lookup uses this
helper.
"""

from __future__ import annotations

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
            module file via ``sys._getframe`` introspection. Tests
            should pass the path explicitly.

    Returns:
        The Path that was added to sys.path (the plugin's src dir).

    Raises:
        FileNotFoundError: If no ``plugins/<plugin_name>/src``
            directory can be found by walking upward from ``caller``.
    """
    if caller is None:
        # Use the immediate caller's __file__ if available.
        frame = sys._getframe(1)  # noqa: SLF001 - sys._getframe is the recommended way
        caller_file = frame.f_globals.get("__file__")
        caller_path = Path(caller_file) if caller_file else Path.cwd()
    else:
        caller_path = Path(caller)

    plugins_root = _find_plugins_root(caller_path)
    if plugins_root is None:
        msg = (
            f"add_plugin_src_to_path({plugin_name!r}): no plugins/ "
            f"directory found above {caller_path}"
        )
        raise FileNotFoundError(msg)

    target = plugins_root / plugin_name / "src"
    if not target.is_dir():
        msg = (
            f"add_plugin_src_to_path({plugin_name!r}): {target} "
            "does not exist"
        )
        raise FileNotFoundError(msg)

    target_str = str(target)
    if target_str not in sys.path:
        sys.path.insert(0, target_str)
    return target


__all__ = ["add_plugin_src_to_path"]
