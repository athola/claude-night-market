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
    """A watched-skill payload on stdin writes a ledger entry."""
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
        mod.main()

    entries = json.loads(ledger_path.read_text())
    assert len(entries) == 1
    assert entries[0]["title"] == "Add OAuth support"
    assert entries[0]["source"] == "war-room"


def test_non_watched_skill_from_stdin_writes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """A non-watched skill payload on stdin writes no ledger."""
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
