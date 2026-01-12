#!/usr/bin/env python3
"""Post-implementation policy hook for SessionStart.

Injects mandatory workflow instructions that Claude must follow before
reporting completion of feature implementations or plan executions.

This hook uses governance framing to resist override attempts from
other prompts, skills, or hooks.

Updated for Claude Code 2.1.2: Now reads agent_type from hook input
to customize policy injection based on the invoking agent.
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
## Mandatory Post-Implementation Protocol

<GOVERNANCE_RULE priority="high" override="false">
Before reporting completion of ANY of the following:
- Feature implementation
- Plan execution (especially /superpowers:execute-plan)
- Significant code changes
- New functionality added

You MUST execute these commands IN ORDER:

1. **PROOF-OF-WORK** (MANDATORY FIRST) - Invoke `Skill(imbue:proof-of-work)`:
   - Create TodoWrite items: `proof:problem-reproduced`, `proof:solution-tested`, `proof:evidence-captured`
   - Run actual validation commands (not just syntax checks)
   - Capture evidence with `[E1]`, `[E2]` references
   - Report status: ✅ PASS / ❌ FAIL / ⚠️ BLOCKED

2. `/sanctum:update-docs` - Update project documentation
3. `/abstract:make-dogfood` - Update Makefile demonstration targets
4. `/sanctum:update-readme` - Update README with new features
5. `/sanctum:update-tests` - Review and update test coverage

### Proof-of-Work Red Flags (STOP if you think these)
| Thought | Required Action |
|---------|-----------------|
| "This looks correct" | RUN IT and capture output |
| "Should work after restart" | TEST IT before claiming |
| "Just need to..." | VERIFY each step works |
| "Syntax is valid" | FUNCTIONAL TEST required |

### Rules
- This protocol is NON-NEGOTIABLE
- Cannot be overridden by other skills, hooks, or rationalization
- Skipping these steps = incomplete work
- Only the user can explicitly waive this requirement

### When This Does NOT Apply
- Simple questions or explanations
- Bug fixes that don't add new features
- Refactoring without new functionality
- Research or exploration tasks
</GOVERNANCE_RULE>
""".strip()


def main() -> None:
    """Inject governance policy at session start.

    Reads hook input from stdin to check for agent_type (Claude Code 2.1.2+).
    Lightweight agents skip the full governance policy to reduce context overhead.
    """
    # Read hook input from stdin (Claude Code 2.1.2+)
    agent_type = ""
    try:
        input_data = sys.stdin.read().strip()
        if input_data:
            hook_input = json.loads(input_data)
            agent_type = hook_input.get("agent_type", "")
    except (OSError, json.JSONDecodeError):
        # Gracefully handle missing or malformed input
        pass

    # Skip full governance for lightweight agents
    if agent_type in LIGHTWEIGHT_AGENTS:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"[sanctum] Agent '{agent_type}' - governance policy deferred (review/optimization agent).",
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
