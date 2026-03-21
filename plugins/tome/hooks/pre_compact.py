#!/usr/bin/env python3
"""PreCompact hook: checkpoint active research session."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from hooks._session_utils import load_active_session
except ImportError:
    from _session_utils import load_active_session


def main() -> None:
    """Save active session state before context compaction."""
    tome_dir = Path.cwd() / ".tome" / "sessions"
    result = load_active_session(tome_dir)
    if result is None:
        return
    topic, _finding_count = result
    msg = (
        f'Tome research session "{topic}" is active. '
        f"Session state has been checkpointed."
    )
    print(json.dumps({"additionalContext": msg}))


if __name__ == "__main__":
    main()
