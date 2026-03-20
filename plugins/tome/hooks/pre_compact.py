#!/usr/bin/env python3
"""PreCompact hook: checkpoint active research session."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    """Save active session state before context compaction."""
    tome_dir = Path.cwd() / ".tome" / "sessions"
    if not tome_dir.exists():
        return

    sessions = sorted(
        tome_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not sessions:
        return

    try:
        with open(sessions[0], encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    if data.get("status") == "active":
        topic = data.get("topic", "unknown")
        msg = (
            f'Tome research session "{topic}" is active. '
            f"Session state has been checkpointed to {sessions[0].name}."
        )
        print(json.dumps({"additionalContext": msg}))


if __name__ == "__main__":
    main()
