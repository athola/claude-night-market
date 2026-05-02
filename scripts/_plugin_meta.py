"""Shared plugin metadata helpers for root-level scripts.

Consolidates per-script copies of metadata accessors so the
top-level scripts (`a2a_cards.py`, `clawhub_export.py`, etc.)
can share one implementation. See D-11.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["get_plugin_version"]

_DEFAULT_VERSION = "1.0.0"


def get_plugin_version(plugin_dir: Path) -> str:
    """Read ``version`` from ``<plugin>/.claude-plugin/plugin.json``.

    Returns ``"1.0.0"`` when the manifest is missing, unreadable,
    or doesn't carry a ``version`` field. Errors are swallowed by
    design: the consumers are best-effort report generators.
    """
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            return data.get("version", _DEFAULT_VERSION)
        except (json.JSONDecodeError, OSError):
            pass
    return _DEFAULT_VERSION
