"""Tests for SessionStart hook."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import patch

import hooks.session_start as mod
import pytest
from hooks.session_start import main


class TestSessionStartHook:
    """
    Feature: Session start notification

    As a researcher
    I want to know if I have an active research session
    So that I can resume or refine it
    """

    @pytest.mark.unit
    def test_no_output_when_no_tome_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: No .tome directory exists
        Given no .tome/sessions directory
        When the hook runs
        Then no output is produced
        """
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            main()
        assert capsys.readouterr().out == ""

    @pytest.mark.unit
    def test_no_output_when_no_sessions(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Empty sessions directory
        Given .tome/sessions exists but is empty
        When the hook runs
        Then no output is produced
        """
        (tmp_path / ".tome" / "sessions").mkdir(parents=True)
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            main()
        assert capsys.readouterr().out == ""

    @pytest.mark.unit
    def test_outputs_context_for_active_session(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Active research session exists
        Given a session file with status "active"
        When the hook runs
        Then additionalContext is printed with topic info
        """
        sessions_dir = tmp_path / ".tome" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {
            "topic": "async patterns",
            "status": "active",
            "findings": [{"title": "f1"}, {"title": "f2"}],
        }
        (sessions_dir / "test-001.json").write_text(json.dumps(session_data))

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            importlib.reload(mod)
            mod.main()

        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        assert "additionalContext" in result
        assert "async patterns" in result["additionalContext"]
        assert "2 findings" in result["additionalContext"]

    @pytest.mark.unit
    def test_no_output_for_complete_session(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Only completed sessions exist
        Given a session file with status "complete"
        When the hook runs
        Then no output is produced
        """
        sessions_dir = tmp_path / ".tome" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {"topic": "done topic", "status": "complete", "findings": []}
        (sessions_dir / "test-002.json").write_text(json.dumps(session_data))

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            importlib.reload(mod)
            mod.main()

        assert capsys.readouterr().out == ""
