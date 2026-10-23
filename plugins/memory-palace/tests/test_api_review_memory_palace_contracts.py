"""Contract tests for API-review findings on memory-palace hooks."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

_HOOKS = str(Path(__file__).resolve().parents[1] / "hooks")
if _HOOKS not in sys.path:
    sys.path.insert(0, _HOOKS)

import local_doc_processor  # noqa: E402 - sys.path modified above

NOTE_TEXT = "# Notes\n\nThis reference document explains the build pipeline. " * 3


def _run_read_hook(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tool_response: object,
) -> str:
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "docs/notes.md"},
        "tool_response": tool_response,
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(local_doc_processor, "is_known", lambda **_: False)
    monkeypatch.setattr(
        local_doc_processor, "_try_register_graph_entity", lambda **_: None
    )
    with pytest.raises(SystemExit) as exit_info:
        local_doc_processor.main()
    assert exit_info.value.code == 0
    return capsys.readouterr().out


def test_read_hook_extracts_content_from_file_content_shape(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    out = _run_read_hook(
        monkeypatch,
        capsys,
        {"type": "text", "file": {"filePath": "docs/notes.md", "content": NOTE_TEXT}},
    )
    assert (
        "Reading local knowledge doc"
        in json.loads(out)["hookSpecificOutput"]["additionalContext"]
    )


def test_read_hook_still_accepts_top_level_content(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    out = _run_read_hook(monkeypatch, capsys, {"content": NOTE_TEXT})
    assert "hookSpecificOutput" in json.loads(out)
