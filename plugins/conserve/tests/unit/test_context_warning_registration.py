"""context_warning sees subagent dispatches, the largest context spends.

Claude Code names the dispatch tool ``Agent``; ``Task`` is its legacy
name. A matcher listing only ``Task`` never runs the warning before a
subagent is sent out.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_HOOKS_JSON = Path(__file__).resolve().parents[2] / "hooks" / "hooks.json"


def _context_warning_matchers() -> list[str]:
    config = json.loads(_HOOKS_JSON.read_text())
    return [
        group["matcher"]
        for group in config["hooks"]["PreToolUse"]
        if any("context_warning.py" in hook["command"] for hook in group["hooks"])
    ]


@pytest.mark.unit
@pytest.mark.parametrize("tool", ["Agent", "Task", "Skill", "Bash"])
def test_context_warning_runs_before_each_costly_tool(tool: str) -> None:
    matchers = _context_warning_matchers()
    assert matchers, "context_warning is not registered on PreToolUse"
    assert any(re.fullmatch(matcher, tool) for matcher in matchers), tool
