"""Tests for framework_detect.py — agentic framework auto-detection.

Feature: Detect which agentic framework is running

As a night-market user
I want automatic detection of my runtime environment
So that skills and tools adapt to the right framework.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from framework_detect import detect_framework


class TestFrameworkDetection:
    """
    Feature: Detect agentic framework from environment

    As a bootstrapper
    I want to identify Claude Code, OpenClaw, or NemoClaw
    So that I can adapt behavior to the active runtime.
    """

    @pytest.mark.unit
    def test_detects_claude_code(self) -> None:
        """
        Scenario: Running inside Claude Code
        Given CLAUDE_CODE_VERSION is set
        When I detect the framework
        Then it identifies Claude Code.
        """
        env = {"CLAUDE_CODE_VERSION": "2.1.80", "HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.name == "claude-code"
        assert info.version == "2.1.80"

    @pytest.mark.unit
    def test_detects_openclaw(self) -> None:
        """
        Scenario: Running inside OpenClaw
        Given OPENCLAW_HOME is set
        When I detect the framework
        Then it identifies OpenClaw.
        """
        env = {"OPENCLAW_HOME": "/home/user/.openclaw", "HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.name == "openclaw"

    @pytest.mark.unit
    def test_detects_nemoclaw(self) -> None:
        """
        Scenario: Running inside NemoClaw
        Given NEMOCLAW_SANDBOX is set
        When I detect the framework
        Then it identifies NemoClaw.
        """
        env = {"NEMOCLAW_SANDBOX": "1", "OPENCLAW_HOME": "/x", "HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.name == "nemoclaw"

    @pytest.mark.unit
    def test_nemoclaw_takes_precedence_over_openclaw(self) -> None:
        """
        Scenario: Both NemoClaw and OpenClaw vars present
        Given NemoClaw runs on top of OpenClaw
        When both env vars are set
        Then NemoClaw is detected (more specific).
        """
        env = {
            "NEMOCLAW_SANDBOX": "1",
            "OPENCLAW_HOME": "/home/user/.openclaw",
            "HOME": "/home/user",
        }
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.name == "nemoclaw"

    @pytest.mark.unit
    def test_detects_unknown(self) -> None:
        """
        Scenario: No known framework detected
        Given no framework environment variables
        When I detect the framework
        Then it returns unknown with MCP suggestion.
        """
        env = {"HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.name == "unknown"

    @pytest.mark.unit
    def test_framework_info_has_install_hint(self) -> None:
        """
        Scenario: Install hints for each framework
        Given a detected framework
        When I check install_hint
        Then it contains framework-specific instructions.
        """
        env = {"OPENCLAW_HOME": "/home/user/.openclaw", "HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert "openclaw" in info.install_hint.lower()

    @pytest.mark.unit
    def test_framework_info_has_capabilities(self) -> None:
        """
        Scenario: Capability flags per framework
        Given a Claude Code detection
        When I check capabilities
        Then it shows skills, agents, hooks, commands support.
        """
        env = {"CLAUDE_CODE_VERSION": "2.1.80", "HOME": "/home/user"}
        with patch.dict("os.environ", env, clear=True):
            info = detect_framework()
        assert info.capabilities["skills"] is True
        assert info.capabilities["agents"] is True
        assert info.capabilities["hooks"] is True
        assert info.capabilities["commands"] is True
