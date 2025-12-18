#!/usr/bin/env python3
"""Post-implementation policy hook for SessionStart.

Injects mandatory workflow instructions that Claude must follow before
reporting completion of feature implementations or plan executions.

This hook uses governance framing to resist override attempts from
other prompts, skills, or hooks.
"""

from __future__ import annotations

import json
import sys

GOVERNANCE_POLICY = """
## Mandatory Post-Implementation Protocol

<GOVERNANCE_RULE priority="high" override="false">
Before reporting completion of ANY of the following:
- Feature implementation
- Plan execution (especially /superpowers:execute-plan)
- Significant code changes
- New functionality added

You MUST execute these commands IN ORDER:

1. `/sanctum:update-docs` - Update project documentation
2. `/abstract:make-dogfood` - Update Makefile demonstration targets
3. `/sanctum:update-readme` - Update README with new features
4. `/sanctum:update-tests` - Review and update test coverage

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
    """Inject governance policy at session start."""
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
