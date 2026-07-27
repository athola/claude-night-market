"""BDD/TDD tests for the agent_dispatch_guard PreToolUse hook.

Tests follow the Given-When-Then pattern:

- Given: Precondition and context
- When: Action or event
- Then: Expected outcome

Claude Code resolves a subagent's model as: ``CLAUDE_CODE_SUBAGENT_MODEL``
env var, then the per-invocation ``model`` parameter, then the agent's
``model:`` frontmatter, then the main conversation's model. Dispatching
the Agent tool without a ``subagent_type`` therefore lands on the last
rung and inherits the session model, so a throwaway search runs on
whatever the parent is running on.

This hook denies such a dispatch and names the tier to pick instead.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PLUGIN_ROOT.parent.parent
_HOOK_PATH = _PLUGIN_ROOT / "hooks" / "agent_dispatch_guard.py"

sys.path.insert(0, str(_PLUGIN_ROOT / "hooks"))

from agent_dispatch_guard import (
    GUARDED_TOOLS,
    _read_payload,
    build_denial_message,
    evaluate,
    main,
)


def is_denial(result: dict) -> bool:
    """True when the hook payload denies the tool call."""
    specific = result.get("hookSpecificOutput", {})
    return specific.get("permissionDecision") == "deny"


def denial_reason(result: dict) -> str:
    """The human-facing reason attached to a denial payload."""
    return result["hookSpecificOutput"]["permissionDecisionReason"]


class TestGuardedTools:
    """The hook covers both the current and legacy dispatch tool names."""

    def test_guards_the_agent_tool(self) -> None:
        """Scenario: The current dispatch tool is named Agent
        Given the set of tools this guard covers
        When it is inspected
        Then Agent is guarded
        And a dispatch through it cannot skip the check
        """
        assert "Agent" in GUARDED_TOOLS

    def test_guards_the_legacy_task_tool(self) -> None:
        """Scenario: Older harness versions name the same tool Task
        Given the set of tools this guard covers
        When it is inspected
        Then Task is guarded
        And the legacy name gets the same protection as Agent
        """
        assert "Task" in GUARDED_TOOLS


class TestUnrelatedTools:
    """Non-dispatch tools pass through untouched."""

    @pytest.mark.parametrize("tool_name", ["Bash", "Read", "Edit", "Skill"])
    def test_should_allow_when_tool_is_not_a_dispatch(self, tool_name: str) -> None:
        """Scenario: A non-dispatch tool is invoked
        Given a tool that does not spawn a subagent
        When the guard evaluates the call
        Then it returns an empty payload and blocks nothing
        """
        assert evaluate(tool_name, {"command": "ls"}) == {}


class TestMissingSubagentType:
    """A dispatch with no named agent is denied."""

    def test_should_deny_when_subagent_type_is_absent(self) -> None:
        """Scenario: Agent dispatched with no subagent_type
        Given an Agent call carrying only a prompt
        When the guard evaluates the call
        Then it denies the call
        And the subagent never reaches the inheritance rung
        """
        result = evaluate("Agent", {"prompt": "find the config loader"})
        assert is_denial(result)

    def test_should_deny_when_subagent_type_is_empty(self) -> None:
        """Scenario: subagent_type present but blank
        Given an Agent call whose subagent_type is an empty string
        When the guard evaluates the call
        Then it denies the call
        And whitespace is not accepted as naming an agent
        """
        assert is_denial(evaluate("Agent", {"subagent_type": "   "}))

    def test_should_deny_legacy_task_dispatch_without_type(self) -> None:
        """Scenario: Legacy Task tool dispatched with no subagent_type
        Given a Task call carrying only a prompt
        When the guard evaluates the call
        Then it denies the call
        And the legacy tool name is covered too
        """
        assert is_denial(evaluate("Task", {"prompt": "audit the tests"}))

    def test_should_allow_when_subagent_type_is_named(self) -> None:
        """Scenario: Agent dispatched with an explicit agent name
        Given an Agent call naming a registered agent
        When the guard evaluates the call
        Then it returns an empty payload and blocks nothing
        """
        result = evaluate(
            "Agent", {"prompt": "review this", "subagent_type": "pensive:code-reviewer"}
        )
        assert result == {}

    @pytest.mark.parametrize(
        "subagent_type", [None, 0, 123, True, ["Explore"], {"name": "Explore"}]
    )
    def test_should_deny_when_subagent_type_is_not_a_string(
        self, subagent_type: object
    ) -> None:
        """Scenario: subagent_type carries a non-string value
        Given an Agent call whose subagent_type is not a string
        When the guard evaluates the call
        Then it denies the call
        And a value the harness cannot resolve to an agent counts as absent
        """
        assert is_denial(evaluate("Agent", {"subagent_type": subagent_type}))

    def test_should_allow_when_tool_input_is_malformed(self) -> None:
        """Scenario: tool_input is not a mapping
        Given a payload whose tool_input is not a dict
        When the guard evaluates the call
        Then it declines to block rather than guessing
        And an uninterpretable payload never wedges a dispatch
        """
        assert evaluate("Agent", "not-a-dict") == {}


class TestDenialMessage:
    """The denial explains which tier to pick for which task shape."""

    def test_names_every_model_tier(self) -> None:
        """Scenario: An author reads the denial
        Given the denial message
        When they look for guidance
        Then all three tier aliases are named
        And the author can pick one without leaving the message
        """
        message = build_denial_message()
        for alias in ("haiku", "sonnet", "opus"):
            assert alias in message

    def test_explains_the_inheritance_hazard(self) -> None:
        """Scenario: The denial justifies itself
        Given the denial message
        When the author asks why an unnamed dispatch matters
        Then the message states that the subagent inherits the session model
        And the denial justifies itself rather than only forbidding
        """
        assert "inherit" in build_denial_message().lower()

    def test_points_at_the_matrix_document(self) -> None:
        """Scenario: The author wants the full roster
        Given the denial message
        When they look for the canonical reference
        Then the matrix document is cited
        And the full roster is one path away
        """
        assert "docs/agent-model-matrix.md" in build_denial_message()

    def test_is_reachable_from_a_denial_payload(self) -> None:
        """Scenario: The denial payload carries the guidance
        Given an Agent call with no subagent_type
        When the guard denies it
        Then the reason is the full denial message
        And no guidance is lost between the check and the payload
        """
        result = evaluate("Agent", {"prompt": "go"})
        assert denial_reason(result) == build_denial_message()


class TestHookExecution:
    """End-to-end behavior through the real stdin/stdout contract."""

    def run_hook(self, payload: dict) -> dict:
        """Run the hook as a subprocess and parse its stdout JSON."""
        completed = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    def test_should_deny_end_to_end_without_subagent_type(self) -> None:
        """Scenario: The harness invokes the hook for real
        Given a PreToolUse payload for an Agent call with no subagent_type
        When the hook runs as a subprocess
        Then stdout carries a deny decision
        And the real stdin contract is exercised end to end
        """
        result = self.run_hook(
            {
                "tool_name": "Agent",
                "tool_input": {"prompt": "search the repo"},
                "hook_event_name": "PreToolUse",
            }
        )
        assert is_denial(result)

    def test_should_allow_end_to_end_with_subagent_type(self) -> None:
        """Scenario: The harness invokes the hook for a well-formed dispatch
        Given a PreToolUse payload naming an agent
        When the hook runs as a subprocess
        Then stdout carries no decision
        And a well-formed dispatch is never delayed
        """
        result = self.run_hook(
            {
                "tool_name": "Agent",
                "tool_input": {"prompt": "search", "subagent_type": "Explore"},
                "hook_event_name": "PreToolUse",
            }
        )
        assert result == {}

    def test_should_exit_zero_on_malformed_stdin(self) -> None:
        """Scenario: The hook receives garbage
        Given stdin that is not valid JSON
        When the hook runs
        Then it exits zero rather than blocking every dispatch
        And a broken guard fails open, not closed
        """
        completed = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert completed.returncode == 0

    def test_should_emit_an_empty_decision_when_it_crashes(self) -> None:
        """Scenario: The guard itself fails
        Given stdin that makes payload parsing raise
        When the hook runs
        Then stdout still parses as an empty decision
        And the diagnostic goes to stderr where it cannot corrupt the decision

        A hook whose stdout is unparseable is worse than one that allows:
        the harness cannot tell "allow" from "broken".
        """
        completed = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input="{not json",
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert json.loads(completed.stdout) == {}
        assert "agent_dispatch_guard" in completed.stderr

    def test_should_allow_when_the_payload_is_not_a_mapping(self) -> None:
        """Scenario: stdin carries valid JSON that is not an object
        Given a payload that parses to a list rather than a mapping
        When the hook runs
        Then it emits an empty decision
        And a shape it cannot interpret never blocks a dispatch
        """
        completed = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input=json.dumps(["Agent", {"prompt": "go"}]),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert completed.returncode == 0
        assert json.loads(completed.stdout) == {}


class TestLegacyEnvironmentPayload:
    """The pre-stdin harness contract still resolves a payload.

    ``_read_payload`` falls back to ``CLAUDE_TOOL_NAME`` and
    ``CLAUDE_TOOL_INPUT`` when stdin is empty. Nothing exercised that
    branch, so the fallback could rot unnoticed until an older harness
    ran the guard and every dispatch sailed through unchecked.
    """

    @staticmethod
    def _silence_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
        """Present an empty, non-tty stdin so the env fallback is reached."""
        monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    def test_stdin_wins_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Both stdin and the legacy env vars carry a call
        Given a stdin payload and a conflicting CLAUDE_TOOL_NAME
        When the payload is read
        Then stdin wins
        And the fallback never overrides the current contract
        """
        stdin = io.StringIO(json.dumps({"tool_name": "Read"}))
        monkeypatch.setattr(sys, "stdin", stdin)
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        assert _read_payload()["tool_name"] == "Read"

    def test_discards_stdin_json_that_is_not_a_mapping(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: stdin parses to a list rather than an object
        Given stdin carrying a JSON array
        When the payload is read
        Then an empty mapping is returned
        And the env fallback is not consulted for a payload that arrived

        Reading a shape it cannot interpret must not silently promote the
        environment, or a stale env var would decide a live dispatch.
        """
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(["Agent"])))
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        assert _read_payload() == {}

    def test_reads_the_dispatch_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: An older harness passes the call in env vars
        Given empty stdin and CLAUDE_TOOL_NAME/CLAUDE_TOOL_INPUT set
        When the payload is read
        Then the tool name comes from the environment
        And the tool input is the parsed JSON
        """
        self._silence_stdin(monkeypatch)
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"prompt": "go"}))
        payload = _read_payload()
        assert payload["tool_name"] == "Agent"
        assert payload["tool_input"] == {"prompt": "go"}

    def test_env_sourced_dispatch_without_a_type_is_still_denied(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: The legacy path must enforce the same rule
        Given an env-sourced Agent call naming no agent
        When main runs
        Then the printed decision denies the call
        And the fallback path is not an enforcement bypass
        """
        self._silence_stdin(monkeypatch)
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"prompt": "go"}))
        main()
        assert is_denial(json.loads(capsys.readouterr().out))

    def test_tolerates_malformed_environment_json(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: CLAUDE_TOOL_INPUT is not valid JSON
        Given empty stdin and an unparseable CLAUDE_TOOL_INPUT
        When the payload is read
        Then the tool input degrades to an empty mapping
        And no exception escapes
        """
        self._silence_stdin(monkeypatch)
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", "{not json")
        assert _read_payload()["tool_input"] == {}

    def test_discards_environment_json_that_is_not_a_mapping(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: CLAUDE_TOOL_INPUT parses to a list
        Given empty stdin and CLAUDE_TOOL_INPUT set to a JSON array
        When the payload is read
        Then the tool input degrades to an empty mapping
        And a wrong-shaped value is not passed downstream
        """
        self._silence_stdin(monkeypatch)
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Agent")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps(["prompt"]))
        assert _read_payload()["tool_input"] == {}

    def test_defaults_to_an_unnamed_tool_when_nothing_is_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Neither stdin nor the environment carries a call
        Given empty stdin and no CLAUDE_TOOL_* variables
        When the payload is read
        Then the tool name is empty
        And an empty tool name guards nothing rather than blocking everything
        """
        self._silence_stdin(monkeypatch)
        monkeypatch.delenv("CLAUDE_TOOL_NAME", raising=False)
        monkeypatch.delenv("CLAUDE_TOOL_INPUT", raising=False)
        payload = _read_payload()
        assert payload["tool_name"] == ""
        assert evaluate(payload["tool_name"], payload["tool_input"]) == {}


class TestDenialMessageStaysTrue:
    """The agents the denial recommends actually exist.

    Encodes the invariant that guidance is checked against reality. The
    guide this hook replaced rotted because a hand-maintained agent list
    had nothing comparing it to disk; a denial that recommends a deleted
    agent teaches the reader to dispatch something that does not resolve.

    If this test breaks, an agent named in the message was renamed or
    removed. Present three options to a human rather than editing the
    assertion:

    1. Preserve: restore the agent, keep the recommendation accurate.
    2. Layer: cite the agent's replacement in the denial message.
    3. Revise: drop the example if that tier no longer needs one.
    """

    @staticmethod
    def _agent_slugs_on_disk() -> set[str]:
        """Every ``plugin:agent`` slug shipped under ``plugins/*/agents/``."""
        return {
            f"{path.parent.parent.name}:{path.stem}"
            for path in (_REPO_ROOT / "plugins").glob("*/agents/**/*.md")
            if ".venv" not in path.parts
        }

    def test_cites_at_least_one_agent_per_tier(self) -> None:
        """Scenario: A reader needs a concrete starting point
        Given the denial message
        When its example slugs are extracted
        Then several agents are named
        And the reader is not left to invent a subagent_type
        """
        cited = set(re.findall(r"\b[a-z0-9-]+:[a-z0-9-]+\b", build_denial_message()))
        assert len(cited & self._agent_slugs_on_disk()) >= 3

    def test_every_agent_it_recommends_exists_on_disk(self) -> None:
        """Scenario: An agent named in the guidance was deleted or renamed
        Given every slug the denial message cites as an example
        When each is compared against the agents on disk
        Then all of them resolve to a real agent definition
        And the guidance cannot recommend a dispatch that fails
        """
        on_disk = self._agent_slugs_on_disk()
        cited = set(re.findall(r"\b[a-z0-9-]+:[a-z0-9-]+\b", build_denial_message()))
        # Slugs that name no plugin directory are prose, not recommendations.
        plugins = {slug.split(":")[0] for slug in on_disk}
        recommended = {slug for slug in cited if slug.split(":")[0] in plugins}
        assert recommended, "the denial message names no agents at all"
        assert sorted(recommended - on_disk) == []
