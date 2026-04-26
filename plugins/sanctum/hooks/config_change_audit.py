#!/usr/bin/env python3
"""Audit log for configuration changes during a session.

The hook accepts two payload shapes:

* **Legacy ConfigChange** (preserved for forward compatibility if the
  dedicated event is reintroduced). Top-level fields ``session_id``,
  ``source``, ``file_path``, ``permission_mode``.

* **PreToolUse for Edit/Write/MultiEdit on a settings file** (current
  Claude Code v2.1.89+, where ConfigChange does not fire). The hook
  detects ``file_path`` paths under any ``.claude/`` directory whose
  basename matches ``settings*.json`` and infers the source bucket
  from the path so the audit line matches the legacy format.

Observe-only: never blocks tool execution. Failures exit 0 silently.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import PurePath

_SETTINGS_TOOLS = {"Edit", "Write", "MultiEdit"}
_POLICY_PATHS = (
    "/etc/claude/managed-settings.json",
    "/Library/Application Support/ClaudeCode/managed-settings.json",
    "C:\\ProgramData\\ClaudeCode\\managed-settings.json",
)


def _is_settings_file(file_path: str) -> bool:
    """Return True if *file_path* is a Claude settings file we should audit."""
    if not file_path:
        return False
    if file_path in _POLICY_PATHS:
        return True
    p = PurePath(file_path)
    if not p.name.startswith("settings") or not p.name.endswith(".json"):
        return False
    # Must live under a ``.claude`` directory anywhere in its parents.
    return any(part == ".claude" for part in p.parts)


def _infer_source(file_path: str) -> str:
    """Map a settings file path to its source bucket."""
    if file_path in _POLICY_PATHS:
        return "policy_settings"

    name = PurePath(file_path).name
    if name == "settings.local.json":
        return "local_settings"

    home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or ""
    if home and (
        file_path.startswith(home + os.sep) or file_path.startswith(home + "/")
    ):
        return "user_settings"

    return "project_settings"


def _audit_line(
    session_id: str,
    source: str,
    file_path: str,
    permission_mode: str,
) -> str:
    """Render the canonical audit line."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"[CONFIG_CHANGE_AUDIT] {timestamp} "
        f"session={session_id} "
        f"source={source} "
        f"file={file_path} "
        f"permission_mode={permission_mode}"
    )


def _handle_pre_tool_use(input_data: dict) -> bool:
    """Audit settings-file edits seen via PreToolUse.

    Returns True if the payload was handled (settings edit audited or
    intentionally skipped) so legacy fall-through does not fire.
    """
    tool_name = input_data.get("tool_name", "")
    if tool_name not in _SETTINGS_TOOLS:
        return True  # PreToolUse but not a settings-touching tool.

    tool_input = input_data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")

    if not _is_settings_file(file_path):
        return True  # Editing some other file -- not config audit material.

    session_id = input_data.get("session_id", "unknown")
    source = _infer_source(file_path)
    # PreToolUse payloads do not carry permission_mode; record explicitly.
    permission_mode = input_data.get("permission_mode", "n/a")

    print(
        _audit_line(session_id, source, file_path, permission_mode),
        file=sys.stderr,
    )
    return True


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

    # PreToolUse migration path -- detect by event name or tool_name presence.
    is_pre_tool_use = (
        input_data.get("hook_event_name") == "PreToolUse" or "tool_name" in input_data
    )
    if is_pre_tool_use:
        _handle_pre_tool_use(input_data)
        sys.exit(0)

    # Legacy ConfigChange path.
    session_id = input_data.get("session_id", "unknown")
    source = input_data.get("source", "unknown")
    file_path = input_data.get("file_path", "unknown")
    permission_mode = input_data.get("permission_mode", "unknown")

    print(
        _audit_line(session_id, source, file_path, permission_mode),
        file=sys.stderr,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
