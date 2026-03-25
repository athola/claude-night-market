"""Tests for tool_output_summarizer hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from tool_output_summarizer import (  # noqa: E402
    BLOAT_WARNING_THRESHOLD,
    assess_output_bloat,
    format_hook_output,
    get_session_output_size,
)


class TestToolOutputSummarizer:
    """Feature: Tool Output Summarization.

    As a Claude Code user
    I want warnings when tool outputs are accumulating bloat
    So that I can proactively manage context before hitting limits
    """

    @pytest.mark.unit
    def test_no_warning_for_small_outputs(self, tmp_path: Path):
        """Scenario: Small cumulative output generates no warning.

        Given cumulative output size is under threshold
        When the hook runs
        Then no warning is generated
        """
        # Arrange - small output size
        session_file = tmp_path / "session.jsonl"
        session_file.write_text("small content")

        # Act
        result = assess_output_bloat(session_file, BLOAT_WARNING_THRESHOLD + 1000)

        # Assert
        assert result["severity"] == "ok"

    @pytest.mark.unit
    def test_warning_for_approaching_threshold(self, tmp_path: Path):
        """Scenario: Output approaching threshold triggers warning.

        Given cumulative output size is 75% of threshold
        When the hook runs
        Then a warning is generated with recommendations
        """
        # Arrange - output at 80% of threshold in JSONL format
        session_file = tmp_path / "session.jsonl"
        large_content = "x" * int(BLOAT_WARNING_THRESHOLD * 0.8)
        entry = {
            "role": "assistant",
            "content": [{"type": "tool_result", "content": large_content}],
        }
        with open(session_file, "w") as f:
            f.write(json.dumps(entry) + "\n")

        # Act
        result = assess_output_bloat(session_file, BLOAT_WARNING_THRESHOLD)

        # Assert
        assert result["severity"] == "warning"
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    @pytest.mark.unit
    def test_critical_at_threshold(self, tmp_path: Path):
        """Scenario: Output at threshold triggers critical warning.

        Given cumulative output size exceeds threshold
        When the hook runs
        Then a critical warning is generated
        """
        # Arrange - output exceeds threshold in JSONL format
        session_file = tmp_path / "session.jsonl"
        large_content = "x" * (BLOAT_WARNING_THRESHOLD + 1000)
        entry = {
            "role": "assistant",
            "content": [{"type": "tool_result", "content": large_content}],
        }
        with open(session_file, "w") as f:
            f.write(json.dumps(entry) + "\n")

        # Act
        result = assess_output_bloat(session_file, BLOAT_WARNING_THRESHOLD)

        # Assert
        assert result["severity"] == "critical"
        assert "/clear" in str(result["recommendations"]).lower()

    @pytest.mark.unit
    def test_hook_output_format(self):
        """Scenario: Hook output is properly formatted.

        Given a bloat assessment result
        When formatted for hook output
        Then it contains hookSpecificOutput with correct structure
        """
        # Arrange
        assessment = {
            "severity": "warning",
            "bytes_accumulated": 50000,
            "threshold": 100000,
            "recommendations": ["Consider clearing context"],
        }

        # Act
        output = format_hook_output(assessment)

        # Assert
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert "additionalContext" in output["hookSpecificOutput"]

    @pytest.mark.unit
    def test_tracks_cumulative_across_tools(self, tmp_path: Path):
        """Scenario: Hook tracks cumulative output across multiple tool calls.

        Given multiple tool calls have accumulated output
        When the hook runs
        Then it reports total accumulated size
        """
        # Arrange - simulate session with multiple tool outputs
        session_file = tmp_path / "session.jsonl"
        entries = [
            {"role": "user", "content": "read file"},
            {
                "role": "assistant",
                "content": [{"type": "tool_result", "content": "x" * 1000}],
            },
            {"role": "user", "content": "another read"},
            {
                "role": "assistant",
                "content": [{"type": "tool_result", "content": "y" * 2000}],
            },
        ]
        with open(session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Act
        size = get_session_output_size(session_file)

        # Assert - should count tool result content
        assert size >= 3000  # At least the content we added

    @pytest.mark.unit
    def test_resolve_session_file_returns_none_when_no_projects(self, tmp_path: Path):
        """Scenario: Session file resolution returns None when no projects exist.

        Given CLAUDE_HOME points to a directory without projects
        When resolve_session_file is called
        Then None is returned
        """
        # Arrange - set CLAUDE_HOME to temp directory without projects
        import os  # noqa: PLC0415

        import tool_output_summarizer as summarizer  # noqa: PLC0415

        original_env = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)

        try:
            # Act
            result = summarizer.resolve_session_file()

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
        import os  # noqa: PLC0415

        import tool_output_summarizer as summarizer  # noqa: PLC0415

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
            result = summarizer.resolve_session_file()

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
    def test_get_session_output_size_handles_list_content(self, tmp_path: Path):
        """Scenario: Output size handles list content with text items.

        Given session with tool_result containing list of text items
        When get_session_output_size is called
        Then all text content is counted
        """
        # Arrange - session with list content in tool_result
        session_file = tmp_path / "session.jsonl"
        entry = {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_result",
                    "content": [
                        {"text": "x" * 100},
                        {"text": "y" * 200},
                        "plain string content",
                    ],
                }
            ],
        }
        with open(session_file, "w") as f:
            f.write(json.dumps(entry) + "\n")

        # Act
        size = get_session_output_size(session_file)

        # Assert - should count all content
        assert size >= 300  # 100 + 200 + 20 chars
