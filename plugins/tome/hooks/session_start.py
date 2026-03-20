#!/usr/bin/env python3
"""SessionStart hook: check for active research sessions."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    """Check for active tome research sessions on startup."""
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
        finding_count = len(data.get("findings", []))
        msg = (
            f'Active tome research session: "{topic}" '
            f"({finding_count} findings). "
            f"Use /tome:dig to refine or /tome:research --resume to continue."
        )
        print(json.dumps({"additionalContext": msg}))


if __name__ == "__main__":
    main()
