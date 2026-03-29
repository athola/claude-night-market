"""Tests for context warning session-file estimation logic.

Tests:
- estimate_context_from_session() fallback estimation
- _estimate_from_recent_turns() heuristic counting
- _find_current_session() session file selection
- _count_content() character/tool-result counting
- _resolve_session_file() orchestration
- _resolve_project_dir() path resolution
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

# Constants for PLR2004 magic values
ZERO = 0.0
HUNDRED = 100


@pytest.fixture(autouse=True)
def _clear_claude_home(monkeypatch):
    """Clear CLAUDE_HOME so tests use monkeypatched Path.home()."""
    monkeypatch.delenv("CLAUDE_HOME", raising=False)


class TestFallbackContextEstimation:
    """Feature: Fallback context estimation from session files.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_estimation_disabled_by_env(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Estimation can be disabled via environment variable."""
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_env_variable_takes_precedence(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: CLAUDE_CONTEXT_USAGE takes precedence over estimation."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.75")

        result = context_warning_full_module.get_context_usage_from_env()

        assert result == 0.75

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_id_matches_correct_file(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: CLAUDE_SESSION_ID selects the correct session file."""
        # Set up fake project directory structure
        home = tmp_path / "home" / "user"
        home.mkdir(parents=True)
        project_dir = home / ".claude" / "projects" / "-fakecwd"
        project_dir.mkdir(parents=True)

        # Create two session files: old-large and new-small
        old_session = project_dir / "old-session-id.jsonl"
        old_session.write_text("x" * 400000)  # ~50% of 800KB

        new_session = project_dir / "target-session-id.jsonl"
        new_session.write_text("x" * 80000)  # ~10% of 800KB

        monkeypatch.setenv("CLAUDE_SESSION_ID", "target-session-id")
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.delenv("CLAUDE_HOME", raising=False)

        # Patch Path.cwd and Path.home
        monkeypatch.setattr(
            "pathlib.Path.cwd", staticmethod(lambda: tmp_path / "fakecwd")
        )
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))

        # Create the cwd directory and matching project dir using dash convention
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(exist_ok=True)
        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        # Write valid JSONL to target file with fewer turns than the large file
        target_lines = []
        for _ in range(10):
            target_lines.append(json.dumps({"role": "user", "content": "hello"}))
            target_lines.append(json.dumps({"role": "assistant", "content": "hi"}))
        target_file = real_project_dir / "target-session-id.jsonl"
        target_file.write_text("\n".join(target_lines))

        # Large file has many more turns
        large_lines = []
        for _ in range(200):
            large_lines.append(json.dumps({"role": "user", "content": "hello"}))
            large_lines.append(json.dumps({"role": "assistant", "content": "hi"}))
        large_file = real_project_dir / "other-session.jsonl"
        large_file.write_text("\n".join(large_lines))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is not None
        assert result > 0.0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stale_session_file_returns_none(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: Stale session files are ignored without CLAUDE_SESSION_ID."""
        home = tmp_path / "home" / "user"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        stale_file = real_project_dir / "old-session.jsonl"
        stale_file.write_text("x" * 500000)

        # Make the file appear old (>60s) by backdating mtime
        old_time = time.time() - 120
        os.utime(stale_file, (old_time, old_time))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fresh_session_file_used_without_session_id(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: Fresh session files are used when no CLAUDE_SESSION_ID."""
        home = tmp_path / "home" / "user"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        # Create a fresh file with valid JSONL turns (just written = within 60s)
        fresh_file = real_project_dir / "fresh-session.jsonl"
        lines = []
        for _ in range(200):
            lines.append(json.dumps({"role": "user", "content": "hello world"}))
            lines.append(json.dumps({"role": "assistant", "content": "hi there"}))
        fresh_file.write_text("\n".join(lines))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is not None
        assert result > 0.0


class TestFallbackContextEstimationCoverage:
    """Coverage tests for estimate_context_from_session branches.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.unit
    def test_returns_none_when_claude_projects_missing(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """No .claude/projects directory returns None."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_no_jsonl_files(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Project dir exists but has no JSONL files returns None."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.unit
    def test_session_id_set_but_no_match_falls_back_to_newest(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """CLAUDE_SESSION_ID set but no match; falls back to newest."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        fresh_file = project_dir / "other-session.jsonl"
        fresh_file.write_text(json.dumps({"role": "user", "content": "hello"}) + "\n")

        monkeypatch.setenv("CLAUDE_SESSION_ID", "nonexistent-id")
        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        # Falls back to newest file (fresh), so returns a non-None result
        assert result is not None

    @pytest.mark.unit
    def test_returns_none_on_os_error(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """OSError during session discovery returns None."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        session = project_dir / "session.jsonl"
        session.write_text(json.dumps({"role": "user", "content": "hi"}) + "\n")

        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        # Make the glob call raise OSError mid-execution
        monkeypatch.setattr(
            type(project_dir),
            "glob",
            lambda _self, _pat: (_ for _ in ()).throw(OSError("disk error")),
        )

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None


class TestEstimateFromRecentTurns:
    """Feature: Token-based estimation from recent session JSONL turns.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_file_returns_zero(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Empty session file yields near-zero estimate."""
        session_file = tmp_path / "empty.jsonl"
        session_file.write_text("")

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result == pytest.approx(ZERO, abs=0.01)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_counts_user_and_assistant_turns(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Turns contribute to token estimate."""
        lines = [
            json.dumps({"role": "user", "content": "hello"}),
            json.dumps({"role": "assistant", "content": "hi"}),
            json.dumps({"role": "user", "content": "question"}),
            json.dumps({"role": "assistant", "content": "answer"}),
        ]
        session_file = tmp_path / "turns.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_counts_tool_results(self, context_warning_full_module, tmp_path) -> None:
        """Scenario: Tool results add to token estimate."""
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "t1",
                            "content": "result1",
                        },
                        {
                            "type": "tool_result",
                            "tool_use_id": "t2",
                            "content": "result2",
                        },
                    ],
                }
            ),
            json.dumps({"role": "assistant", "content": "response"}),
        ]
        session_file = tmp_path / "tools.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_caps_at_095(self, context_warning_full_module, tmp_path) -> None:
        """Scenario: Estimate is capped at 0.95 to avoid false 100%."""
        # Create valid JSONL with large text blocks so content_chars >> context_window
        big_text = "a" * 10_000
        lines = []
        for _ in range(100):
            entry = {
                "role": "assistant",
                "content": [{"type": "text", "text": big_text}],
            }
            lines.append(json.dumps(entry))
        session_file = tmp_path / "large.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result <= 0.95

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_malformed_json_lines(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Malformed JSON lines are skipped gracefully."""
        lines = [
            "not valid json",
            json.dumps({"role": "user", "content": "hello"}),
            "{bad json{",
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "mixed.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_file_returns_none(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Missing file returns None."""
        missing_file = tmp_path / "nonexistent.jsonl"

        result = context_warning_full_module._estimate_from_recent_turns(missing_file)

        assert result is None

    @pytest.mark.unit
    def test_blank_lines_skipped(self, context_warning_full_module, tmp_path) -> None:
        """Blank lines in JSONL are skipped without error."""
        lines = [
            "",
            "   ",
            json.dumps({"role": "user", "content": "hello"}),
            "",
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "blanks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_string_block_in_content_list_counted(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """String items inside a content list contribute to content_chars."""
        lines = [
            json.dumps({"role": "user", "content": ["hello world", "second string"]}),
        ]
        session_file = tmp_path / "strblocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_string_message_content_counted(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """String message content (not list) contributes to content_chars."""
        lines = [
            json.dumps({"role": "assistant", "content": "a" * 4000}),
        ]
        session_file = tmp_path / "strcontents.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tail_reading_skips_old_history(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Large files are read from the tail only."""
        old_text = "x" * 500_000  # 500KB per entry
        old_entry = {
            "role": "assistant",
            "content": [{"type": "text", "text": old_text}],
        }
        old_line = json.dumps(old_entry)
        old_count = 10
        old_lines = [old_line] * old_count

        recent_lines = [
            json.dumps({"role": "user", "content": "recent question"}),
            json.dumps({"role": "assistant", "content": "recent answer"}),
            json.dumps({"role": "user", "content": "follow-up"}),
            json.dumps({"role": "assistant", "content": "response"}),
        ]

        session_file = tmp_path / "large_session.jsonl"
        all_content = "\n".join(old_lines + recent_lines)
        session_file.write_text(all_content)

        # Verify file actually exceeds the tail threshold
        assert session_file.stat().st_size > context_warning_full_module._TAIL_BYTES

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result < 0.95, (
            f"Tail reading should produce lower estimate than full file, got {result}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_user_assistant_roles_not_counted_as_turns(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Only user and assistant roles count as turns."""
        lines = [
            json.dumps({"role": "system", "content": "system prompt text"}),
            json.dumps({"role": "tool", "content": "tool output text"}),
            json.dumps({"role": "user", "content": "hello"}),
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "mixed_roles.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        expected_approx = 1200 / 1_000_000
        assert result == pytest.approx(expected_approx, abs=0.005)

    @pytest.mark.unit
    def test_mixed_dict_and_str_blocks_in_content_list(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Content list with both dict and str blocks counts all."""
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        "plain string block",
                        {"type": "text", "text": "dict block"},
                    ],
                }
            ),
        ]
        session_file = tmp_path / "mixed_blocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_multiple_lines_with_string_content(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Multiple lines with string content all contribute."""
        lines = [
            json.dumps({"role": "user", "content": "first message"}),
            json.dumps({"role": "assistant", "content": "reply"}),
            json.dumps({"role": "user", "content": "second message"}),
        ]
        session_file = tmp_path / "multi_str.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_non_dict_non_str_block_in_content_list_skipped(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Content list items that are neither dict nor str are silently skipped."""
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        42,
                        None,
                        True,
                        {"type": "text", "text": "real content"},
                    ],
                }
            ),
        ]
        session_file = tmp_path / "odd_blocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_non_list_non_str_content_skipped(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Message content that is neither list nor str is skipped."""
        lines = [
            json.dumps({"role": "user", "content": None}),
            json.dumps({"role": "assistant", "content": 12345}),
            json.dumps({"role": "user", "content": "real content"}),
        ]
        session_file = tmp_path / "odd_content.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO


class TestFindCurrentSession:
    """Feature: Active session file discovery from JSONL candidates.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_matches_by_session_id_env(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: Session ID env var matches a JSONL file by stem."""
        monkeypatch.setenv("CLAUDE_SESSION_ID", "abc-123")
        target = tmp_path / "abc-123.jsonl"
        target.write_text("{}\n")
        other = tmp_path / "other.jsonl"
        other.write_text("{}\n")

        result = context_warning_full_module._find_current_session([other, target])

        assert result == target

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_id_no_match_falls_back_to_newest(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: Session ID set but no file matches, falls back to newest."""
        monkeypatch.setenv("CLAUDE_SESSION_ID", "nonexistent-id")
        old = tmp_path / "old.jsonl"
        old.write_text("{}\n")
        new = tmp_path / "new.jsonl"
        new.write_text("{}\n")
        # Ensure 'new' is newest by touching it
        os.utime(old, (time.time() - HUNDRED, time.time() - HUNDRED))

        result = context_warning_full_module._find_current_session([old, new])

        assert result == new

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_session_id_uses_newest_fresh_file(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: No session ID, picks the most recently modified file."""
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        f1 = tmp_path / "a.jsonl"
        f1.write_text("{}\n")
        f2 = tmp_path / "b.jsonl"
        f2.write_text("{}\n")
        os.utime(f1, (time.time() - HUNDRED, time.time() - HUNDRED))

        result = context_warning_full_module._find_current_session([f1, f2])

        assert result == f2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stale_files_return_none(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: All files are stale, returns None."""
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        stale = tmp_path / "stale.jsonl"
        stale.write_text("{}\n")
        stale_time = time.time() - 120
        os.utime(stale, (stale_time, stale_time))

        result = context_warning_full_module._find_current_session([stale])

        assert result is None


class TestCountContent:
    """Feature: Message content character and tool result counting.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_with_dict_blocks(self, context_warning_full_module) -> None:
        """Scenario: Content is a list of dict blocks with text."""
        content = [
            {"type": "text", "text": "hello"},
            {"type": "tool_result", "text": "result data"},
        ]

        chars, tool_results = context_warning_full_module._count_content(content)

        assert chars == len("hello") + len("result data")
        assert tool_results == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_with_string_blocks(self, context_warning_full_module) -> None:
        """Scenario: Content is a list of plain strings."""
        content = ["hello", "world"]

        chars, tool_results = context_warning_full_module._count_content(content)

        assert chars == len("hello") + len("world")
        assert tool_results == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_plain_string_content(self, context_warning_full_module) -> None:
        """Scenario: Content is a plain string (not a list)."""
        content = "a simple message"

        chars, tool_results = context_warning_full_module._count_content(content)

        assert chars == len("a simple message")
        assert tool_results == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_list_returns_zeros(self, context_warning_full_module) -> None:
        """Scenario: Content is an empty list."""
        chars, tool_results = context_warning_full_module._count_content([])

        assert chars == 0
        assert tool_results == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dict_without_text_key(self, context_warning_full_module) -> None:
        """Scenario: Dict block has no text key."""
        content = [{"type": "image", "source": "data:..."}]

        chars, tool_results = context_warning_full_module._count_content(content)

        assert chars == 0
        assert tool_results == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mixed_dict_and_string_blocks(self, context_warning_full_module) -> None:
        """Scenario: Content mixes dict and string blocks."""
        content = [
            {"type": "text", "text": "abc"},
            "def",
            {"type": "tool_result", "text": "ghi"},
        ]

        chars, tool_results = context_warning_full_module._count_content(content)

        assert chars == 9
        assert tool_results == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_list_non_string_returns_zeros(
        self, context_warning_full_module
    ) -> None:
        """Scenario: Content is neither list nor string (e.g. None or int)."""
        chars, tool_results = context_warning_full_module._count_content(None)

        assert chars == 0
        assert tool_results == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_result_content_key_counted(self, context_warning_full_module) -> None:
        """Scenario: tool_result block using 'content' key is counted."""
        payload = "tool output data here"
        content = [{"type": "tool_result", "content": payload}]
        chars, tool_results = context_warning_full_module._count_content(content)
        assert chars == len(payload)
        assert tool_results == 1


class TestResolveSessionFile:
    """Feature: Session file resolution orchestration.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_when_projects_dir_missing(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: ~/.claude/projects does not exist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

        result = context_warning_full_module._resolve_session_file()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_when_no_project_match(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: Projects dir exists but no matching project dir."""
        projects = tmp_path / ".claude" / "projects"
        projects.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

        result = context_warning_full_module._resolve_session_file()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_when_no_jsonl_files(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: Project dir exists but contains no JSONL files."""
        cwd = Path.cwd()
        projects = tmp_path / ".claude" / "projects"
        dir_name = str(cwd).replace(os.sep, "-")
        if not dir_name.startswith("-"):
            dir_name = "-" + dir_name
        project_dir = projects / dir_name
        project_dir.mkdir(parents=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

        result = context_warning_full_module._resolve_session_file()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_session_file_on_happy_path(
        self, context_warning_full_module, tmp_path, monkeypatch
    ) -> None:
        """Scenario: Full directory structure exists with a fresh JSONL file."""
        cwd = Path.cwd()
        projects = tmp_path / ".claude" / "projects"
        dir_name = str(cwd).replace(os.sep, "-")
        if not dir_name.startswith("-"):
            dir_name = "-" + dir_name
        project_dir = projects / dir_name
        project_dir.mkdir(parents=True)

        session_file = project_dir / "active-session.jsonl"
        session_file.write_text('{"role": "user", "content": "hello"}\n')

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("CLAUDE_SESSION_ID", "active-session")

        result = context_warning_full_module._resolve_session_file()

        assert result == session_file


class TestResolveProjectDir:
    """Feature: Project directory resolution using Claude Code naming convention.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_resolves_path_with_dashes(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Path separators are replaced with dashes."""
        claude_projects = tmp_path / "projects"
        cwd = tmp_path / "home" / "user" / "project"
        cwd.mkdir(parents=True)

        dir_name = str(cwd).replace(os.sep, "-")
        if not dir_name.startswith("-"):
            dir_name = "-" + dir_name
        expected = claude_projects / dir_name
        expected.mkdir(parents=True)

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result == expected

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_when_dir_not_found(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Returns None when no matching directory exists."""
        claude_projects = tmp_path / "projects"
        claude_projects.mkdir(parents=True)
        cwd = tmp_path / "nonexistent" / "project"

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_leading_dash_added_when_missing(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Leading dash is added if path does not start with separator."""
        claude_projects = tmp_path / "projects"
        cwd = Path("relative/path")
        dir_name = str(cwd).replace(os.sep, "-")
        # dir_name = "relative-path" — no leading dash
        assert not dir_name.startswith("-")

        expected_dir = claude_projects / ("-" + dir_name)
        expected_dir.mkdir(parents=True)

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result == expected_dir
