"""Tests for session discovery and listing.

Validates that list_sessions discovers .jsonl files, sorts by
modification time, extracts preview metadata, and respects limits.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from scribe.session_parser import list_sessions


def _make_session_file(
    directory: Path,
    name: str,
    records: list[dict[str, Any]],
    mtime_offset: float = 0.0,
) -> Path:
    """Write a JSONL session file and optionally set its mtime."""
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r) for r in records]
    path.write_text("\n".join(lines))
    if mtime_offset != 0.0:
        stat = path.stat()
        os.utime(path, (stat.st_atime + mtime_offset, stat.st_mtime + mtime_offset))
    return path


def _user_record(content: str | list[Any]) -> dict[str, Any]:
    """Build a user-type JSONL record."""
    return {"type": "user", "message": {"content": content}}


def _assistant_record(content: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an assistant-type JSONL record."""
    return {"type": "assistant", "message": {"content": content}}


class TestSessionDiscovery:
    """Feature: discover session JSONL files for interactive picking.

    As a session-replay user
    I want to list recent sessions from my projects directory
    So that I can pick a session without remembering file paths
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_sessions_finds_jsonl_files(self, tmp_path: Path) -> None:
        """Scenario: discovers .jsonl files in a directory tree.

        Given a directory structure with .jsonl files in subdirectories
        When listing sessions
        Then all .jsonl files are discovered
        """
        proj_a = tmp_path / "project-a"
        proj_b = tmp_path / "project-b"
        _make_session_file(
            proj_a,
            "session1.jsonl",
            [_user_record("hello")],
        )
        _make_session_file(
            proj_b,
            "session2.jsonl",
            [_user_record("world")],
        )

        sessions = list_sessions(base_dir=tmp_path)
        assert len(sessions) == 2
        paths = {s.path for s in sessions}
        assert proj_a / "session1.jsonl" in paths
        assert proj_b / "session2.jsonl" in paths

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_sessions_sorted_by_mtime(self, tmp_path: Path) -> None:
        """Scenario: sessions are sorted by modification time descending.

        Given three session files with different modification times
        When listing sessions
        Then the most recently modified file appears first
        """
        _make_session_file(
            tmp_path,
            "old.jsonl",
            [_user_record("old")],
            mtime_offset=-200.0,
        )
        _make_session_file(
            tmp_path,
            "newest.jsonl",
            [_user_record("newest")],
            mtime_offset=100.0,
        )
        _make_session_file(
            tmp_path,
            "middle.jsonl",
            [_user_record("middle")],
            mtime_offset=-50.0,
        )

        sessions = list_sessions(base_dir=tmp_path)
        assert len(sessions) == 3
        assert sessions[0].path.name == "newest.jsonl"
        assert sessions[1].path.name == "middle.jsonl"
        assert sessions[2].path.name == "old.jsonl"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_sessions_empty_directory(self, tmp_path: Path) -> None:
        """Scenario: empty directory returns empty list.

        Given a directory with no .jsonl files
        When listing sessions
        Then an empty list is returned
        """
        sessions = list_sessions(base_dir=tmp_path)
        assert sessions == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_info_fields(self, tmp_path: Path) -> None:
        """Scenario: SessionInfo has all expected fields.

        Given a session file with user turns
        When listing sessions
        Then SessionInfo contains path, modified, first_user_message,
             turn_count, and project_name
        """
        proj = tmp_path / "my-project"
        records = [
            _user_record("implement auth"),
            _assistant_record([{"type": "text", "text": "OK"}]),
            _user_record("add tests"),
        ]
        _make_session_file(proj, "session.jsonl", records)

        sessions = list_sessions(base_dir=tmp_path)
        assert len(sessions) == 1
        info = sessions[0]
        assert info.path == proj / "session.jsonl"
        assert isinstance(info.modified, float)
        assert info.modified > 0
        assert info.first_user_message == "implement auth"
        assert info.turn_count == 2
        assert info.project_name == "my-project"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_first_user_message_extraction(self, tmp_path: Path) -> None:
        """Scenario: extracts the first user message with string content.

        Given a session file where the first record is a system record
              followed by a user record with string content
        When listing sessions
        Then first_user_message is the string from the first user record
        """
        records = [
            {"type": "system", "message": {"content": "context"}},
            _user_record([{"type": "text", "text": "skill injection"}]),
            _user_record("actual question"),
            _assistant_record([{"type": "text", "text": "response"}]),
        ]
        _make_session_file(tmp_path, "session.jsonl", records)

        sessions = list_sessions(base_dir=tmp_path)
        assert sessions[0].first_user_message == "actual question"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_turn_count_extraction(self, tmp_path: Path) -> None:
        """Scenario: counts user records with string content as turns.

        Given a session with 3 user string messages and 1 tool result
        When listing sessions
        Then turn_count is 3 (tool results are not counted)
        """
        records = [
            _user_record("first"),
            _assistant_record([{"type": "text", "text": "r1"}]),
            _user_record("second"),
            _user_record(
                [{"type": "tool_result", "tool_use_id": "a", "content": "ok"}]
            ),
            _user_record("third"),
        ]
        _make_session_file(tmp_path, "session.jsonl", records)

        sessions = list_sessions(base_dir=tmp_path)
        assert sessions[0].turn_count == 3

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_sessions_skips_non_jsonl(self, tmp_path: Path) -> None:
        """Scenario: non-.jsonl files are ignored.

        Given a directory with .json, .txt, and .jsonl files
        When listing sessions
        Then only the .jsonl file is returned
        """
        _make_session_file(tmp_path, "session.jsonl", [_user_record("hello")])
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "notes.txt").write_text("some notes")
        (tmp_path / "log.jsonl.bak").write_text("backup")

        sessions = list_sessions(base_dir=tmp_path)
        assert len(sessions) == 1
        assert sessions[0].path.suffix == ".jsonl"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_sessions_respects_limit(self, tmp_path: Path) -> None:
        """Scenario: limit parameter caps the number of results.

        Given 5 session files
        When listing sessions with limit=3
        Then only 3 sessions are returned (the most recent)
        """
        for i in range(5):
            _make_session_file(
                tmp_path,
                f"session{i}.jsonl",
                [_user_record(f"msg {i}")],
                mtime_offset=float(i * 10),
            )

        sessions = list_sessions(base_dir=tmp_path, limit=3)
        assert len(sessions) == 3
        # Most recent first (highest mtime_offset)
        assert sessions[0].path.name == "session4.jsonl"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_first_user_message_truncated(self, tmp_path: Path) -> None:
        """Scenario: long first user messages are truncated for display.

        Given a session where the first user message is very long
        When listing sessions
        Then first_user_message is truncated to 120 characters with ...
        """
        long_msg = "x" * 200
        _make_session_file(tmp_path, "session.jsonl", [_user_record(long_msg)])

        sessions = list_sessions(base_dir=tmp_path)
        assert len(sessions[0].first_user_message) <= 123  # 120 + "..."
        assert sessions[0].first_user_message.endswith("...")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_with_no_user_messages(self, tmp_path: Path) -> None:
        """Scenario: session file with no user string messages.

        Given a session file with only system and assistant records
        When listing sessions
        Then first_user_message is empty and turn_count is 0
        """
        records = [
            {"type": "system", "message": {"content": "context"}},
            _assistant_record([{"type": "text", "text": "response"}]),
        ]
        _make_session_file(tmp_path, "session.jsonl", records)

        sessions = list_sessions(base_dir=tmp_path)
        assert sessions[0].first_user_message == ""
        assert sessions[0].turn_count == 0
