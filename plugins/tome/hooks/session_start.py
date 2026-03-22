#!/usr/bin/env python3
"""SessionStart hook: check for active research sessions."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from hooks._session_utils import load_active_session
except ImportError:
    from _session_utils import load_active_session


def main() -> None:
    """Check for active tome research sessions on startup."""
    tome_dir = Path.cwd() / ".tome" / "sessions"
    result = load_active_session(tome_dir)
    if result is None:
        return
    topic, finding_count = result
    msg = (
        f'Active tome research session: "{topic}" '
        f"({finding_count} findings). "
        f"Use /tome:dig to refine or /tome:research --resume to continue."
    )
    print(json.dumps({"additionalContext": msg}))


if __name__ == "__main__":
    main()
