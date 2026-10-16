"""Tests for verify_workflow_complete hook - post-implementation reminders."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from hooks.verify_workflow_complete import REMINDER, _turn_edited_files, main


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


_EDIT_ROW = json.dumps(
    {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {}}]},
    }
)


def _write_rows(path: Path, lines: list[str]) -> str:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_edit_is_found_past_a_line_that_is_not_json(tmp_path: Path) -> None:
    """A cut or garbled transcript line does not hide a later edit.

    GIVEN a transcript tail with an unparsable last line after an Edit row
    WHEN the turn is checked for file edits
    THEN the edit is found.
    """
    transcript = _write_rows(tmp_path / "t.jsonl", [_EDIT_ROW, "not json {"])

    assert _turn_edited_files(transcript) is True


def test_edit_is_found_past_a_row_that_is_not_an_object(tmp_path: Path) -> None:
    """A JSON line holding a list does not hide an earlier edit.

    GIVEN a transcript whose last line is a JSON array
    AND an Edit row before it
    WHEN the turn is checked for file edits
    THEN the edit is found.
    """
    transcript = _write_rows(tmp_path / "t.jsonl", [_EDIT_ROW, "[1, 2]"])

    assert _turn_edited_files(transcript) is True


def test_turn_without_prompt_or_edit_reports_no_edit(tmp_path: Path) -> None:
    """A transcript of assistant text alone has no edit to remind about.

    GIVEN a transcript holding only an assistant text row
    WHEN the turn is checked for file edits
    THEN no edit is reported.
    """
    text_row = json.dumps(
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}
    )
    transcript = _write_rows(tmp_path / "t.jsonl", [text_row])

    assert _turn_edited_files(transcript) is False
