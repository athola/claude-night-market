#!/usr/bin/env python3
"""Post-implementation checklist after a turn that edited files.

Claude Code runs Stop hooks at the end of every assistant turn, not once
per session. Shown unconditionally, the 22-line checklist would follow
every answer to a question. It is shown only when the turn that just
ended used a file-editing tool, read from the tail of the transcript.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REMINDER = """
## Post-Implementation Checklist Reminder

If you just completed a feature implementation or plan execution,
verify these were done:

### PROOF-OF-WORK (Verify First!)
- [ ] Invoked `Skill(imbue:proof-of-work)`
- [ ] Recorded progress items: `proof:solution-tested`, `proof:evidence-captured`
- [ ] Captured evidence with `[E1]`, `[E2]` references
- [ ] Ran functional tests (not just syntax validation)
- [ ] Reported status: ✅ PASS / ❌ FAIL

### Documentation Updates
- [ ] `/sanctum:update-docs`
- [ ] `/abstract:make-dogfood`
- [ ] `/sanctum:update-readme`
- [ ] `/sanctum:update-tests`

### Stewardship
- [ ] Left the campsite better? (See `Skill(leyline:stewardship)`)

⚠️ If proof-of-work was skipped, implementation may have untested assumptions!
If not applicable (simple fix, research, etc.), disregard this reminder.
""".strip()


_EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})

# The hook's timeout in hooks.json is 1s, so only the end of the
# transcript is read. One turn's rows fit in this many bytes in practice.
_TAIL_BYTES = 512 * 1024


def _content_items(row: dict) -> list:
    message = row.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return [{"type": "text"}]
    return [item for item in content or [] if isinstance(item, dict)]


def _is_prompt(row: dict) -> bool:
    """Return True for a user row that starts a turn (not a tool result)."""
    if row.get("type") != "user" or row.get("isMeta"):
        return False
    return not any(item.get("type") == "tool_result" for item in _content_items(row))


def _turn_edited_files(transcript_path: str) -> bool:
    """Whether the last turn in the transcript used a file-editing tool."""
    try:
        with Path(transcript_path).open("rb") as handle:
            handle.seek(0, 2)
            handle.seek(max(0, handle.tell() - _TAIL_BYTES))
            tail = handle.read().decode("utf-8", errors="replace")
    except (OSError, TypeError, ValueError):
        return False
    for line in reversed(tail.splitlines()):
        try:
            row = json.loads(line)
        except ValueError:
            continue  # the first line of the tail is usually cut
        if not isinstance(row, dict):
            continue
        if _is_prompt(row):
            return False
        if row.get("type") == "assistant" and any(
            item.get("type") == "tool_use" and item.get("name") in _EDIT_TOOLS
            for item in _content_items(row)
        ):
            return True
    return False


def main() -> None:
    """Show the checklist when the turn that just ended edited files."""
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)  # no payload means no transcript to judge
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        sys.exit(0)
    if not _turn_edited_files(payload.get("transcript_path", "")):
        sys.exit(0)

    # Without decision="block" a Stop hook's "reason" is not shown to anyone,
    # so the reminder goes out as the user-visible systemMessage.
    print(json.dumps({"systemMessage": REMINDER}))
    sys.exit(0)


if __name__ == "__main__":
    main()
