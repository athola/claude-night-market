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
from scripts.war_room import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
    ExpertConfig,
    active_panel,
    get_expert_command,
    get_glm_command,
)
from scripts.war_room.experts import _COMMAND_RESOLVERS


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
        assert len(FULL_COUNCIL) == 10

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

    def test_minimax_experts_use_official_mmx_command(self) -> None:
        """MiniMax experts invoke the official ``mmx`` CLI contract.

        ``mmx text chat --message`` is the documented text interface; the
        orchestrator appends the prompt as the final argv element, so
        ``--message`` must be the trailing flag.
        """
        advisor = EXPERT_CONFIGS["operational_advisor"]
        analyst = EXPERT_CONFIGS["skeptical_analyst"]

        assert advisor.service == "minimax"
        assert advisor.model == "MiniMax-M3"
        assert get_expert_command(advisor) == [
            "mmx",
            "text",
            "chat",
            "--model",
            "MiniMax-M3",
            "--message",
        ]

        assert analyst.service == "minimax"
        assert analyst.model == "MiniMax-M2.7"
        assert get_expert_command(analyst) == [
            "mmx",
            "text",
            "chat",
            "--model",
            "MiniMax-M2.7",
            "--message",
        ]

    def test_minimax_experts_are_optional(self) -> None:
        """MiniMax experts are opt-in so they cannot change existing councils."""
        assert EXPERT_CONFIGS["operational_advisor"].optional is True
        assert EXPERT_CONFIGS["skeptical_analyst"].optional is True

    def test_established_experts_are_not_optional(self) -> None:
        """Gating applies only to experts added after the council existed."""
        for key in ("supreme_commander", "chief_strategist", "red_team", "scout"):
            assert EXPERT_CONFIGS[key].optional is False

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
                # Asserts the remedy, not the version. The message used to
                # name GLM-5.2 and outlived that release; pinning a version
                # here is what turned a model bump into a test failure.
                with pytest.raises(RuntimeError, match="Install claude-glm"):
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

        with patch.dict(_COMMAND_RESOLVERS, {"bad_resolver": bad_resolver}):
            with pytest.raises(RuntimeError, match="did not return list"):
                get_expert_command(fake_expert)


class TestActivePanel:
    """Optional experts join a panel only when their CLI is installed."""

    def test_optional_experts_dropped_when_cli_missing(self) -> None:
        """Without ``mmx`` on PATH the MiniMax experts cast no ballots.

        Otherwise they fall back to Haiku and add duplicate votes to the
        Borda count for users who never installed MiniMax.
        """
        with patch("scripts.war_room.experts.shutil.which", return_value=None):
            panel = active_panel(FULL_COUNCIL)

        assert "operational_advisor" not in panel
        assert "skeptical_analyst" not in panel
        assert "chief_strategist" in panel
        assert "red_team" in panel

    def test_optional_experts_kept_when_cli_present(self) -> None:
        """With ``mmx`` installed the MiniMax experts join the full council."""
        with patch(
            "scripts.war_room.experts.shutil.which", return_value="/usr/bin/mmx"
        ):
            panel = active_panel(FULL_COUNCIL)

        assert "operational_advisor" in panel
        assert "skeptical_analyst" in panel

    def test_active_panel_preserves_order_and_membership(self) -> None:
        """Gating never reorders or invents panel members."""
        with patch(
            "scripts.war_room.experts.shutil.which", return_value="/usr/bin/mmx"
        ):
            assert active_panel(FULL_COUNCIL) == FULL_COUNCIL
            assert active_panel(LIGHTWEIGHT_PANEL) == LIGHTWEIGHT_PANEL


class TestMuseExpert:
    """Meta's Muse Code joins the council on its documented contract."""

    def test_muse_expert_uses_the_documented_exec_contract(self) -> None:
        """``muse exec`` takes the prompt positionally.

        The orchestrator appends the prompt as the final argv element, so a
        command ending in a flag would consume it as that flag's value.
        Muse documents no prompt flag at all, so the command ends at
        ``exec`` and the prompt lands in the right place.
        """
        expert = EXPERT_CONFIGS["systems_engineer"]

        assert expert.service == "muse"
        assert expert.model == "muse-spark-1.2"
        assert get_expert_command(expert) == ["muse", "exec"]

    def test_muse_expert_is_optional(self) -> None:
        """Muse is not installed by default, so it must opt in.

        An expert whose CLI is absent otherwise votes through the Haiku
        fallback, which puts a ballot in the Borda count that no external
        model actually cast.
        """
        assert EXPERT_CONFIGS["systems_engineer"].optional is True
