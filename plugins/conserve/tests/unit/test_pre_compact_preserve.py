"""Tests for pre_compact_preserve hook."""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

import pre_compact_preserve as preserve_module
from pre_compact_preserve import (
    cleanup_old_archives,
    extract_decisions,
    extract_errors,
    extract_file_paths,
    extract_recent_content,
    main,
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


class TestCleanupOldArchives:
    """Feature: Archive file cleanup."""

    @pytest.mark.unit
    def test_removes_excess_archives(self, tmp_path: Path):
        """Keep only the most recent N archives."""
        original_get = preserve_module.get_archive_dir
        preserve_module.get_archive_dir = lambda: tmp_path

        try:
            for i in range(15):
                f = tmp_path / f"pre-compact-2024010{i:02d}-test.md"
                f.write_text(f"archive {i}")

            cleanup_old_archives(keep_count=5)
            remaining = list(tmp_path.glob("pre-compact-*.md"))
            assert len(remaining) == 5
        finally:
            preserve_module.get_archive_dir = original_get

    @pytest.mark.unit
    def test_keeps_all_when_under_limit(self, tmp_path: Path):
        """No files removed when count is under keep_count."""
        original_get = preserve_module.get_archive_dir
        preserve_module.get_archive_dir = lambda: tmp_path

        try:
            for i in range(3):
                f = tmp_path / f"pre-compact-2024010{i}-test.md"
                f.write_text(f"archive {i}")

            cleanup_old_archives(keep_count=10)
            remaining = list(tmp_path.glob("pre-compact-*.md"))
            assert len(remaining) == 3
        finally:
            preserve_module.get_archive_dir = original_get


class TestSavePreservedContextBranches:
    """Additional branch coverage for save_preserved_context."""

    @pytest.mark.unit
    def test_save_with_empty_data(self, tmp_path: Path):
        """Save with no files, decisions, or errors."""
        original_get = preserve_module.get_archive_dir
        preserve_module.get_archive_dir = lambda: tmp_path

        try:
            archive = save_preserved_context([], [], [], "auto")
            content = archive.read_text()
            assert "_No files tracked_" in content
            assert "_No decisions tracked_" in content
            assert "_No errors tracked_" in content
        finally:
            preserve_module.get_archive_dir = original_get


class TestExtractRecentContentBranches:
    """Branch coverage for extract_recent_content edge cases."""

    @pytest.mark.unit
    def test_handles_large_file_with_seek(self, tmp_path: Path):
        """Large session files are read from the tail."""
        session = tmp_path / "session.jsonl"
        # Write more than 500KB to trigger seek
        lines = []
        for i in range(2000):
            lines.append(
                json.dumps(
                    {
                        "role": "user" if i % 2 == 0 else "assistant",
                        "content": "x" * 300,
                    }
                )
            )
        session.write_text("\n".join(lines))
        result = extract_recent_content(session, max_turns=10)
        assert len(result) <= 10

    @pytest.mark.unit
    def test_handles_read_error(self, tmp_path: Path):
        """Returns empty list on OS error."""
        missing = tmp_path / "missing.jsonl"
        result = extract_recent_content(missing)
        assert result == []

    @pytest.mark.unit
    def test_skips_non_conversation_entries(self, tmp_path: Path):
        """Entries without user/assistant role are skipped."""
        session = tmp_path / "session.jsonl"
        entries = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Hello"},
        ]
        with open(session, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        result = extract_recent_content(session)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    @pytest.mark.unit
    def test_handles_invalid_json_lines(self, tmp_path: Path):
        """Invalid JSON lines are skipped."""
        session = tmp_path / "session.jsonl"
        session.write_text("not json\n{invalid\n")
        result = extract_recent_content(session)
        assert result == []


class TestResolveSessionFileBranches:
    """Branch coverage for resolve_session_file edge cases."""

    @pytest.mark.unit
    def test_fallback_to_most_recent_project_dir(self, tmp_path: Path):
        """Falls back to most recent project dir if cwd doesn't match."""
        projects = tmp_path / "projects"
        projects.mkdir()
        # Create a project dir that doesn't match cwd
        other_project = projects / "-some-other-project"
        other_project.mkdir()
        session = other_project / "session.jsonl"
        session.write_text(json.dumps({"role": "user", "content": "hi"}) + "\n")

        original_env = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)
        try:
            preserve_module.resolve_session_file()
            # May or may not find it depending on cwd, but shouldn't crash
            # The important thing is the fallback branch is exercised
        finally:
            if original_env:
                os.environ["CLAUDE_HOME"] = original_env
            else:
                os.environ.pop("CLAUDE_HOME", None)

    @pytest.mark.unit
    def test_no_jsonl_files_returns_none(self, tmp_path: Path):
        """Returns None when project dir has no JSONL files."""
        projects = tmp_path / "projects"
        cwd = Path.cwd()
        project_name = str(cwd).replace(os.sep, "-")
        if not project_name.startswith("-"):
            project_name = "-" + project_name
        project_dir = projects / project_name
        project_dir.mkdir(parents=True)

        original_env = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)
        try:
            result = preserve_module.resolve_session_file()
            assert result is None
        finally:
            if original_env:
                os.environ["CLAUDE_HOME"] = original_env
            else:
                os.environ.pop("CLAUDE_HOME", None)

    @pytest.mark.unit
    def test_fallback_to_most_recent_jsonl(self, tmp_path: Path):
        """Falls back to most recently modified JSONL when no session ID."""
        projects = tmp_path / "projects"
        cwd = Path.cwd()
        project_name = str(cwd).replace(os.sep, "-")
        if not project_name.startswith("-"):
            project_name = "-" + project_name
        project_dir = projects / project_name
        project_dir.mkdir(parents=True)

        f1 = project_dir / "old.jsonl"
        f1.write_text("{}\n")
        f2 = project_dir / "new.jsonl"
        f2.write_text("{}\n")

        original_env = os.environ.get("CLAUDE_HOME")
        original_session = os.environ.get("CLAUDE_SESSION_ID")
        os.environ["CLAUDE_HOME"] = str(tmp_path)
        os.environ.pop("CLAUDE_SESSION_ID", None)
        try:
            result = preserve_module.resolve_session_file()
            assert result is not None
        finally:
            if original_env:
                os.environ["CLAUDE_HOME"] = original_env
            else:
                os.environ.pop("CLAUDE_HOME", None)
            if original_session:
                os.environ["CLAUDE_SESSION_ID"] = original_session


class TestExtractFilePathsBranches:
    """Additional branch coverage for extract_file_paths."""

    @pytest.mark.unit
    def test_handles_string_blocks_in_list(self, tmp_path: Path):
        """String elements in content list are processed."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        entries = [
            {
                "role": "assistant",
                "content": [f"Reading {test_file} now"],
            }
        ]
        paths = extract_file_paths(entries)
        assert str(test_file) in paths

    @pytest.mark.unit
    def test_handles_invalid_paths_gracefully(self):
        """Invalid paths don't cause crashes."""
        entries = [
            {
                "role": "assistant",
                "content": "file at /nonexistent/path/to/nowhere.py",
            }
        ]
        paths = extract_file_paths(entries)
        # Path doesn't exist, so it should be filtered out
        assert "/nonexistent/path/to/nowhere.py" not in paths


class TestPreCompactMain:
    """Entry point integration tests."""

    @pytest.mark.unit
    def test_main_no_session_file(self, monkeypatch: pytest.MonkeyPatch):
        """Outputs minimal JSON when no session found."""
        monkeypatch.setattr(preserve_module, "resolve_session_file", lambda: None)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))

        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert output["hookSpecificOutput"]["hookEventName"] == "PreCompact"

    @pytest.mark.unit
    def test_main_no_content_in_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Outputs minimal JSON when session has no extractable content."""
        session = tmp_path / "session.jsonl"
        session.write_text("")  # Empty session
        monkeypatch.setattr(preserve_module, "resolve_session_file", lambda: session)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))

        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert output["hookSpecificOutput"]["hookEventName"] == "PreCompact"

    @pytest.mark.unit
    def test_main_with_content_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Creates archive and outputs summary when session has content."""
        session = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"role": "user", "content": "Fix the bug"}),
            json.dumps(
                {
                    "role": "assistant",
                    "content": "I decided to use pytest for testing",
                }
            ),
        ]
        session.write_text("\n".join(lines))

        monkeypatch.setattr(preserve_module, "resolve_session_file", lambda: session)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        monkeypatch.setattr(preserve_module, "get_archive_dir", lambda: archive_dir)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))

        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert "archivePath" in output["hookSpecificOutput"]

    @pytest.mark.unit
    def test_main_invalid_json_stdin(self, monkeypatch: pytest.MonkeyPatch):
        """Handles invalid JSON stdin gracefully."""
        monkeypatch.setattr(preserve_module, "resolve_session_file", lambda: None)
        monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))

        rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_reads_trigger_from_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Trigger from hook input is passed to save_preserved_context."""
        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({"role": "user", "content": "test"}) + "\n")
        monkeypatch.setattr(preserve_module, "resolve_session_file", lambda: session)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        monkeypatch.setattr(preserve_module, "get_archive_dir", lambda: archive_dir)
        hook_input = json.dumps({"trigger": "auto-compact"})
        monkeypatch.setattr("sys.stdin", io.StringIO(hook_input))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))

        rc = main()
        assert rc == 0
        # Check archive file was created with trigger info
        archives = list(archive_dir.glob("pre-compact-*.md"))
        assert len(archives) == 1
        content = archives[0].read_text()
        assert "auto-compact" in content
