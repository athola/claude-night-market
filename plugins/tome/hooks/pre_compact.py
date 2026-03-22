#!/usr/bin/env python3
"""PreCompact hook: inject active research session context."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from hooks._session_utils import load_active_session
except ImportError:
    from _session_utils import load_active_session


def main() -> None:
    """Inject active session context before compaction.

    Reads the most recent active session and emits its topic
    as additionalContext so the compacted prompt retains it.
    Does not save or modify any session state.
    """
    tome_dir = Path.cwd() / ".tome" / "sessions"
    result = load_active_session(tome_dir)
    if result is None:
        return
    topic, _finding_count = result
    msg = f'Tome research session "{topic}" is active.'
    print(json.dumps({"additionalContext": msg}))


if __name__ == "__main__":
    main()
