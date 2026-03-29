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
    plugin_root = Path(__file__).resolve().parents[2]
    hooks_json = plugin_root / "hooks" / "hooks.json"
    data = json.loads(hooks_json.read_text())

    commands: list[str] = []
    for hook_event_rules in (data.get("hooks") or {}).values():
        for rule in hook_event_rules:
            for hook in rule.get("hooks") or []:
                cmd = hook.get("command")
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
