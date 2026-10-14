"""Tests for verify_workflow_complete hook - post-implementation reminders."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from hooks.verify_workflow_complete import REMINDER, main


def _user_prompt(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _tool_use(name: str) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "name": name, "input": {}}],
        },
    }


def _tool_result() -> dict:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1"}],
        },
    }


def _run(monkeypatch, capsys, payload: object) -> str:
    """Run the hook on ``payload`` and return what it printed."""
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    return capsys.readouterr().out


def _transcript(tmp_path: Path, rows: list[dict]) -> str:
    path = tmp_path / "session.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return str(path)


@pytest.mark.unit
@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit", "NotebookEdit"])
def test_reminder_shows_when_the_turn_edited_files(
    tool, tmp_path, monkeypatch, capsys
) -> None:
    rows = [_user_prompt("implement it"), _tool_use(tool), _tool_result()]
    out = _run(monkeypatch, capsys, {"transcript_path": _transcript(tmp_path, rows)})

    output = json.loads(out)
    assert output["systemMessage"] == REMINDER
    assert "decision" not in output


@pytest.mark.unit
def test_no_reminder_when_the_turn_only_read(tmp_path, monkeypatch, capsys) -> None:
    rows = [_user_prompt("what does x do?"), _tool_use("Read"), _tool_result()]
    out = _run(monkeypatch, capsys, {"transcript_path": _transcript(tmp_path, rows)})

    assert out == ""


@pytest.mark.unit
def test_edit_in_an_earlier_turn_does_not_repeat_the_reminder(
    tmp_path, monkeypatch, capsys
) -> None:
    rows = [
        _user_prompt("implement it"),
        _tool_use("Edit"),
        _tool_result(),
        _user_prompt("thanks, now explain it"),
        _tool_use("Read"),
        _tool_result(),
    ]
    out = _run(monkeypatch, capsys, {"transcript_path": _transcript(tmp_path, rows)})

    assert out == ""


@pytest.mark.unit
def test_no_reminder_while_a_stop_hook_is_already_continuing(
    tmp_path, monkeypatch, capsys
) -> None:
    rows = [_user_prompt("implement it"), _tool_use("Edit")]
    payload = {
        "transcript_path": _transcript(tmp_path, rows),
        "stop_hook_active": True,
    }

    assert _run(monkeypatch, capsys, payload) == ""


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    ["", "not json", [], {}, {"transcript_path": "/nonexistent/x.jsonl"}],
)
def test_no_reminder_without_a_readable_transcript(
    payload, monkeypatch, capsys
) -> None:
    assert _run(monkeypatch, capsys, payload) == ""


@pytest.mark.unit
def test_edit_in_a_large_transcript_tail_is_found(
    tmp_path, monkeypatch, capsys
) -> None:
    padding = [_tool_use("Read"), _tool_result()] * 4000
    rows = [_user_prompt("old"), *padding, _user_prompt("go"), _tool_use("Write")]
    out = _run(monkeypatch, capsys, {"transcript_path": _transcript(tmp_path, rows)})

    assert json.loads(out)["systemMessage"] == REMINDER


class TestReminderContent:
    """The checklist the hook shows after a turn that edited files."""

    @pytest.mark.unit
    def test_reminder_contains_proof_of_work_section(self) -> None:
        assert "PROOF-OF-WORK" in REMINDER
        assert "progress items" in REMINDER
        assert "proof:solution-tested" in REMINDER
        assert "proof:evidence-captured" in REMINDER
        assert "[E1]" in REMINDER

    @pytest.mark.unit
    def test_reminder_contains_documentation_updates(self) -> None:
        assert "Documentation Updates" in REMINDER
        for command in (
            "/sanctum:update-docs",
            "/abstract:make-dogfood",
            "/sanctum:update-readme",
            "/sanctum:update-tests",
        ):
            assert command in REMINDER

    @pytest.mark.unit
    def test_reminder_mentions_applicability_disclaimer(self) -> None:
        assert "not applicable" in REMINDER.lower()
        assert "simple fix" in REMINDER.lower()
