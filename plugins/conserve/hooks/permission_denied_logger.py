#!/usr/bin/env python3
"""Log auto-mode permission denials for observability.

Fires on PermissionDenied events (new in v2.1.89). When auto mode's
classifier denies a tool call, this hook logs the denial and optionally
signals retry for known-safe patterns.

Return {retry: true} to tell the model it can retry the denied tool.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Tools that are safe to retry after denial (read-only operations)
RETRY_SAFE_TOOLS = frozenset({"Read", "Glob", "Grep", "WebFetch", "WebSearch"})

# Log location
LOG_DIR = (
    Path(
        os.environ.get(
            "CLAUDE_PROJECT_DIR",
            os.environ.get("PWD", "."),
        )
    )
    / ".claude"
    / "logs"
)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "unknown")
    reason = input_data.get("reason", "")
    timestamp = datetime.now(timezone.utc).isoformat()

    # Log the denial
    print(
        f"[PermissionDenied] {timestamp} tool={tool_name} reason={reason}",
        file=sys.stderr,
    )

    # Append to denial log file for post-session analysis
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "permission_denials.jsonl"
        entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "reason": reason,
            "session": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Non-critical logging failure

    # Auto-retry read-only tools (safe to re-attempt)
    if tool_name in RETRY_SAFE_TOOLS:
        output = {"retry": True}
        print(json.dumps(output))
        print(
            f"[PermissionDenied] Auto-retry for read-only tool: {tool_name}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
