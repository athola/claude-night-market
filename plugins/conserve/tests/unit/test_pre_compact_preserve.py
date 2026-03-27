"""Tests for pre_compact_preserve hook."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

import pre_compact_preserve as preserve_module  # noqa: E402
from pre_compact_preserve import (  # noqa: E402
    extract_decisions,
    extract_errors,
    extract_file_paths,
    extract_recent_content,
    save_preserved_context,
)


class TestPreCompactPreserve:
    """Feature: PreCompact Context Preservation.

    As a Claude Code user
    I want my context preserved before compression
    So that I can recover critical information after compaction
    """

    @pytest.mark.unit
    def test_extract_file_paths_from_content(self, tmp_path: Path):
        """Scenario: File paths are extracted from conversation.

        Given conversation contains file paths
        When extraction runs
        Then valid file paths are returned
        """
        # Arrange - create a real file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        entries = [
            {
                "role": "assistant",
                "content": f"Let me read {test_file} for context",
            }
        ]

        # Act
        paths = extract_file_paths(entries)

        # Assert
        assert str(test_file) in paths

    @pytest.mark.unit
    def test_extract_decisions_from_content(self):
        """Scenario: Decisions are extracted from conversation.

        Given conversation contains decision statements
        When extraction runs
        Then decisions are returned
        """
        # Arrange
        entries = [
            {
                "role": "assistant",
                "content": "I decided to use pytest for testing because it's better",
            }
        ]

        # Act
        decisions = extract_decisions(entries)

        # Assert
        assert len(decisions) > 0
        assert "pytest" in decisions[0].lower()

    @pytest.mark.unit
    def test_extract_errors_from_content(self):
        """Scenario: Errors are extracted from conversation.

        Given conversation contains error messages
        When extraction runs
        Then errors are returned
        """
        # Arrange
        entries = [
            {
                "role": "user",
                "content": "Error: module not found when running tests",
            }
        ]

        # Act
        errors = extract_errors(entries)

        # Assert
        assert len(errors) > 0

    @pytest.mark.unit
    def test_save_preserved_context_creates_archive(self, tmp_path: Path):
        """Scenario: Archive file is created with preserved context.

        Given file paths, decisions, and errors to preserve
        When save_preserved_context is called
        Then an archive file is created with all content
        """
        # Arrange - create test file
        test_file = tmp_path / "example.py"
        test_file.write_text("# example")

        # Act - save with our temp path as archive dir
        original_get_archive = preserve_module.get_archive_dir
        preserve_module.get_archive_dir = lambda: tmp_path

        try:
            archive_file = save_preserved_context(
                [str(test_file)],
                ["Use pytest for testing"],
                ["Error: missing module"],
                "manual",
            )

            # Assert
            assert archive_file.exists()
            content = archive_file.read_text()
            assert str(test_file) in content
            assert "pytest" in content
            assert "missing module" in content
        finally:
            preserve_module.get_archive_dir = original_get_archive

    @pytest.mark.unit
    def test_extract_recent_content_handles_jsonl(self, tmp_path: Path):
        """Scenario: Recent content is extracted from JSONL session.

        Given a session file with JSONL entries
        When extract_recent_content is called
        Then recent entries are returned
        """
        # Arrange
        session_file = tmp_path / "session.jsonl"
        entries = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "Help me code"},
        ]
        with open(session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Act
        result = extract_recent_content(session_file, max_turns=10)

        # Assert
        assert len(result) == 3
        assert result[0]["role"] == "user"
        assert result[-1]["content"] == "Help me code"

    @pytest.mark.unit
    def test_resolve_session_file_returns_none_when_no_projects(self, tmp_path: Path):
        """Scenario: Session file resolution returns None when no projects exist.

        Given CLAUDE_HOME points to a directory without projects
        When resolve_session_file is called
        Then None is returned
        """
        original_env = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)

        try:
            # Act
            result = preserve_module.resolve_session_file()

            # Assert
            assert result is None
        finally:
            if original_env:
                os.environ["CLAUDE_HOME"] = original_env
            else:
                os.environ.pop("CLAUDE_HOME", None)

    @pytest.mark.unit
    def test_resolve_session_file_finds_by_session_id(self, tmp_path: Path):
        """Scenario: Session file resolution finds file by session ID.

        Given a project directory with multiple session files
        When resolve_session_file is called with CLAUDE_SESSION_ID
        Then the matching file is returned
        """
        # Arrange - create project structure
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        # Create project dir with cwd-style name
        cwd_path = tmp_path / "myproject"
        cwd_path.mkdir()
        project_dir_name = "-" + str(cwd_path).replace(os.sep, "-")
        project_dir = projects_dir / project_dir_name
        project_dir.mkdir()

        # Create session files
        target_file = project_dir / "session-123.jsonl"
        target_file.write_text('{"role": "user", "content": "test"}')
        other_file = project_dir / "session-456.jsonl"
        other_file.write_text('{"role": "user", "content": "other"}')

        original_home = os.environ.get("CLAUDE_HOME")
        original_session = os.environ.get("CLAUDE_SESSION_ID")
        original_cwd = os.getcwd()

        os.environ["CLAUDE_HOME"] = str(tmp_path)
        os.environ["CLAUDE_SESSION_ID"] = "session-123"

        try:
            # Act
            result = preserve_module.resolve_session_file()

            # Assert
            assert result is not None
            assert result.name == "session-123.jsonl"
        finally:
            if original_home:
                os.environ["CLAUDE_HOME"] = original_home
            else:
                os.environ.pop("CLAUDE_HOME", None)
            if original_session:
                os.environ["CLAUDE_SESSION_ID"] = original_session
            else:
                os.environ.pop("CLAUDE_SESSION_ID", None)
            os.chdir(original_cwd)

    @pytest.mark.unit
    def test_extract_file_paths_handles_list_content(self, tmp_path: Path):
        """Scenario: File path extraction handles list content blocks.

        Given conversation with file paths in content blocks
        When extract_file_paths is called
        Then paths are extracted from all content types
        """
        # Arrange - create a real file
        test_file = tmp_path / "example.py"
        test_file.write_text("# test")

        entries = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": f"Reading {test_file} for analysis"}
                ],
            }
        ]

        # Act
        paths = extract_file_paths(entries)

        # Assert
        assert str(test_file) in paths

    @pytest.mark.unit
    def test_extract_decisions_handles_list_content(self):
        """Scenario: Decision extraction handles list content blocks.

        Given conversation with decisions in content blocks
        When extract_decisions is called
        Then decisions are extracted from all content types
        """
        entries = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "I decided to use pytest for testing"}
                ],
            }
        ]

        # Act
        decisions = extract_decisions(entries)

        # Assert
        assert len(decisions) > 0
        assert "pytest" in decisions[0].lower()

    @pytest.mark.unit
    def test_extract_errors_handles_list_content(self):
        """Scenario: Error extraction handles list content blocks.

        Given conversation with errors in content blocks
        When extract_errors is called
        Then errors are extracted from all content types
        """
        entries = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Error: module not found when testing"}
                ],
            }
        ]

        # Act
        errors = extract_errors(entries)

        # Assert
        assert len(errors) > 0

    @pytest.mark.unit
    def test_get_archive_dir_creates_directory(self, tmp_path: Path):
        """Scenario: Archive directory is created if it doesn't exist.

        Given CLAUDE_HOME points to a temp directory
        When get_archive_dir is called
        Then the archive directory is created
        """
        original_env = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)

        try:
            # Act
            archive_dir = preserve_module.get_archive_dir()

            # Assert
            assert archive_dir.exists()
            assert archive_dir.name == "context-archive"
        finally:
            if original_env:
                os.environ["CLAUDE_HOME"] = original_env
            else:
                os.environ.pop("CLAUDE_HOME", None)
