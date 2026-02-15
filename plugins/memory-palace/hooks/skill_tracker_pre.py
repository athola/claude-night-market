#!/usr/bin/env python3
"""PreToolUse hook for skill execution tracking.

Records start time and initializes invocation tracking before skill execution.
Works with skill_tracker_post.py to calculate duration and enable per-iteration learning.

Migrated from pensieve plugin to consolidate skill memory storage in memory-palace.
Zero external dependencies - uses only Python standard library.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def get_skill_observability_dir() -> Path:
    """Get or create skill observability state directory."""
    claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    state_dir = claude_home / "skills" / "observability"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def parse_skill_name(tool_input: dict[str, Any]) -> tuple[str, str]:
    """Parse plugin and skill name from Skill tool input.

    Args:
        tool_input: Skill tool input dictionary

    Returns:
        Tuple of (plugin_name, skill_name)

    """
    skill_ref = tool_input.get("skill", "unknown:unknown")

    if ":" in skill_ref:
        plugin, skill = skill_ref.split(":", 1)
        return plugin.strip(), skill.strip()

    return "unknown", skill_ref.strip()


def main() -> None:
    """PreToolUse hook entry point."""
    try:
        # Read environment variables from Claude Code
        tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
        tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

        # Only process Skill tool invocations
        if tool_name != "Skill":
            sys.exit(0)

        # Parse tool input
        try:
            tool_input = json.loads(tool_input_str)
        except json.JSONDecodeError:
            sys.exit(0)  # Silently skip malformed input

        # Parse skill name
        plugin, skill = parse_skill_name(tool_input)
        skill_ref = f"{plugin}:{skill}"

        # Create unique invocation ID
        invocation_id = f"{skill_ref}:{datetime.now(UTC).timestamp()}"

        # Create state for PostToolUse to read
        state = {
            "invocation_id": invocation_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "skill": skill_ref,
            "plugin": plugin,
            "skill_name": skill,
            "tool_input": tool_input,
        }

        # Store state file for PostToolUse
        state_dir = get_skill_observability_dir()
        state_file = state_dir / f"{invocation_id}.json"

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Output hook data (becomes available to Claude Code)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "invocation_id": invocation_id,
                "skill": skill_ref,
                "message": f"Tracking skill execution: {skill_ref}",
            }
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # Never block Claude Code on hook errors
        sys.stderr.write(f"skill_tracker_pre error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
