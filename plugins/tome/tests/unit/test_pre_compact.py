"""Tests for PreCompact hook."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import patch

import hooks.pre_compact as mod
import pytest
from hooks.pre_compact import main


class TestPreCompactHook:
    """
    Feature: Pre-compact session checkpoint

    As a researcher
    I want my session state preserved before compaction
    So that I don't lose research context
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
    def test_outputs_context_for_active_session(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Active session during compaction
        Given a session file with status "active"
        When the hook runs
        Then additionalContext confirms checkpoint
        """
        sessions_dir = tmp_path / ".tome" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {"topic": "cache eviction", "status": "active", "findings": []}
        (sessions_dir / "test-001.json").write_text(json.dumps(session_data))

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            importlib.reload(mod)
            mod.main()

        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        assert "additionalContext" in result
        assert "cache eviction" in result["additionalContext"]
        assert "checkpointed" in result["additionalContext"]

    @pytest.mark.unit
    def test_no_output_for_complete_session(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Only completed sessions during compaction
        Given a session with status "complete"
        When the hook runs
        Then no output is produced
        """
        sessions_dir = tmp_path / ".tome" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {"topic": "done", "status": "complete", "findings": []}
        (sessions_dir / "test-002.json").write_text(json.dumps(session_data))

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            importlib.reload(mod)
            mod.main()

        assert capsys.readouterr().out == ""
