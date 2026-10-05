"""Every shell-form hook command quotes ${CLAUDE_PLUGIN_ROOT}.

The placeholder expands to the plugin's install path. Unquoted, a path
with a space splits into several words and the hook fails to start; since
CLI 2.1.281 `claude plugin validate` warns on it. Exec form (`args`) needs
no quoting and is not a shell command.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UNQUOTED = re.compile(r'(?<!")\$\{CLAUDE_PLUGIN_ROOT\}')


def _commands():
    for hooks_file in sorted(REPO_ROOT.glob("plugins/*/hooks/hooks.json")):
        events = json.loads(hooks_file.read_text()).get("hooks", {})
        for event, groups in events.items():
            for group in groups:
                for handler in group.get("hooks", []):
                    command = handler.get("command")
                    if isinstance(command, str) and "args" not in handler:
                        yield hooks_file.relative_to(REPO_ROOT), event, command


def test_there_are_hook_commands_to_check() -> None:
    assert any("CLAUDE_PLUGIN_ROOT" in c for _, _, c in _commands())


def test_no_hook_command_leaves_the_plugin_root_unquoted() -> None:
    unquoted = [
        f"{path} {event}: {command}"
        for path, event, command in _commands()
        if UNQUOTED.search(command)
    ]
    assert unquoted == [], "\n".join(unquoted)
