"""The `if` gates on imbue's PreToolUse:Bash hooks cover what the hooks inspect.

Three imbue hooks matched every Bash call and then exited early on almost
all of them. The harness can decide that without spawning a process, via
the hook-entry `if` field, but only if the registered rules are a superset
of what each hook's own parser recognizes. A rule that is narrower than
the parser turns a guard off silently, which for the package guard means a
typosquat install stops being checked.

These tests pin the superset relation. Adding an ecosystem to
``_INSTALL_HEADS`` without adding a gate fails here.

Gate semantics measured on Claude Code 2.1.245 (see
``docs/plans/hook-fanout-and-context-budget.md``): the rule body is an
fnmatch glob, and a compound command is split so each segment is tested
on its own.
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[3] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from shared.package_guard import (  # noqa: E402 - hooks/ must join sys.path above before its shared/ package resolves
    _INSTALL_HEADS,
    parse_packages,
)
from shared.vow_utils import (  # noqa: E402 - same sys.path ordering requirement
    is_git_commit,
)

_HOOKS_JSON = _HOOKS_DIR / "hooks.json"
_SEGMENT_SEPARATORS = ("&&", "||", ";", "|")

# One command per entry in _INSTALL_HEADS, in the same order. The count
# assertion below is what fails when an ecosystem is added upstream.
_INSTALL_COMMANDS = [
    "pip install reqeusts",
    "uv pip install reqeusts",
    "uv add reqeusts",
    "poetry add reqeusts",
    "npm install lodahs",
    "yarn add lodahs",
    "cargo add serd",
]

_EXTRA_INSTALL_COMMANDS = [
    "pip3 install reqeusts",
    "python3 -m pip install reqeusts",
    "pdm add reqeusts",
    "pnpm add lodahs",
    "npm i lodahs",
]

_UNRELATED_COMMANDS = [
    "ls -la",
    "cat README.md",
    "rg install src/",
    "git status",
]


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


class TestGatesAreRegisteredAsStrings:
    """An array-valued `if` suppressed the hook outright when measured."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "script",
        [
            "vow_no_ai_attribution.py",
            "vow_no_emoji_commits.py",
            "guard_package_hallucination.py",
        ],
    )
    def test_every_bash_hook_declares_at_least_one_string_gate(self, script):
        rules = _gates_for(script)
        assert rules, f"{script} has no `if` gate and spawns on every Bash call"
        assert all(isinstance(rule, str) for rule in rules)


class TestCommitVowGates:
    """Feature: the commit vows gate on exactly what is_git_commit accepts."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "script", ["vow_no_ai_attribution.py", "vow_no_emoji_commits.py"]
    )
    @pytest.mark.parametrize(
        "command",
        [
            'git commit -m "feat: thing"',
            "git commit --amend",
            'git add . && git commit -m "feat: thing"',
        ],
    )
    def test_gate_admits_commands_the_hook_inspects(self, script, command):
        assert _any_gate_matches(script, command)

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "script", ["vow_no_ai_attribution.py", "vow_no_emoji_commits.py"]
    )
    @pytest.mark.parametrize("command", _UNRELATED_COMMANDS)
    def test_gate_rejects_commands_the_hook_ignores(self, script, command):
        assert not is_git_commit(command)
        assert not _any_gate_matches(script, command)


class TestPackageGuardGates:
    """Feature: every ecosystem the guard parses has a gate admitting it."""

    _SCRIPT = "guard_package_hallucination.py"

    @pytest.mark.unit
    def test_one_sample_command_per_install_head(self):
        assert len(_INSTALL_COMMANDS) == len(_INSTALL_HEADS), (
            "_INSTALL_HEADS changed; add a sample command and a gate for the "
            "new ecosystem"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("command", _INSTALL_COMMANDS + _EXTRA_INSTALL_COMMANDS)
    def test_gate_admits_every_install_the_guard_parses(self, command):
        assert parse_packages(command), f"guard does not parse {command!r}"
        assert _any_gate_matches(self._SCRIPT, command), (
            f"{command!r} is inspected by the guard but no `if` gate admits "
            "it, so the guard would never run for it"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("command", _UNRELATED_COMMANDS)
    def test_gate_rejects_commands_the_guard_ignores(self, command):
        assert not parse_packages(command)
        assert not _any_gate_matches(self._SCRIPT, command)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_gate_admits_a_compound_install(self):
        command = "cd /tmp && pip install reqeusts"
        assert _any_gate_matches(self._SCRIPT, command)
