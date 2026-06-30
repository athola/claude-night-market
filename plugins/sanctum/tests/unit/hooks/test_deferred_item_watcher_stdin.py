"""Input-contract tests for deferred_item_watcher: payload arrives on stdin.

Claude Code delivers the PostToolUse payload (``tool_name``,
``tool_input``, ``tool_response``) as JSON on stdin. The hook previously
read only the non-existent ``CLAUDE_TOOL_*`` env vars, so deferral signals
in real skill outputs never reached the ledger.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import deferred_item_watcher as mod


class _FakeStdin(io.StringIO):
    """A stdin stand-in that reports as a pipe, not a terminal."""

    def isatty(self) -> bool:
        return False


def _stdin(payload: dict) -> _FakeStdin:
    return _FakeStdin(json.dumps(payload))


def _clear_legacy_env(monkeypatch) -> None:
    for key in ("CLAUDE_TOOL_NAME", "CLAUDE_TOOL_INPUT", "CLAUDE_TOOL_OUTPUT"):
        monkeypatch.delenv(key, raising=False)


def test_writes_ledger_from_stdin_payload(tmp_path: Path, monkeypatch) -> None:
    """A watched-skill payload on stdin writes a ledger entry.

    GIVEN a valid PostToolUse JSON payload on stdin
    AND the tool_name is Skill and the skill is in WATCH_LIST
    AND the tool_response contains a [Deferred] marker
    WHEN main() runs
    THEN a ledger entry is written with the correct title and source
    """
    _clear_legacy_env(monkeypatch)
    ledger_path = tmp_path / "deferred-items-session.json"
    payload = {
        "tool_name": "Skill",
        "tool_input": {"skill": "war-room"},
        "tool_response": "[Deferred] Add OAuth support\nSome other text.",
    }
    with (
        patch.object(mod.sys, "stdin", _stdin(payload)),
        patch.object(mod, "get_ledger_path", return_value=ledger_path),
    ):
        try:
            mod.main()
        except SystemExit as exc:
            # The success path returns normally; an early skip-exit before
            # writing is caught here so the ledger assertion below fails
            # cleanly (genuine guard) rather than erroring on SystemExit.
            assert exc.code == 0, f"unexpected exit code: {exc.code}"

    assert ledger_path.exists(), (
        "watched-skill deferral did not write a ledger; "
        "payload likely not read from stdin"
    )
    entries = json.loads(ledger_path.read_text())
    assert len(entries) == 1
    assert entries[0]["title"] == "Add OAuth support"
    assert entries[0]["source"] == "war-room"


def test_non_watched_skill_from_stdin_writes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """A non-watched skill payload on stdin writes no ledger.

    GIVEN a valid PostToolUse JSON payload on stdin
    AND the tool_name is Skill but the skill is NOT in WATCH_LIST
    WHEN main() runs
    THEN no ledger file is created
    AND the process exits with code 0
    """
    _clear_legacy_env(monkeypatch)
    ledger_path = tmp_path / "deferred-items-session.json"
    payload = {
        "tool_name": "Skill",
        "tool_input": {"skill": "commit-messages"},
        "tool_response": "[Deferred] Some item",
    }
    with (
        patch.object(mod.sys, "stdin", _stdin(payload)),
        patch.object(mod, "get_ledger_path", return_value=ledger_path),
    ):
        try:
            mod.main()
        except SystemExit as exc:
            assert exc.code == 0
    assert not ledger_path.exists()


# ---------------------------------------------------------------------------
# OSError / ValueError on stdin read in read_payload()
# ---------------------------------------------------------------------------


class _ErrorStdin:
    """Stdin stand-in that is not a tty and raises OSError on read."""

    def isatty(self) -> bool:
        return False

    def read(self) -> str:
        raise OSError("stdin pipe broken")


def test_oserror_on_stdin_read_falls_back_to_env(monkeypatch) -> None:
    """OSError reading stdin makes read_payload fall back to CLAUDE_TOOL_* env vars.

    GIVEN stdin that raises OSError when read
    AND CLAUDE_TOOL_* env vars carry a valid Skill payload
    WHEN read_payload is called
    THEN the env-var fallback payload is returned with correct fields
    """
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Skill")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"skill": "war-room"}))
    monkeypatch.setenv("CLAUDE_TOOL_OUTPUT", "env output")

    with patch.object(mod.sys, "stdin", _ErrorStdin()):
        payload = mod.read_payload()

    assert payload["tool_name"] == "Skill"
    assert payload["tool_input"] == {"skill": "war-room"}
    assert payload["tool_response"] == "env output"


# ---------------------------------------------------------------------------
# Invalid JSON in CLAUDE_TOOL_INPUT env var (lines 203-204)
# ---------------------------------------------------------------------------


class _TtyStdin:
    """Stdin stand-in that reports as a terminal (no piped data)."""

    def isatty(self) -> bool:
        return True


def test_invalid_json_tool_input_env_defaults_to_empty_dict(monkeypatch) -> None:
    """Invalid JSON in CLAUDE_TOOL_INPUT produces an empty tool_input dict.

    GIVEN stdin is a tty so no stdin payload is read
    AND CLAUDE_TOOL_INPUT contains malformed JSON
    WHEN read_payload is called
    THEN tool_input in the returned payload is an empty dict
    AND tool_name is taken from CLAUDE_TOOL_NAME as-is
    """
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Skill")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", "{not: valid: json}")
    monkeypatch.setenv("CLAUDE_TOOL_OUTPUT", "")

    with patch.object(mod.sys, "stdin", _TtyStdin()):
        payload = mod.read_payload()

    assert payload["tool_input"] == {}
    assert payload["tool_name"] == "Skill"


# ---------------------------------------------------------------------------
# Invalid JSON on stdin body: read_payload() decode fallback
# ---------------------------------------------------------------------------


def test_non_json_stdin_content_falls_back_to_env(monkeypatch) -> None:
    """Non-JSON content on stdin causes read_payload to use env-var fallback.

    GIVEN stdin is not a tty and contains text that is not valid JSON
    AND CLAUDE_TOOL_* env vars carry a valid Skill payload
    WHEN read_payload is called
    THEN the env-var fallback payload is returned with correct fields
    """
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Skill")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"skill": "brainstorm"}))
    monkeypatch.setenv("CLAUDE_TOOL_OUTPUT", "env fallback output")

    with patch.object(mod.sys, "stdin", _FakeStdin("this is not json {")):
        payload = mod.read_payload()

    assert payload["tool_name"] == "Skill"
    assert payload["tool_input"] == {"skill": "brainstorm"}
    assert payload["tool_response"] == "env fallback output"


# ---------------------------------------------------------------------------
# _response_text() non-serializable fallback: the return str(value) branch
# ---------------------------------------------------------------------------


def test_response_text_non_serializable_falls_back_to_str(monkeypatch) -> None:
    """_response_text falls back to str() for values json.dumps cannot handle.

    GIVEN a payload where tool_response is a value json.dumps cannot serialize
    WHEN _response_text is called
    THEN the string representation via str() is returned
    """

    class _Unserializable:
        def __str__(self) -> str:
            return "unserializable-repr"

    text = mod._response_text({"tool_response": _Unserializable()})
    assert isinstance(text, str)
    assert text == "unserializable-repr"
