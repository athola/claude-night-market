"""The `if` gates on gauntlet's Bash hooks admit every commit the hooks inspect.

Both hooks run only when the harness `if` rule admits the command. A rule
narrower than ``is_git_commit`` turns the challenge gate and the graph
refresh off silently for the forms it misses, such as ``git -C repo commit``.

Gate semantics as measured on Claude Code 2.1.245: the rule body is an
fnmatch glob, and a compound command is split so each segment is tested on
its own. The gate may admit more than the hook inspects, never less.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import pytest

from gauntlet.git_commands import is_git_commit

_HOOKS_JSON = Path(__file__).resolve().parents[2] / "hooks" / "hooks.json"
_SEGMENT_SEPARATORS = ("&&", "||", ";", "|")
_SCRIPTS = ["precommit_gate.py", "graph_auto_update.py"]


def _gates_for(script_name: str) -> list[str]:
    """Return every `if` rule registered against *script_name*."""
    config = json.loads(_HOOKS_JSON.read_text())
    rules = []
    for groups in config["hooks"].values():
        for group in groups:
            for entry in group["hooks"]:
                if script_name in entry.get("command", "") and "if" in entry:
                    rules.append(entry["if"])
    return rules


def _segments(command: str) -> list[str]:
    parts = [command]
    for sep in _SEGMENT_SEPARATORS:
        parts = [piece for part in parts for piece in part.split(sep)]
    return [part.strip() for part in parts if part.strip()]


def _gate_matches(rule: str, command: str) -> bool:
    """Mirror the measured harness rule: Bash(<glob>) per command segment."""
    assert rule.startswith("Bash(") and rule.endswith(")"), rule
    glob = rule[len("Bash(") : -1]
    return any(fnmatch.fnmatch(segment, glob) for segment in _segments(command))


def _any_gate_matches(script_name: str, command: str) -> bool:
    return any(_gate_matches(rule, command) for rule in _gates_for(script_name))


@pytest.mark.unit
@pytest.mark.parametrize("script", _SCRIPTS)
def test_every_commit_hook_declares_a_string_gate(script: str) -> None:
    """An array-valued `if` suppressed the hook outright when measured."""
    rules = _gates_for(script)
    assert rules, f"{script} has no `if` gate and spawns on every Bash call"
    assert all(isinstance(rule, str) for rule in rules)


@pytest.mark.unit
@pytest.mark.parametrize("script", _SCRIPTS)
@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x",
        "git commit --amend",
        "git add -A && git commit -m x",
        "cd repo && git commit -m x",
        "git status; git commit -m x",
        "git -C repo commit -m x",
        "git -c user.name=x commit -m x",
        "git --no-pager commit -m x",
    ],
)
def test_gate_admits_every_commit_the_hook_inspects(script: str, command: str) -> None:
    """A commit the hook recognizes but the gate refuses is never checked."""
    assert is_git_commit(command)
    assert _any_gate_matches(script, command)


@pytest.mark.unit
@pytest.mark.parametrize("script", _SCRIPTS)
@pytest.mark.parametrize(
    "command", ["git status", "git push", "ls -la", "cat README.md"]
)
def test_gate_skips_commands_the_hook_ignores(script: str, command: str) -> None:
    assert not is_git_commit(command)
    assert not _any_gate_matches(script, command)
