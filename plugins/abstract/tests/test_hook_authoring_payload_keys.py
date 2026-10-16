"""The hook-authoring skill teaches the payload keys hooks receive.

Its event table listed `message`, `tool_output`, `reason, result`,
`subagent_id, result` and `context_size`. None of these is in the payload
(code.claude.com/docs/en/hooks, per-event "input" sections), so a hook
written from the table reads a missing key and silently does nothing,
which is how two hooks here read `tool_result` for months.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "hook-authoring" / "SKILL.md"

DOCUMENTED = {
    "PostToolUse": "`tool_response`",
    "UserPromptSubmit": "`prompt`",
    "Notification": "`notification_type`",
    "Stop": "`background_tasks`",
    "SubagentStop": "`agent_type`",
    "TaskCompleted": "`task_subject`",
    "PreCompact": "`trigger`",
    "SessionEnd": "`reason`",
    "WorktreeCreate": "`name`",
}


def _row(event: str) -> str:
    match = re.search(rf"^\| \*\*{event}\*\* \|.*$", SKILL.read_text(), re.MULTILINE)
    assert match is not None, f"no table row for {event}"
    return match.group(0)


@pytest.mark.parametrize(("event", "key"), sorted(DOCUMENTED.items()))
def test_event_row_names_a_documented_key(event: str, key: str) -> None:
    assert key in _row(event)


@pytest.mark.parametrize(
    "invented", ["`tool_output`", "`subagent_id`", "`context_size`", "`result`"]
)
def test_table_names_no_invented_key(invented: str) -> None:
    table = "\n".join(
        line for line in SKILL.read_text().splitlines() if line.startswith("| **")
    )
    assert invented not in table
