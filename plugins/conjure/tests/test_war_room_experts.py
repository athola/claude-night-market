"""Tests for War Room expert configuration and command resolution.

Tests expert panel configuration:
- Lightweight and full council panels
- Native experts (no subprocess command)
- Command resolution with fallback
- GLM command detection
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.war_room_orchestrator import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
    ExpertConfig,
    get_expert_command,
    get_glm_command,
)


class TestExpertConfiguration:
    """Test expert panel configuration."""

    def test_lightweight_panel_has_required_experts(self) -> None:
        """Lightweight panel includes minimum required experts."""
        assert "supreme_commander" in LIGHTWEIGHT_PANEL
        assert "chief_strategist" in LIGHTWEIGHT_PANEL
        assert "red_team" in LIGHTWEIGHT_PANEL
        assert len(LIGHTWEIGHT_PANEL) == 3

    def test_full_council_includes_all_experts(self) -> None:
        """Full council includes all configured experts."""
        assert set(FULL_COUNCIL) == set(EXPERT_CONFIGS.keys())
        assert len(FULL_COUNCIL) == 7

    def test_native_experts_have_no_command(self) -> None:
        """Native experts (Opus, Sonnet) should not have subprocess commands."""
        for key in ["supreme_commander", "chief_strategist"]:
            expert = EXPERT_CONFIGS[key]
            assert expert.service == "native"
            assert expert.command is None
            assert expert.dangerous is False


class TestCommandResolution:
    """Test expert command resolution logic."""

    def test_get_expert_command_with_static_command(self) -> None:
        """Experts with static commands return them directly."""
        # Scout has a static command
        scout = EXPERT_CONFIGS["scout"]
        cmd = get_expert_command(scout)

        assert cmd == ["qwen", "--model", "qwen-turbo", "-p"]
        # Verify it's a copy (not mutating original)
        cmd.append("test")
        assert EXPERT_CONFIGS["scout"].command == [
            "qwen",
            "--model",
            "qwen-turbo",
            "-p",
        ]

    def test_get_expert_command_native_raises(self) -> None:
        """Native experts (no command) raise RuntimeError."""
        supreme = EXPERT_CONFIGS["supreme_commander"]
        with pytest.raises(RuntimeError, match="No command configured"):
            get_expert_command(supreme)

    def test_get_expert_command_resolver(self) -> None:
        """Experts with command_resolver use dynamic resolution."""
        tactician = EXPERT_CONFIGS["field_tactician"]
        assert tactician.command_resolver == "get_glm_command"

        # Mock shutil.which to return None for all commands to force error
        def mock_which(_cmd: str) -> None:
            return None

        # Also mock Path.exists to return False for direct path check
        with patch("shutil.which", side_effect=mock_which):
            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(RuntimeError, match="GLM-4.7 not available"):
                    get_expert_command(tactician)

    def test_get_glm_command_with_ccgd_alias(self) -> None:
        """GLM command prefers ccgd alias when available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/ccgd"
            cmd = get_glm_command()
            assert cmd == ["ccgd", "-p"]

    def test_get_glm_command_with_claude_glm(self) -> None:
        """GLM command falls back to claude-glm when ccgd unavailable."""

        def which_side_effect(cmd: str) -> str | None:
            if cmd == "ccgd":
                return None
            if cmd == "claude-glm":
                return "/usr/local/bin/claude-glm"
            return None

        with patch("shutil.which", side_effect=which_side_effect):
            cmd = get_glm_command()
            assert cmd == ["claude-glm", "--dangerously-skip-permissions", "-p"]

    def test_get_glm_command_local_bin_fallback(self) -> None:
        """GLM command falls back to ~/.local/bin/claude-glm path."""

        def which_returns_none(_cmd: str) -> None:
            return None

        with patch("shutil.which", side_effect=which_returns_none):
            with patch.object(Path, "exists", return_value=True):
                cmd = get_glm_command()
                assert "--dangerously-skip-permissions" in cmd
                assert "-p" in cmd
                assert ".local/bin/claude-glm" in cmd[0]

    def test_get_expert_command_invalid_resolver(self) -> None:
        """get_expert_command raises for unknown command resolver."""
        fake_expert = ExpertConfig(
            role="Test Expert",
            service="test",
            model="test-model",
            description="Test",
            phases=["test"],
            command_resolver="nonexistent_resolver_function",
        )

        with pytest.raises(RuntimeError, match="Unknown command resolver"):
            get_expert_command(fake_expert)

    def test_get_expert_command_resolver_returns_non_list(self) -> None:
        """get_expert_command raises when resolver returns non-list."""

        # Create a resolver that returns a string instead of list
        def bad_resolver() -> str:
            return "not a list"

        fake_expert = ExpertConfig(
            role="Test Expert",
            service="test",
            model="test-model",
            description="Test",
            phases=["test"],
            command_resolver="bad_resolver",
        )

        with patch.dict(
            "scripts.war_room_orchestrator.__dict__", {"bad_resolver": bad_resolver}
        ):
            with pytest.raises(RuntimeError, match="did not return list"):
                get_expert_command(fake_expert)
