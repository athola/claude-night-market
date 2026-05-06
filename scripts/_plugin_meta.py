"""Shared plugin metadata helpers for root-level scripts.

Consolidates per-script copies of metadata accessors so the
top-level scripts (`a2a_cards.py`, `clawhub_export.py`, etc.)
can share one implementation. See D-11.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

__all__ = ["get_plugin_version"]

_DEFAULT_VERSION = "1.0.0"


def get_plugin_version(plugin_dir: Path) -> str:
    """Read ``version`` from ``<plugin>/.claude-plugin/plugin.json``.

    Returns ``"1.0.0"`` when the manifest is missing or doesn't
    carry a ``version`` field. ``OSError`` (permission, ENOSPC,
    disconnected mounts, etc.) is logged to stderr before falling
    back; ``JSONDecodeError`` falls back silently because the
    consumers are best-effort report generators.
    """
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            return data.get("version", _DEFAULT_VERSION)
        except json.JSONDecodeError:
            pass
        except OSError as exc:
            print(
                f"_plugin_meta: plugin.json unreadable at {pj}: {exc}",
                file=sys.stderr,
            )
    return _DEFAULT_VERSION
