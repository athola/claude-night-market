#!/usr/bin/env python3
"""Verify workflow completion hook for Stop event.

Provides a final reminder about the post-implementation protocol.
This is a backup safeguard - Stop hooks cannot block, only inform.
"""

from __future__ import annotations

import json
import sys

REMINDER = """
## Post-Implementation Checklist Reminder

If you just completed a feature implementation or plan execution,
verify these were done:

### PROOF-OF-WORK (Verify First!)
- [ ] Invoked `Skill(imbue:proof-of-work)`
- [ ] Created TodoWrite items: `proof:solution-tested`, `proof:evidence-captured`
- [ ] Captured evidence with `[E1]`, `[E2]` references
- [ ] Ran functional tests (not just syntax validation)
- [ ] Reported status: ✅ PASS / ❌ FAIL

### Documentation Updates
- [ ] `/sanctum:update-docs`
- [ ] `/abstract:make-dogfood`
- [ ] `/sanctum:update-readme`
- [ ] `/sanctum:update-tests`

⚠️ If proof-of-work was skipped, implementation may have untested assumptions!
If not applicable (simple fix, research, etc.), disregard this reminder.
""".strip()


def main() -> None:
    """Provide workflow reminder at session end."""
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        # No payload or invalid JSON - still provide reminder
        pass

    # Output reminder as hook context (Stop hooks are informational-only)
    # Stop hooks use 'reason' field, not hookSpecificOutput
    output = {
        "reason": REMINDER,
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
