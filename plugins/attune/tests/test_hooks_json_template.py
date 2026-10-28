"""The hooks.json a new plugin project receives must load and fire.

The template matched with an object where Claude Code takes a string, and
gated the hook on ``$CLAUDE_TOOL_INPUT``, which Claude Code does not set:
every generated project got a hook that never ran.
"""

from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[1] / "templates" / "hooks" / "hooks.json.template"
)


def _entries() -> list[tuple[dict, dict]]:
    config = json.loads(TEMPLATE.read_text())
    return [
        (group, hook)
        for groups in config["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]


def test_every_matcher_is_a_string() -> None:
    """Claude Code matches tool names against a string pattern."""
    assert all(isinstance(group["matcher"], str) for group, _ in _entries())


def test_no_hook_reads_tool_input_from_the_environment() -> None:
    """Tool input arrives on stdin; no CLAUDE_TOOL_* variable is set."""
    assert not any("CLAUDE_TOOL_" in hook["command"] for _, hook in _entries())


def test_the_tdd_hook_fires_only_on_git_commit() -> None:
    """The ``if`` field sits on the hook entry, beside ``command``."""
    [(group, hook)] = _entries()
    assert group["matcher"] == "Bash"
    assert hook["if"] == "Bash(git commit*)"
