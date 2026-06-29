"""Unit tests for the shared hook payload reader (``shared.hook_io``).

Locks the input contract: stdin JSON is the primary channel, the legacy
``CLAUDE_TOOL_*`` env vars are a fallback, and ``tool_input`` /
``tool_response`` are normalized for downstream callers.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

_HOOK_IO = Path(__file__).resolve().parents[2] / "hooks" / "shared" / "hook_io.py"
_spec = importlib.util.spec_from_file_location("hook_io", _HOOK_IO)
assert _spec and _spec.loader
hook_io = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook_io)


@pytest.fixture(autouse=True)
def _clear_legacy_env(monkeypatch):
    for key in (
        "CLAUDE_TOOL_NAME",
        "CLAUDE_TOOL_INPUT",
        "CLAUDE_TOOL_OUTPUT",
        "CLAUDE_SESSION_ID",
    ):
        monkeypatch.delenv(key, raising=False)


class _FakeStdin(io.StringIO):
    """A stdin stand-in that reports as a pipe, not a terminal."""

    def isatty(self) -> bool:
        return False


def _feed_stdin(monkeypatch, text: str) -> None:
    monkeypatch.setattr(hook_io.sys, "stdin", _FakeStdin(text))


class _ExplodingStdin:
    """A non-tty stdin whose ``read()`` raises, exercising the OSError guard."""

    def isatty(self) -> bool:
        return False

    def read(self) -> str:
        raise OSError("stream closed")


class _TerminalStdin:
    """A stdin that reports as a terminal, so the read branch is skipped."""

    def isatty(self) -> bool:
        return True

    def read(self) -> str:
        raise AssertionError("read() must not run when stdin is a tty")


def test_reads_payload_from_stdin(monkeypatch):
    """Given a JSON payload on stdin, fields are returned verbatim."""
    _feed_stdin(
        monkeypatch,
        json.dumps(
            {
                "tool_name": "Skill",
                "tool_input": {"skill": "a:b"},
                "tool_response": {"ok": True},
                "session_id": "sid-123",
            }
        ),
    )
    payload = hook_io.read_hook_payload()
    assert payload["tool_name"] == "Skill"
    assert payload["tool_input"] == {"skill": "a:b"}
    assert payload["session_id"] == "sid-123"


def test_stdin_wins_over_legacy_env(monkeypatch):
    """Stdin is authoritative even when legacy env vars are also set."""
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    _feed_stdin(monkeypatch, json.dumps({"tool_name": "Skill"}))
    assert hook_io.read_hook_payload()["tool_name"] == "Skill"


def test_falls_back_to_legacy_env_when_stdin_empty(monkeypatch):
    """Empty stdin falls back to CLAUDE_TOOL_* env vars (test harness path)."""
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Skill")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"skill": "x:y"}))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "env-sid")
    _feed_stdin(monkeypatch, "")
    payload = hook_io.read_hook_payload()
    assert payload["tool_name"] == "Skill"
    assert payload["tool_input"] == {"skill": "x:y"}
    assert payload["session_id"] == "env-sid"


def test_tool_input_string_is_coerced_to_dict(monkeypatch):
    """A stringified tool_input (legacy shape) is parsed to a dict."""
    _feed_stdin(
        monkeypatch,
        json.dumps({"tool_name": "Skill", "tool_input": '{"skill": "p:q"}'}),
    )
    assert hook_io.read_hook_payload()["tool_input"] == {"skill": "p:q"}


def test_session_id_defaults_to_unknown(monkeypatch):
    """Missing session id resolves to 'unknown', never empty."""
    _feed_stdin(monkeypatch, json.dumps({"tool_name": "Skill"}))
    assert hook_io.read_hook_payload()["session_id"] == "unknown"


def test_tool_response_text_stringifies_dict():
    """tool_response_text renders a dict response as JSON text."""
    payload = {"tool_response": {"error": "boom"}}
    assert "boom" in hook_io.tool_response_text(payload)


def test_tool_response_text_passes_through_string():
    assert hook_io.tool_response_text({"tool_response": "plain"}) == "plain"


def test_malformed_stdin_falls_back(monkeypatch):
    """Non-JSON stdin does not crash; it falls back to env defaults."""
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Edit")
    _feed_stdin(monkeypatch, "not json {{{")
    assert hook_io.read_hook_payload()["tool_name"] == "Edit"


def test_tool_input_invalid_json_string_collapses_to_empty(monkeypatch):
    """An invalid-JSON tool_input string collapses to {} instead of raising."""
    _feed_stdin(monkeypatch, json.dumps({"tool_input": "not json{{{"}))
    assert hook_io.read_hook_payload()["tool_input"] == {}


def test_tool_input_json_array_collapses_to_empty(monkeypatch):
    """A tool_input JSON array (non-dict) collapses to {} by the lenient contract."""
    _feed_stdin(monkeypatch, json.dumps({"tool_input": "[1, 2, 3]"}))
    assert hook_io.read_hook_payload()["tool_input"] == {}


def test_tool_input_native_non_string_collapses_to_empty(monkeypatch):
    """A native non-string tool_input (e.g. int) collapses to {} for callers."""
    _feed_stdin(monkeypatch, json.dumps({"tool_input": 42}))
    assert hook_io.read_hook_payload()["tool_input"] == {}


def test_stdin_read_error_falls_back_to_env(monkeypatch):
    """An OSError reading stdin falls back to the legacy env vars, not a crash."""
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setattr(hook_io.sys, "stdin", _ExplodingStdin())
    assert hook_io.read_hook_payload()["tool_name"] == "Bash"


def test_terminal_stdin_skips_read_and_falls_back(monkeypatch):
    """A tty stdin (no piped payload) skips read() and falls back to env vars."""
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Edit")
    monkeypatch.setattr(hook_io.sys, "stdin", _TerminalStdin())
    assert hook_io.read_hook_payload()["tool_name"] == "Edit"


def test_tool_response_text_non_serializable_falls_back_to_str():
    """A non-JSON-serializable tool_response renders via str(), never raising."""
    value = {1, 2, 3}  # set: not JSON serializable
    assert hook_io.tool_response_text({"tool_response": value}) == str(value)


def test_payload_contract_holds_on_minimal_stdin(monkeypatch):
    """Invariant: read_hook_payload always returns the full contract dict.

    Consumer hooks index tool_input / session_id directly and crash if the
    shape drifts. If this test must change, flag it for human review:
    preserve the contract, layer a new field, or revise it deliberately.
    """
    _feed_stdin(monkeypatch, json.dumps({"tool_name": "Skill"}))
    payload = hook_io.read_hook_payload()
    assert {"tool_name", "tool_input", "tool_response", "session_id"} <= set(payload)
    assert isinstance(payload["tool_input"], dict)
    assert isinstance(payload["session_id"], str) and payload["session_id"]


def test_explicit_null_fields_are_coerced_not_left_none(monkeypatch):
    """Explicit JSON null for tool_name/tool_response is coerced to ''.

    Guards the I5 fix: ``setdefault`` only fills *missing* keys, so an
    explicit ``null`` survived as None and would crash the next consumer
    that called a str method on it. Reverting to setdefault fails this.
    """
    _feed_stdin(
        monkeypatch,
        json.dumps({"tool_name": None, "tool_response": None}),
    )
    payload = hook_io.read_hook_payload()
    assert payload["tool_name"] == ""
    assert payload["tool_response"] == ""
