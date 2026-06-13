#!/usr/bin/env python3
"""SessionStart hook: check for active research sessions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the plugin root is importable so the `hooks` package resolves whether
# this file is run as a standalone script or imported as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hooks._session_utils import (
    load_active_session,  # noqa: E402 - hook script must extend sys.path before importing the hooks package
)


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
