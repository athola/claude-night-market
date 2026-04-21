"""Tests for vow_bounded_reads hook.

Feature: Warn when discovery read budget is exceeded.

As a Night Market vow enforcement system
I want to count consecutive Read/Grep calls in a session
So that the bounded-discovery-reads vow is tracked and enforced.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def hook_module():
    """Import vow_bounded_reads via importlib (hook is a standalone script)."""
    hooks_path = Path(__file__).resolve().parents[3] / "hooks"
    module_path = hooks_path / "vow_bounded_reads.py"
    spec = importlib.util.spec_from_file_location("vow_bounded_reads", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vow_bounded_reads"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_input(tool_name="Read", session_id="test-session-abc"):
    payload = {
        "tool_name": tool_name,
        "session_id": session_id,
        "tool_input": {"file_path": "/some/file.py"},
    }
    return json.dumps(payload)


class TestCounterFilePath:
    """Feature: Counter file path uses session ID.

    As the hook
    I want a per-session counter file
    So that reads are tracked independently per session.
    """

    @pytest.mark.unit
    def test_counter_file_uses_session_id(self, hook_module, tmp_path):
        """
        Scenario: Counter path includes session ID
        Given a session ID
        When _counter_path is called
        Then the returned path contains the session ID
        """
        path = hook_module._counter_path("my-session-123")
        assert "my-session-123" in str(path)

    @pytest.mark.unit
    def test_counter_file_in_tmp(self, hook_module):
        """
        Scenario: Counter file lives under /tmp
        Given any session ID
        When _counter_path is called
        Then the path is under /tmp
        """
        path = hook_module._counter_path("some-session")
        assert str(path).startswith("/tmp")

    @pytest.mark.unit
    def test_counter_path_fallback_when_no_session(self, hook_module):
        """
        Scenario: Counter path falls back gracefully with empty session
        Given an empty session ID
        When _counter_path is called
        Then a valid path is still returned
        """
        path = hook_module._counter_path("")
        assert isinstance(path, Path)


class TestReadWriteCounter:
    """Feature: Counter persistence in JSON file.

    As the hook
    I want to read and write the counter atomically
    So that consecutive reads across tool calls are counted.
    """

    @pytest.mark.unit
    def test_read_counter_returns_zero_when_missing(self, hook_module, tmp_path):
        """
        Scenario: Counter starts at zero when file missing
        Given no counter file exists
        When _read_counter is called
        Then it returns 0
        """
        path = tmp_path / "vow_read_counter_none.json"
        count = hook_module._read_counter(path)
        assert count == 0

    @pytest.mark.unit
    def test_write_then_read_counter(self, hook_module, tmp_path):
        """
        Scenario: Written counter value is read back correctly
        Given a counter file is written with value 7
        When _read_counter is called
        Then it returns 7
        """
        path = tmp_path / "vow_read_counter_test.json"
        hook_module._write_counter(path, 7)
        assert hook_module._read_counter(path) == 7

    @pytest.mark.unit
    def test_read_counter_ignores_corrupt_file(self, hook_module, tmp_path):
        """
        Scenario: Corrupt counter file treated as zero (fail-safe)
        Given a counter file with invalid JSON
        When _read_counter is called
        Then it returns 0 without raising
        """
        path = tmp_path / "vow_read_counter_bad.json"
        path.write_text("not valid json")
        count = hook_module._read_counter(path)
        assert count == 0


class TestIsReadTool:
    """Feature: Classify tools as read or write operations.

    As the hook
    I want to know which tools increment the read counter
    And which tools reset it (write operations)
    So that the counter resets when implementation begins.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name,expected",
        [
            ("Read", True),
            ("Grep", True),
            ("Glob", True),
            ("Write", False),
            ("Edit", False),
            ("MultiEdit", False),
            ("Bash", False),
        ],
        ids=["Read", "Grep", "Glob", "Write", "Edit", "MultiEdit", "Bash"],
    )
    def test_read_tool_classification(self, hook_module, tool_name, expected):
        """
        Scenario: Correctly classify read vs non-read tools
        Given a tool name
        When _is_read_tool is called
        Then it returns True only for Read/Grep/Glob
        """
        assert hook_module._is_read_tool(tool_name) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name,expected",
        [
            ("Write", True),
            ("Edit", True),
            ("MultiEdit", True),
            ("Read", False),
            ("Grep", False),
            ("Bash", False),
        ],
        ids=["Write", "Edit", "MultiEdit", "Read", "Grep", "Bash"],
    )
    def test_write_tool_classification(self, hook_module, tool_name, expected):
        """
        Scenario: Correctly classify write tools (counter-reset triggers)
        Given a tool name
        When _is_write_tool is called
        Then it returns True only for Write/Edit/MultiEdit
        """
        assert hook_module._is_write_tool(tool_name) == expected


class TestMainHook:
    """Feature: Hook main() tracks reads and warns over budget.

    As the Claude Code hook runner
    I want the hook to warn when read budget is exceeded
    So that the bounded-discovery vow is surfaced to the developer.
    """

    @pytest.mark.unit
    def test_read_below_budget_passes_silently(self, hook_module, capsys, tmp_path):
        """
        Scenario: Read calls below budget pass without warning
        Given a fresh session with 5 reads counted
        When main() is called with a Read tool
        Then no warning JSON is emitted
        """
        counter_path = tmp_path / "vow_read_counter_test-session.json"
        hook_module._write_counter(counter_path, 5)

        stdin_data = _make_input(tool_name="Read", session_id="test-session")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_warn_when_budget_exceeded(self, hook_module, capsys, tmp_path):
        """
        Scenario: Warning emitted when read count exceeds 15
        Given a session with 15 reads already counted
        When main() is called with a Read tool
        Then output JSON has decision=warn mentioning the budget
        """
        counter_path = tmp_path / "vow_read_counter_test-session2.json"
        hook_module._write_counter(counter_path, 15)

        stdin_data = _make_input(tool_name="Read", session_id="test-session2")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        hook_out = output["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "warn"
        assert "Bounded discovery" in hook_out["permissionDecisionReason"]
        assert (
            "15" in hook_out["permissionDecisionReason"]
            or "16" in hook_out["permissionDecisionReason"]
        )

    @pytest.mark.unit
    def test_write_tool_resets_counter(self, hook_module, capsys, tmp_path):
        """
        Scenario: Write tool resets the read counter to zero
        Given a session with 12 reads counted
        When main() is called with a Write tool
        Then the counter file is reset to 0
        And no warning is emitted
        """
        counter_path = tmp_path / "vow_read_counter_test-session3.json"
        hook_module._write_counter(counter_path, 12)

        stdin_data = json.dumps(
            {
                "tool_name": "Write",
                "session_id": "test-session3",
                "tool_input": {"file_path": "/tmp/out.py"},
            }
        )
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        assert hook_module._read_counter(counter_path) == 0

    @pytest.mark.unit
    def test_non_tracked_tool_exits_silently(self, hook_module, capsys, tmp_path):
        """
        Scenario: Untracked tool types pass through without counter change
        Given a Bash tool call
        When main() runs
        Then no output and counter unchanged
        """
        counter_path = tmp_path / "vow_read_counter_test-session4.json"
        hook_module._write_counter(counter_path, 3)

        stdin_data = json.dumps(
            {
                "tool_name": "Bash",
                "session_id": "test-session4",
                "tool_input": {"command": "git status"},
            }
        )
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        # Counter should NOT be incremented for Bash
        assert hook_module._read_counter(counter_path) == 3

    @pytest.mark.unit
    def test_malformed_stdin_exits_cleanly(self, hook_module, capsys):
        """
        Scenario: Malformed stdin does not crash the hook
        Given non-JSON input on stdin
        When main() runs
        Then it exits 0 without output (fail-safe)
        """
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_session_id_from_stdin_json(self, hook_module, capsys, tmp_path):
        """
        Scenario: Session ID is read from stdin JSON field
        Given a stdin payload with session_id=abc123
        When main() runs
        Then the counter file is named for abc123
        """
        observed_paths = []

        original_counter_path = hook_module._counter_path

        def tracking_counter_path(session_id):
            path = original_counter_path(session_id)
            observed_paths.append((session_id, path))
            # Redirect to tmp_path so we don't write to /tmp during tests
            return tmp_path / path.name

        stdin_data = json.dumps(
            {
                "tool_name": "Read",
                "session_id": "abc123",
                "tool_input": {"file_path": "/x.py"},
            }
        )
        with patch.object(
            hook_module, "_counter_path", side_effect=tracking_counter_path
        ):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit):
                    hook_module.main()

        assert any("abc123" in str(p) for _, p in observed_paths)


class TestGetSessionId:
    """Feature: Session ID resolution from stdin, env var, or fallback.

    As the hook
    I want to resolve the session ID from multiple sources
    So that counter files are scoped to the correct session.
    """

    @pytest.mark.unit
    def test_session_id_from_stdin_data(self, hook_module):
        """
        Scenario: Session ID taken from stdin JSON when present
        Given a data dict with session_id='sid-001'
        When _get_session_id is called
        Then it returns 'sid-001'
        """
        assert hook_module._get_session_id({"session_id": "sid-001"}) == "sid-001"

    @pytest.mark.unit
    def test_session_id_falls_back_to_env_var(self, hook_module):
        """
        Scenario: Session ID taken from CLAUDE_SESSION_ID env var when stdin missing
        Given an empty data dict
        And CLAUDE_SESSION_ID=env-session-xyz in the environment
        When _get_session_id is called
        Then it returns 'env-session-xyz'
        """
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "env-session-xyz"}):
            assert hook_module._get_session_id({}) == "env-session-xyz"

    @pytest.mark.unit
    def test_session_id_falls_back_to_default(self, hook_module):
        """
        Scenario: Session ID defaults to 'default' when no source available
        Given an empty data dict
        And CLAUDE_SESSION_ID is not set in the environment
        When _get_session_id is called
        Then it returns 'default'
        """
        env = {
            k: v
            for k, v in __import__("os").environ.items()
            if k != "CLAUDE_SESSION_ID"
        }
        with patch.dict("os.environ", env, clear=True):
            assert hook_module._get_session_id({}) == "default"

    @pytest.mark.unit
    def test_stdin_session_id_takes_priority_over_env(self, hook_module):
        """
        Scenario: Stdin session_id wins over env var when both present
        Given a data dict with session_id='from-stdin'
        And CLAUDE_SESSION_ID=from-env in the environment
        When _get_session_id is called
        Then it returns 'from-stdin'
        """
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "from-env"}):
            assert (
                hook_module._get_session_id({"session_id": "from-stdin"})
                == "from-stdin"
            )
