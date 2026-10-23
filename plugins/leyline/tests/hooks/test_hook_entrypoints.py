"""Tests for hook entrypoint executability and shebang lines."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Executable-bit checks not reliable on Windows",
)
def test_hook_entrypoints_are_executable() -> None:
    """Scenario: All hooks.json commands reference executable scripts with shebangs.

    Given the leyline hooks.json configuration
    When iterating all command-type hooks
    Then each referenced script exists, is executable, and starts with a shebang.
    """
    plugin_root = Path(__file__).resolve().parents[2]
    hooks_json = plugin_root / "hooks" / "hooks.json"
    data = json.loads(hooks_json.read_text())

    commands: list[str] = []
    for hook_event_rules in (data.get("hooks") or {}).values():
        for rule in hook_event_rules:
            for hook in rule.get("hooks") or []:
                cmd = hook.get("command")
                if isinstance(cmd, str):
                    cmd = cmd.replace('"', "")  # the plugin root is quoted
                if isinstance(cmd, str) and cmd.startswith(
                    "${CLAUDE_PLUGIN_ROOT}/hooks/"
                ):
                    commands.append(cmd.split("/hooks/", 1)[1])

    assert commands, "Expected at least one hook command in hooks.json"

    for rel in commands:
        path = plugin_root / "hooks" / rel
        assert path.exists(), f"Missing hook entrypoint: {rel}"
        assert os.access(path, os.X_OK), f"Hook entrypoint not executable: {rel}"
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line.startswith("#!"), f"Hook entrypoint missing shebang: {rel}"


def test_auto_star_does_not_hold_up_session_start() -> None:
    """auto-star-repo.sh makes a network call before it decides to prompt.

    Claude's first response waits for every synchronous SessionStart hook,
    so this one could hold it up to its 5 s timeout. With `async: true`
    the star prompt, its only `additionalContext`, is delivered "to Claude
    on the next conversation turn" once the process exits
    (https://code.claude.com/docs/en/hooks, "How async hooks execute").
    A prompt one turn late is the accepted cost. The hook prints its JSON
    on one line because a multi-line async response needs Claude Code
    v2.1.295 or later; test_hook_host_and_jq_edges.py pins that.
    """
    manifest = json.loads(
        (Path(__file__).parents[2] / "hooks" / "hooks.json").read_text()
    )
    handlers = [
        handler
        for group in manifest["hooks"]["SessionStart"]
        for handler in group["hooks"]
        if "auto-star-repo.sh" in handler["command"]
    ]
    assert len(handlers) == 1
    assert handlers[0].get("async") is True
