#!/usr/bin/env python3
"""PreToolUse hook for skill execution tracking.

Records start time and initializes invocation tracking before skill execution.
Works with post_skill_execution.py to calculate duration and enable
per-iteration learning.

Zero external dependencies - uses only Python standard library.
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

from shared.dir_utils import get_observability_dir
from shared.hook_io import read_hook_payload
from shared.skill_utils import parse_skill_name as _parse_skill_name


def parse_skill_name(tool_input: dict[str, Any]) -> tuple[str, str]:
    """Parse plugin and skill name from Skill tool input.

    Delegates to shared.skill_utils for consistent sanitization.

    Args:
        tool_input: Skill tool input dictionary

    Returns:
        Tuple of (plugin_name, skill_name)

    """
    return _parse_skill_name(tool_input)


def main() -> None:
    """PreToolUse hook entry point."""
    try:
        # Claude Code delivers the hook payload as JSON on stdin (with a
        # legacy CLAUDE_TOOL_* env-var fallback for the test harness).
        payload = read_hook_payload()
        tool_name = payload["tool_name"]

        # Only process Skill tool invocations
        if tool_name != "Skill":
            sys.exit(0)

        tool_input = payload["tool_input"]

        # Parse skill name
        plugin, skill = parse_skill_name(tool_input)
        skill_ref = f"{plugin}:{skill}"

        # Create unique invocation ID
        invocation_id = f"{skill_ref}:{datetime.now(timezone.utc).timestamp()}"

        # Create state for PostToolUse to read
        state = {
            "invocation_id": invocation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skill": skill_ref,
            "plugin": plugin,
            "skill_name": skill,
            "tool_input": tool_input,
        }

        # Store state file for PostToolUse
        state_dir = get_observability_dir()
        state_file = state_dir / f"{invocation_id}.json"

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Output hook data with additionalContext (Claude Code 2.1.9+)
        # Inject skill execution context visible to Claude
        additional_context = f"[Skill Invocation] Executing {skill_ref}"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "invocation_id": invocation_id,
                "skill": skill_ref,
                "additionalContext": additional_context,
            }
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # Never block Claude Code on hook errors
        sys.stderr.write(traceback.format_exc())
        sys.stderr.write(f"pre_skill_execution error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
