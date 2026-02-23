#!/usr/bin/env python3
"""Audit log for configuration changes during a session.

Logs all ConfigChange events to stderr for security audit trail.
This hook is observe-only — it never blocks changes.

Supported sources: user_settings, project_settings, local_settings,
policy_settings, skills.
"""

import json
import sys
from datetime import datetime, timezone


def main():
    """Log configuration change events for audit purposes."""
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
        if not isinstance(input_data, dict):
            print("[DEBUG] ConfigChange hook: not a JSON object", file=sys.stderr)
            sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"[DEBUG] ConfigChange hook input parse failed: {e}", file=sys.stderr)
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    source = input_data.get("source", "unknown")
    file_path = input_data.get("file_path", "unknown")
    permission_mode = input_data.get("permission_mode", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017

    print(
        f"[CONFIG_CHANGE_AUDIT] {timestamp} "
        f"session={session_id} "
        f"source={source} "
        f"file={file_path} "
        f"permission_mode={permission_mode}",
        file=sys.stderr,
    )

    # Exit cleanly — audit only, never block
    sys.exit(0)


if __name__ == "__main__":
    main()
