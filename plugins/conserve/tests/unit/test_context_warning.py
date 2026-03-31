"""Tests for context warning hook with three-tier MECW alerts."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from context_warning import (
    ContextAlert,
    ContextSeverity,
    _count_content,
    _estimate_from_recent_turns,
    _find_current_session,
    _resolve_project_dir,
    _resolve_session_file,
    assess_context_usage,
    estimate_context_from_session,
    format_hook_output,
    get_context_usage_from_env,
    main,
)


class TestContextSeverity:
    """Severity enum has expected values."""

    def test_ok_value(self) -> None:
        """Verify Ok value."""
        assert ContextSeverity.OK.value == "ok"

    def test_warning_value(self) -> None:
        """Verify Warning value."""
        assert ContextSeverity.WARNING.value == "warning"

    def test_critical_value(self) -> None:
        """Verify Critical value."""
        assert ContextSeverity.CRITICAL.value == "critical"

    def test_emergency_value(self) -> None:
        """Verify Emergency value."""
        assert ContextSeverity.EMERGENCY.value == "emergency"


class TestContextAlert:
    """ContextAlert dataclass serialization."""

    def test_to_dict_returns_expected_keys(self) -> None:
        """Verify To dict returns expected keys."""
        alert = ContextAlert(
            severity=ContextSeverity.OK,
            usage_percent=0.15,
            message="OK: Context at 15.0%",
            recommendations=[],
        )
        d = alert.to_dict()
        assert d["severity"] == "ok"
        assert d["usage_percent"] == 15.0
        assert d["message"] == "OK: Context at 15.0%"
        assert d["recommendations"] == []

    def test_to_dict_rounds_usage(self) -> None:
        """Verify To dict rounds usage."""
        alert = ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=0.4567,
            message="test",
            recommendations=["do something"],
        )
        d = alert.to_dict()
        assert d["usage_percent"] == 45.7


class TestAssessContextUsage:
    """Three-tier context usage assessment."""

    def test_ok_below_warning_threshold(self) -> None:
        """Verify Ok below warning threshold."""
        alert = assess_context_usage(0.10)
        assert alert.severity == ContextSeverity.OK
        assert alert.recommendations == []

    def test_ok_at_zero(self) -> None:
        """Verify Ok at zero."""
        alert = assess_context_usage(0.0)
        assert alert.severity == ContextSeverity.OK

    def test_warning_at_threshold(self) -> None:
        """Verify Warning at threshold."""
        alert = assess_context_usage(0.40)
        assert alert.severity == ContextSeverity.WARNING
        assert "WARNING" in alert.message
        assert len(alert.recommendations) > 0

    def test_warning_between_warning_and_critical(self) -> None:
        """Verify Warning between warning and critical."""
        alert = assess_context_usage(0.45)
        assert alert.severity == ContextSeverity.WARNING

    def test_critical_at_threshold(self) -> None:
        """Verify Critical at threshold."""
        alert = assess_context_usage(0.50)
        assert alert.severity == ContextSeverity.CRITICAL
        assert "CRITICAL" in alert.message
        assert len(alert.recommendations) > 0

    def test_critical_between_critical_and_emergency(self) -> None:
        """Verify Critical between critical and emergency."""
        alert = assess_context_usage(0.65)
        assert alert.severity == ContextSeverity.CRITICAL

    def test_emergency_at_threshold(self) -> None:
        """Verify Emergency at threshold."""
        alert = assess_context_usage(0.80)
        assert alert.severity == ContextSeverity.EMERGENCY
        assert "EMERGENCY" in alert.message
        assert "clear-context" in alert.message
        assert len(alert.recommendations) > 0

    def test_emergency_at_max(self) -> None:
        """Verify Emergency at max."""
        alert = assess_context_usage(1.0)
        assert alert.severity == ContextSeverity.EMERGENCY

    def test_invalid_usage_below_zero_raises(self) -> None:
        """Verify Invalid usage below zero raises."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            assess_context_usage(-0.1)

    def test_invalid_usage_above_one_raises(self) -> None:
        """Verify Invalid usage above one raises."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            assess_context_usage(1.1)


class TestResolveProjectDir:
    """Project directory resolution from cwd."""

    def test_resolves_existing_project_dir(self, tmp_path: Path) -> None:
        """Verify Resolves existing project dir."""
        projects = tmp_path / "projects"
        project_dir = projects / "-home-user-project"
        project_dir.mkdir(parents=True)
        result = _resolve_project_dir(Path("/home/user/project"), projects)
        assert result == project_dir

    def test_returns_none_for_missing_project_dir(self, tmp_path: Path) -> None:
        """Verify Returns none for missing project dir."""
        projects = tmp_path / "projects"
        projects.mkdir(parents=True)
        result = _resolve_project_dir(Path("/home/user/nonexistent"), projects)
        assert result is None

    def test_adds_leading_dash(self, tmp_path: Path) -> None:
        """Verify leading dash is prepended to project dir name."""
        projects = tmp_path / "projects"
        test_dir = tmp_path / "workdir"
        # Build expected dir name: replace os.sep with dash
        dir_name = str(test_dir).replace(os.sep, "-")
        if not dir_name.startswith("-"):
            dir_name = "-" + dir_name
        project_dir = projects / dir_name
        project_dir.mkdir(parents=True)
        result = _resolve_project_dir(test_dir, projects)
        assert result == project_dir


class TestFindCurrentSession:
    """Session file discovery from JSONL candidates."""

    def test_finds_by_session_id_env(self, tmp_path: Path) -> None:
        """Verify Finds by session id env."""
        target = tmp_path / "abc123.jsonl"
        target.write_text("{}\n")
        other = tmp_path / "other.jsonl"
        other.write_text("{}\n")

        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "abc123"}):
            result = _find_current_session([other, target])
        assert result == target

    def test_falls_back_to_newest_when_no_session_id(self, tmp_path: Path) -> None:
        """Verify Falls back to newest when no session id."""
        older = tmp_path / "older.jsonl"
        older.write_text("{}\n")
        time.sleep(0.05)
        newer = tmp_path / "newer.jsonl"
        newer.write_text("{}\n")

        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("CLAUDE_SESSION_ID", None)
            with patch.dict(os.environ, env, clear=True):
                result = _find_current_session([older, newer])
        assert result == newer

    def test_returns_none_for_stale_files(self, tmp_path: Path) -> None:
        """Verify Returns none for stale files."""
        stale = tmp_path / "stale.jsonl"
        stale.write_text("{}\n")
        # Set mtime to far in the past
        old_time = time.time() - 120
        os.utime(stale, (old_time, old_time))

        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("CLAUDE_SESSION_ID", None)
            with patch.dict(os.environ, env, clear=True):
                result = _find_current_session([stale])
        assert result is None


class TestResolveSessionFile:
    """Full session file resolution pipeline."""

    def test_returns_none_when_no_projects_dir(self, tmp_path: Path) -> None:
        """Verify Returns none when no projects dir."""
        with patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}):
            result = _resolve_session_file()
        assert result is None

    def test_returns_none_when_no_project_match(self, tmp_path: Path) -> None:
        """Verify Returns none when no project match."""
        projects = tmp_path / "projects"
        projects.mkdir()
        with (
            patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}),
            patch("context_warning.Path") as mock_path_cls,
        ):
            mock_path_cls.return_value = mock_path_cls
            mock_path_cls.home.return_value = tmp_path
            # Let the real Path work for everything else
            result = _resolve_session_file()
        assert result is None

    def test_returns_none_when_no_jsonl_files(self, tmp_path: Path) -> None:
        """Verify Returns none when no jsonl files."""
        projects = tmp_path / "projects"
        cwd = Path.cwd()
        project_name = str(cwd).replace(os.sep, "-")
        if not project_name.startswith("-"):
            project_name = "-" + project_name
        project_dir = projects / project_name
        project_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}):
            result = _resolve_session_file()
        assert result is None


class TestCountContent:
    """Content counting from message content fields."""

    def test_counts_string_content(self) -> None:
        """Verify Counts string content."""
        chars, tools = _count_content("hello world")
        assert chars == 11
        assert tools == 0

    def test_counts_list_with_text_blocks(self) -> None:
        """Verify Counts list with text blocks."""
        content = [
            {"type": "text", "text": "hello"},
            {"type": "text", "text": "world"},
        ]
        chars, tools = _count_content(content)
        assert chars == 10
        assert tools == 0

    def test_counts_tool_results(self) -> None:
        """Verify Counts tool results."""
        content = [
            {"type": "tool_result", "content": "result data"},
        ]
        chars, tools = _count_content(content)
        assert chars == 11
        assert tools == 1

    def test_counts_string_blocks_in_list(self) -> None:
        """Verify Counts string blocks in list."""
        content = ["hello", "world"]
        chars, tools = _count_content(content)
        assert chars == 10
        assert tools == 0

    def test_handles_empty_content(self) -> None:
        """Verify Handles empty content."""
        chars, tools = _count_content([])
        assert chars == 0
        assert tools == 0

    def test_handles_none_text(self) -> None:
        """Verify Handles none text."""
        content = [{"type": "text"}]
        chars, tools = _count_content(content)
        assert chars == 0
        assert tools == 0


class TestEstimateFromRecentTurns:
    """Session file estimation from JSONL turns."""

    def test_estimates_from_small_session(self, tmp_path: Path) -> None:
        """Verify Estimates from small session."""
        session = tmp_path / "session.jsonl"
        lines = []
        for i in range(10):
            lines.append(
                json.dumps(
                    {
                        "role": "user" if i % 2 == 0 else "assistant",
                        "content": f"Message {i} " * 50,
                    }
                )
            )
        session.write_text("\n".join(lines))
        result = _estimate_from_recent_turns(session)
        assert result is not None
        assert 0.0 < result < 1.0

    def test_returns_none_for_unreadable_file(self, tmp_path: Path) -> None:
        """Verify Returns none for unreadable file."""
        session = tmp_path / "missing.jsonl"
        result = _estimate_from_recent_turns(session)
        assert result is None

    def test_handles_invalid_json_lines(self, tmp_path: Path) -> None:
        """Verify Handles invalid json lines."""
        session = tmp_path / "session.jsonl"
        session.write_text("not json\n{invalid\n")
        result = _estimate_from_recent_turns(session)
        assert result is not None  # Returns 0-ish estimate, not None

    def test_caps_at_0_95(self, tmp_path: Path) -> None:
        """Verify Caps at 0 95."""
        session = tmp_path / "session.jsonl"
        # Write a large number of turns to push estimate high
        lines = []
        for i in range(5000):
            lines.append(
                json.dumps(
                    {
                        "role": "user" if i % 2 == 0 else "assistant",
                        "content": "x" * 2000,
                    }
                )
            )
        session.write_text("\n".join(lines))
        result = _estimate_from_recent_turns(session)
        assert result is not None
        assert result <= 0.95

    def test_handles_empty_lines(self, tmp_path: Path) -> None:
        """Verify Handles empty lines."""
        session = tmp_path / "session.jsonl"
        session.write_text("\n\n\n")
        result = _estimate_from_recent_turns(session)
        assert result is not None


class TestEstimateContextFromSession:
    """High-level session estimation with env controls."""

    def test_returns_none_when_estimation_disabled(self) -> None:
        """Verify Returns none when estimation disabled."""
        with patch.dict(os.environ, {"CONSERVE_CONTEXT_ESTIMATION": "0"}):
            result = estimate_context_from_session()
        assert result is None

    def test_returns_none_when_no_session_file(self) -> None:
        """Verify Returns none when no session file."""
        with (
            patch.dict(os.environ, {"CONSERVE_CONTEXT_ESTIMATION": "1"}),
            patch("context_warning._resolve_session_file", return_value=None),
        ):
            result = estimate_context_from_session()
        assert result is None

    def test_returns_estimate_when_session_exists(self, tmp_path: Path) -> None:
        """Verify Returns estimate when session exists."""
        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({"role": "user", "content": "hi"}) + "\n")
        with (
            patch.dict(os.environ, {"CONSERVE_CONTEXT_ESTIMATION": "1"}),
            patch("context_warning._resolve_session_file", return_value=session),
        ):
            result = estimate_context_from_session()
        assert result is not None

    def test_handles_os_error_gracefully(self) -> None:
        """Verify Handles os error gracefully."""
        with (
            patch.dict(os.environ, {"CONSERVE_CONTEXT_ESTIMATION": "1"}),
            patch(
                "context_warning._resolve_session_file",
                side_effect=OSError("disk error"),
            ),
        ):
            result = estimate_context_from_session()
        assert result is None


class TestGetContextUsageFromEnv:
    """Environment-based context usage retrieval."""

    def test_reads_from_env_variable(self) -> None:
        """Verify Reads from env variable."""
        with patch.dict(os.environ, {"CLAUDE_CONTEXT_USAGE": "0.55"}):
            usage, is_estimated = get_context_usage_from_env()
        assert usage == 0.55
        assert is_estimated is False

    def test_returns_none_for_invalid_env_value(self) -> None:
        """Verify Returns none for invalid env value."""
        with (
            patch.dict(os.environ, {"CLAUDE_CONTEXT_USAGE": "not-a-float"}),
            patch(
                "context_warning.estimate_context_from_session",
                return_value=None,
            ),
        ):
            usage, is_estimated = get_context_usage_from_env()
        assert usage is None
        assert is_estimated is True

    def test_falls_back_to_session_estimation(self) -> None:
        """Verify Falls back to session estimation."""
        env = os.environ.copy()
        env.pop("CLAUDE_CONTEXT_USAGE", None)
        with (
            patch.dict(os.environ, env, clear=True),
            patch(
                "context_warning.estimate_context_from_session",
                return_value=0.35,
            ),
        ):
            usage, is_estimated = get_context_usage_from_env()
        assert usage == 0.35
        assert is_estimated is True


class TestFormatHookOutput:
    """Hook output formatting."""

    def test_ok_alert_has_no_additional_context(self) -> None:
        """Verify Ok alert has no additional context."""
        alert = ContextAlert(
            severity=ContextSeverity.OK,
            usage_percent=0.1,
            message="OK",
            recommendations=[],
        )
        output = format_hook_output(alert)
        assert "additionalContext" not in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    def test_warning_alert_has_additional_context(self) -> None:
        """Verify Warning alert has additional context."""
        alert = ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=0.45,
            message="WARNING: Context at 45.0%",
            recommendations=["Monitor usage"],
        )
        output = format_hook_output(alert)
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "WARNING" in ctx
        assert "Monitor usage" in ctx

    def test_critical_alert_has_additional_context(self) -> None:
        """Verify Critical alert has additional context."""
        alert = ContextAlert(
            severity=ContextSeverity.CRITICAL,
            usage_percent=0.55,
            message="CRITICAL",
            recommendations=["Optimize now"],
        )
        output = format_hook_output(alert)
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_contextwarning_key_present(self) -> None:
        """Verify Contextwarning key present."""
        alert = ContextAlert(
            severity=ContextSeverity.OK,
            usage_percent=0.1,
            message="OK",
            recommendations=[],
        )
        output = format_hook_output(alert)
        assert "contextWarning" in output["hookSpecificOutput"]


class TestMain:
    """Entry point integration tests."""

    def test_ok_level_outputs_minimal_json(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify Ok level outputs minimal json."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.10")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    def test_warning_level_outputs_alert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify Warning level outputs alert."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert "contextWarning" in output["hookSpecificOutput"]

    def test_emergency_level_has_delegation_guidance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify Emergency level has delegation guidance."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.85")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "EMERGENCY" in ctx
        assert "continuation" in ctx.lower()

    def test_no_context_available_outputs_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify No context available outputs empty."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert "contextWarning" not in output.get("hookSpecificOutput", {})

    def test_invalid_json_stdin_still_works(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify Invalid json stdin still works."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.10")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("not json"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0

    def test_context_from_hook_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify Context from hook input."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        hook_input = json.dumps({"context_usage": 0.45})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(hook_input))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert "contextWarning" in output["hookSpecificOutput"]

    def test_invalid_usage_from_hook_input(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify Invalid usage from hook input."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        hook_input = json.dumps({"context_usage": 5.0})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(hook_input))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0


class TestEstimationSeverityCapping:
    """Severity capping when usage comes from JSONL estimation fallback."""

    def test_estimated_high_usage_capped_at_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When estimation returns 0.85, severity is WARNING not EMERGENCY."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr(
            "context_warning.estimate_context_from_session",
            lambda: 0.85,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        ctx = output["hookSpecificOutput"].get("additionalContext", "")
        assert "WARNING" in ctx
        assert "EMERGENCY" not in ctx
        warning = output["hookSpecificOutput"]["contextWarning"]
        assert warning["severity"] == "warning"

    def test_estimated_critical_usage_capped_at_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When estimation returns 0.55, severity is WARNING not CRITICAL."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr(
            "context_warning.estimate_context_from_session",
            lambda: 0.55,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        warning = output["hookSpecificOutput"]["contextWarning"]
        assert warning["severity"] == "warning"
        ctx = output["hookSpecificOutput"].get("additionalContext", "")
        assert "estimated" in ctx.lower()

    def test_env_var_high_usage_still_emergency(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When CLAUDE_CONTEXT_USAGE is 0.85, severity is EMERGENCY."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.85")
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "EMERGENCY" in ctx

    def test_estimated_warning_level_not_capped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When estimation returns 0.45, severity stays WARNING (no capping needed)."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr(
            "context_warning.estimate_context_from_session",
            lambda: 0.45,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        warning = output["hookSpecificOutput"]["contextWarning"]
        assert warning["severity"] == "warning"

    def test_estimated_ok_level_not_affected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When estimation returns 0.10, severity stays OK."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr(
            "context_warning.estimate_context_from_session",
            lambda: 0.10,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        assert "contextWarning" not in output.get("hookSpecificOutput", {})

    def test_capped_alert_mentions_estimated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Capped alert message notes the value is estimated."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr(
            "context_warning.estimate_context_from_session",
            lambda: 0.90,
        )
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        captured: list[str] = []
        monkeypatch.setattr("builtins.print", lambda s: captured.append(s))
        rc = main()
        assert rc == 0
        output = json.loads(captured[0])
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "estimated" in ctx.lower()
        assert "may be inaccurate" in ctx.lower()
