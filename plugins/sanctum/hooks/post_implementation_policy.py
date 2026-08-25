#!/usr/bin/env python3
"""Post-implementation policy hook for SessionStart.

Inject mandatory workflow instructions for Claude to follow before reporting
completion of feature implementations or plan executions.

Use governance framing to resist override attempts from other prompts, skills, or hooks.

Read `agent_type` from hook input (Claude Code 2.1.2+) to customize policy injection.
"""

from __future__ import annotations

import json
import sys

# Lightweight agents that skip full governance policy
LIGHTWEIGHT_AGENTS = frozenset(
    {
        "quick-query",
        "simple-task",
        "code-reviewer",  # Review agents don't implement features
        "architecture-reviewer",
        "rust-auditor",
        "bloat-auditor",
        "context-optimizer",  # Optimization agents don't add features
    }
)

GOVERNANCE_POLICY = """
## Post-Implementation Protocol

<GOVERNANCE_RULE priority="high">
Applies before you report a feature, a plan execution, or a significant
code change as complete. It does not apply to questions, explanations,
bug fixes that add no behavior, refactors, or exploration.

Run these in order:

1. `Skill(imbue:proof-of-work)`. Invoke it first, because it carries the
   evidence bar and the Iron Law -- no implementation without a failing
   test first -- and the TodoWrite items, the `[E1]` citation form and
   the PASS / FAIL / BLOCKED report are all defined there.
2. `/sanctum:update-docs`
3. `/abstract:make-dogfood`
4. `/sanctum:update-readme`
5. `/sanctum:update-tests`

Done means every step above ran and every claim you make cites output you
saw. Only the user waives a step.
</GOVERNANCE_RULE>
""".strip()


def main() -> None:
    """Inject governance policy at session start.

    Read hook input from stdin to check for agent_type (Claude Code 2.1.2+).
    Skip the full governance policy for lightweight agents to reduce context overhead.
    """
    # Read hook input from stdin (Claude Code 2.1.2+)
    agent_type = ""
    try:
        input_data = sys.stdin.read().strip()
        if input_data:
            hook_input = json.loads(input_data)
            agent_type = hook_input.get("agent_type", "")
    except (OSError, json.JSONDecodeError) as e:
        # Gracefully handle missing or malformed input
        # Log to stderr for debugging (doesn't break hook output)
        print(f"[DEBUG] Hook input parse failed: {e}", file=sys.stderr)

    # Skip full governance for lightweight agents
    if agent_type in LIGHTWEIGHT_AGENTS:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    f"[sanctum] Agent '{agent_type}'"
                    " - governance policy deferred"
                    " (review/optimization agent)."
                ),
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Full governance policy for implementation agents
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": GOVERNANCE_POLICY,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
