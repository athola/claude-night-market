#!/usr/bin/env python3
"""Combined Stop hook: workflow verification + session notification.

Merges verify_workflow_complete.py and session_complete_notify.py into a single
process to eliminate one Python interpreter startup (~20ms savings).

This is an OPTIONAL optimization. The individual hooks are already fast (~57ms total).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# ============================================================================
# HOOK 1: Workflow Verification (from verify_workflow_complete.py)
# ============================================================================

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


def workflow_verification() -> dict:
    """Provide workflow reminder at session end."""
    return {"reason": REMINDER}


# ============================================================================
# HOOK 2: Session Notification (from session_complete_notify.py)
# ============================================================================


def spawn_notification_background() -> None:
    """Spawn notification in background process (non-blocking)."""
    # Skip if notifications disabled
    if os.environ.get("CLAUDE_NO_NOTIFICATIONS") == "1":
        return

    # Get the original notification script path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    notify_script = os.path.join(script_dir, "session_complete_notify.py")

    # If the separate script exists, use it for actual notification logic
    if os.path.exists(notify_script):
        try:
            subprocess.Popen(  # noqa: S603
                [sys.executable, notify_script, "--background"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Fully detach from parent
            )
        except Exception:  # noqa: S110
            pass  # Silent fail - notifications are non-critical


# ============================================================================
# MAIN: Combined Stop Hook
# ============================================================================


def main() -> None:
    """Execute combined Stop hook logic."""
    # Read stop reason from stdin
    stop_reason = None
    try:
        payload = json.load(sys.stdin)
        stop_reason = payload.get("reason")
    except json.JSONDecodeError:
        pass  # No payload or invalid JSON - continue anyway

    # Execute Hook 1: Workflow verification
    output = workflow_verification()

    # Execute Hook 2: Spawn notification ONLY when user input is needed
    # Only notify on "end_turn" - when Claude finished and awaits user input
    # Skip for: tool_use (intermediate), max_tokens, stop_sequence, etc.
    if stop_reason == "end_turn":
        spawn_notification_background()

    # Output combined result
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
