"""Shared manifest utilities for egregore hooks.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def consume_stdin() -> None:
    """Consume and discard stdin JSON payload."""
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass


def read_stdin_payload() -> dict:
    """Read the hook payload from stdin.

    Returns an empty dict when stdin holds nothing parseable, so a
    caller can read optional fields without gating on the shape of
    the payload.
    """
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_manifest_data(manifest_path: Path) -> dict | None:
    """Load and parse manifest JSON, returning None on failure."""
    try:
        data = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def find_manifest() -> Path:
    """Find manifest.json walking up from CWD."""
    cwd = Path(os.getcwd())
    for directory in [cwd] + list(cwd.parents):
        candidate = directory / ".egregore" / "manifest.json"
        if candidate.exists():
            return candidate
    return cwd / ".egregore" / "manifest.json"


def get_items(data: dict) -> list:
    """Get work items from manifest, supporting both key names."""
    items = data.get("work_items") or data.get("items") or []
    return items if isinstance(items, list) else []


# Statuses that indicate remaining work
ACTIVE_STATUSES = ("active", "paused", "pending")


def has_active_work(manifest_path: Path) -> bool:
    """Check if manifest has unfinished work items."""
    if not manifest_path.exists():
        return False
    try:
        data = json.loads(manifest_path.read_text())
        items = get_items(data)
        return any(item.get("status") in ACTIVE_STATUSES for item in items)
    except (json.JSONDecodeError, OSError):
        return False
