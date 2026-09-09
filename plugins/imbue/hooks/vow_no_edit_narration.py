#!/usr/bin/env python3
"""Vow: No edit narration in a written artifact (Hard layer).

PreToolUse hook that blocks (or warns in shadow mode) when text being
written into a file narrates the edit the session is making. "We
renamed the handler", "reads the manifest instead of the previous
inline config": a change event, recorded where a reader came for
current state.

Two registers, and only one is guarded. Saying what was not done is
required of a completion report, both by the harness and by
`Skill(imbue:proof-of-work)`, which asks for BLOCKED work to be named.
A docstring has no session to report on. This hook sees a file write
and never a reply, so the split is structural rather than a rule the
model has to remember.

The pattern set is deliberately small. `tier5.temporal_residue` in
`plugins/scribe/data/languages/en.yaml` carries the broad list, gated
off and low confidence, because temporal narration in rationale
documentation is correct and no regex separates it from residue. What
is left here is the subset that matches nothing in this repository
today, which `tests/unit/hooks/test_vow_no_edit_narration.py` pins.
A guard that fires on correct prose is instruction load, and the
papers cited in `.claude/rules/bounded-autonomy.md` say what that
costs.

Shadow mode is ON by default (warn only).  Set VOW_SHADOW_MODE=0
to switch to full blocking.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    shadow_mode_active,
)

_GUARDED_SUFFIXES = (".py", ".md", ".rs", ".ts", ".tsx", ".js", ".go", ".proto")

# Both patterns measure zero over `git ls-files` today. Anything that
# fires here is text this session introduced.
_NARRATION_PATTERNS = (
    # First-person edit narration, anchored so a quoted question
    # ("What would break if I removed this line?") is left alone. Four
    # such quotes exist in the skills and all four are correct.
    (
        "first-person edit narration",
        re.compile(
            r"(?:^[\s#/*-]*|(?<=\.\s))(?:I|We)\s+"
            r"(?:removed|renamed|replaced|dropped|deleted|moved|switched)\b",
            re.MULTILINE,
        ),
    ),
    (
        "comparison against the superseded version",
        re.compile(
            r"\binstead\s+of\s+the\s+(?:old|previous|former|earlier)\b",
            re.IGNORECASE,
        ),
    ),
)


def inserted_text(tool_name: str, tool_input: dict) -> str:
    """Return the text this call adds, and none of what was there.

    Residue is a property of new prose. Scanning a whole file on every
    edit would charge the session for text it inherited, and would fire
    on the same line until someone rewrote a file they had not touched.

    For Write the whole body is new. For Edit only the lines in
    `new_string` that are absent from `old_string` are, which keeps a
    one-word change to a line that already narrated an edit from
    reading as a fresh violation.
    """
    if tool_name == "Write":
        return tool_input.get("content", "") or ""

    edits = tool_input.get("edits")
    if not isinstance(edits, list):
        edits = [tool_input]

    added: list[str] = []
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        new = edit.get("new_string", "") or ""
        old = edit.get("old_string", "") or ""
        old_lines = set(old.splitlines())
        added.extend(line for line in new.splitlines() if line not in old_lines)
    return "\n".join(added)


def find_narration(text: str) -> tuple[str, str] | None:
    """Return (label, matched text) for the first narration found."""
    for label, pattern in _NARRATION_PATTERNS:
        found = pattern.search(text)
        if found:
            return label, found.group(0)
    return None


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        tool_name = data.get("tool_name", "")
        if tool_name not in ("Write", "Edit", "MultiEdit"):
            sys.exit(0)

        tool_input = data.get("tool_input", {}) or {}
        file_path = tool_input.get("file_path", "") or ""
        if not file_path.endswith(_GUARDED_SUFFIXES):
            sys.exit(0)

        found = find_narration(inserted_text(tool_name, tool_input))
        if not found:
            sys.exit(0)
        label, matched = found

        shadow = shadow_mode_active()
        decision = "warn" if shadow else "block"
        reason = (
            f"Vow violation: {label} in written text ({matched!r}). "
            "The file records what the code is; the commit message "
            "records what changed. State the current behavior and drop "
            "the comparison. "
            + (
                "Shadow mode active -- this will block once VOW_SHADOW_MODE=0."
                if shadow
                else ""
            )
        )

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(output))
        print(
            f"[vow-no-edit-narration] {decision.upper()}: {label}",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception as exc:  # hook must not crash the agent under any circumstance
        print(
            f"[vow-no-edit-narration] internal error: {exc}",
            file=sys.stderr,
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
