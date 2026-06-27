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
