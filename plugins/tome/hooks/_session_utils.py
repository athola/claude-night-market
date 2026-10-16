"""Shared utilities for tome hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_active_session(tome_dir: Path) -> tuple[str, int] | None:
    """Return (topic, finding_count) for the most recent active session, or None."""
    if not tome_dir.exists():
        return None
    sessions = sorted(
        tome_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not sessions:
        return None
    try:
        data = json.loads(sessions[0].read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        # ValueError covers JSONDecodeError and UnicodeDecodeError.
        print(f"tome: corrupt session file {sessions[0]}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"tome: session file {sessions[0]} is not an object", file=sys.stderr)
        return None
    if data.get("status") == "active":
        return data.get("topic", "unknown"), len(data.get("findings") or [])
    return None
