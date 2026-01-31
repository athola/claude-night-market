#!/usr/bin/env python3
"""Workflow verification reminder at session stop.

Provides a reminder to complete post-implementation checklist
when a Claude session ends.
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
    # Read stop reason from stdin (optional)
    try:
        _ = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as e:
        pass  # No payload or invalid input - continue anyway
        # Log to stderr for debugging (doesn't break hook output)
        print(f"[DEBUG] Hook input parse failed: {e}", file=sys.stderr)

    # Output reminder
    print(json.dumps({"reason": REMINDER}))
    sys.exit(0)


if __name__ == "__main__":
    main()
