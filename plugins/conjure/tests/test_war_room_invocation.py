"""Tests for War Room expert invocation and external calls.

Tests expert invocation:
- External command invocation
- Haiku fallback for unavailable experts
- Parallel invocation error handling
- Native expert placeholders
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room_orchestrator import (
    EXPERT_CONFIGS,
    ExpertConfig,
    WarRoomOrchestrator,
    WarRoomSession,
    _expert_availability,
    _haiku_fallback_notices,
    clear_availability_cache,
    get_fallback_notice,
    get_haiku_command,
    test_expert_availability,
)


class TestExternalInvocation:
    """Test external expert invocation and error handling."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_invoke_external_command_not_found(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation handles command not found gracefully."""
        fake_expert = ExpertConfig(
            role="Fake Expert",
            service="fake",
            model="fake-model",
            description="Test expert",
            phases=["test"],
            command=["nonexistent_command_12345", "-p"],
        )

        result = await orchestrator._invoke_external(fake_expert, "test prompt")

        assert "[Fake Expert command not found" in result

    @pytest.mark.asyncio
    async def test_invoke_external_timeout(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation handles timeout."""
        # Use sleep command that will timeout
        fake_expert = ExpertConfig(
            role="Slow Expert",
            service="test",
            model="test-model",
            description="Slow test expert",
            phases=["test"],
            command=["sleep", "200"],
        )

        # Patch timeout to be very short
        with patch.object(asyncio, "wait_for", side_effect=TimeoutError()):
            result = await orchestrator._invoke_external(fake_expert, "test")

        assert "[Slow Expert timed out" in result

    @pytest.mark.asyncio
    async def test_invoke_expert_native_placeholder(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Native experts return placeholder (handled by orchestrating Claude)."""
        session = WarRoomSession(
            session_id="native-test",
            problem_statement="Test native invocation",
        )

        result = await orchestrator._invoke_expert(
            "supreme_commander", "test prompt", session, "synthesis"
        )

        assert "[Native expert Supreme Commander response placeholder]" in result
        assert len(session.merkle_dag.nodes) == 1

    @pytest.mark.asyncio
    async def test_invoke_external_nonzero_return(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation handles non-zero return code."""
        # Use 'false' command which returns exit code 1
        fake_expert = ExpertConfig(
            role="Failing Expert",
            service="test",
            model="test-model",
            description="Test expert that fails",
            phases=["test"],
            command=["false"],
        )

        result = await orchestrator._invoke_external(fake_expert, "test prompt")
        assert "[Failing Expert failed:" in result

    @pytest.mark.asyncio
    async def test_invoke_external_general_exception(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation handles general exceptions."""
        fake_expert = ExpertConfig(
            role="Error Expert",
            service="test",
            model="test-model",
            description="Test expert",
            phases=["test"],
            command=["echo", "test"],
        )

        # Mock create_subprocess_exec to raise a general exception
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=OSError("Simulated OS error"),
        ):
            result = await orchestrator._invoke_external(fake_expert, "test")
            assert "[Error Expert error:" in result

    @pytest.mark.asyncio
    async def test_invoke_expert_external_service(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_invoke_expert calls _invoke_external for non-native services when available."""
        session = WarRoomSession(
            session_id="external-test",
            problem_statement="Test external invocation",
        )

        # Mock availability to return True (expert is available)
        with patch(
            "scripts.war_room_orchestrator.test_expert_availability",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch.object(
                orchestrator, "_invoke_external", new_callable=AsyncMock
            ) as mock_external:
                mock_external.return_value = "External response"

                # Scout is an external service (qwen)
                result = await orchestrator._invoke_expert(
                    "scout", "test prompt", session, "intel"
                )

                mock_external.assert_called_once()
                assert result == "External response"

    @pytest.mark.asyncio
    async def test_invoke_external_successful_stdout(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation returns decoded stdout on success."""
        # Use echo command which succeeds and outputs
        fake_expert = ExpertConfig(
            role="Echo Expert",
            service="test",
            model="test-model",
            description="Test expert",
            phases=["test"],
            command=["echo", "hello world"],
        )

        result = await orchestrator._invoke_external(fake_expert, "")
        assert "hello world" in result


class TestParallelInvocation:
    """Test parallel expert invocation."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_invoke_parallel_handles_exceptions(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Parallel invocation handles individual expert failures."""
        session = WarRoomSession(
            session_id="parallel-error-test",
            problem_statement="Test parallel errors",
        )

        async def mock_invoke_expert(
            expert_key: str, _prompt: str, _session: WarRoomSession, _phase: str
        ) -> str:
            if expert_key == "chief_strategist":
                raise RuntimeError("Simulated failure")
            return f"Success from {expert_key}"

        with patch.object(
            orchestrator, "_invoke_expert", side_effect=mock_invoke_expert
        ):
            results = await orchestrator._invoke_parallel(
                ["chief_strategist", "red_team"],
                {"default": "test prompt"},
                session,
                "test",
            )

        assert "[Error:" in results["chief_strategist"]
        assert "Success from red_team" in results["red_team"]

    @pytest.mark.asyncio
    async def test_invoke_parallel_skips_unknown_experts(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Parallel invocation skips experts not in EXPERT_CONFIGS."""
        session = WarRoomSession(
            session_id="skip-unknown-test",
            problem_statement="Test unknown experts",
        )

        with patch.object(
            orchestrator, "_invoke_expert", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = "test result"

            results = await orchestrator._invoke_parallel(
                ["chief_strategist", "unknown_expert_xyz"],
                {"default": "test prompt"},
                session,
                "test",
            )

        # Only known expert should be invoked
        assert mock_invoke.call_count == 1
        assert "chief_strategist" in results
        assert "unknown_expert_xyz" not in results

    @pytest.mark.asyncio
    async def test_invoke_parallel_non_string_result(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Parallel invocation converts non-string results to string."""
        session = WarRoomSession(
            session_id="non-string-test",
            problem_statement="Test non-string results",
        )

        async def mock_invoke_expert(
            _expert_key: str, _prompt: str, _session: WarRoomSession, _phase: str
        ) -> int:
            # Return an integer instead of string
            return 42

        with patch.object(
            orchestrator, "_invoke_expert", side_effect=mock_invoke_expert
        ):
            results = await orchestrator._invoke_parallel(
                ["chief_strategist"],
                {"default": "test prompt"},
                session,
                "test",
            )

        # Non-string result should be converted to string
        assert results["chief_strategist"] == "42"


class TestHaikuFallback:
    """Test Haiku fallback for unavailable external LLMs."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_clear_availability_cache(self) -> None:
        """Availability cache can be cleared."""
        # Populate cache
        _expert_availability["test:model"] = True
        _haiku_fallback_notices.append("test notice")

        clear_availability_cache()

        assert len(_expert_availability) == 0
        assert len(_haiku_fallback_notices) == 0

    def test_get_fallback_notice_empty(self) -> None:
        """get_fallback_notice returns empty string when no fallbacks."""
        clear_availability_cache()
        assert get_fallback_notice() == ""

    def test_get_fallback_notice_with_notices(self) -> None:
        """get_fallback_notice formats notices when present."""
        clear_availability_cache()
        _haiku_fallback_notices.append("Scout (qwen-turbo) unavailable, using Haiku")
        _haiku_fallback_notices.append("Red Team (gemini) unavailable, using Haiku")

        notice = get_fallback_notice()

        assert "External LLM Fallbacks" in notice
        assert "Scout" in notice
        assert "Red Team" in notice

    def test_get_haiku_command_with_claude(self) -> None:
        """get_haiku_command returns claude command when available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/claude"
            cmd = get_haiku_command()
            assert cmd == ["claude", "--model", "claude-haiku-3", "-p"]

    def test_get_haiku_command_not_found(self) -> None:
        """get_haiku_command raises when claude not available."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="Claude CLI not found"):
                get_haiku_command()

    @pytest.mark.asyncio
    async def test_expert_availability_caches_result(self) -> None:
        """test_expert_availability caches results to avoid repeated probes."""
        clear_availability_cache()
        expert = EXPERT_CONFIGS["scout"]

        # Mock subprocess to fail
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("command not found"),
        ):
            result1 = await test_expert_availability(expert)
            result2 = await test_expert_availability(expert)

        assert result1 is False
        assert result2 is False
        # Should only have called once (cached)
        assert f"{expert.service}:{expert.model}" in _expert_availability

    @pytest.mark.asyncio
    async def test_expert_availability_native_always_available(self) -> None:
        """Native experts are always reported as available."""
        clear_availability_cache()
        expert = EXPERT_CONFIGS["supreme_commander"]

        result = await test_expert_availability(expert)
        assert result is True

    @pytest.mark.asyncio
    async def test_invoke_expert_uses_fallback_when_unavailable(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_invoke_expert falls back to Haiku when external expert unavailable."""
        clear_availability_cache()

        session = WarRoomSession(
            session_id="fallback-test",
            problem_statement="Test fallback",
        )

        # Mock availability to return False
        with patch(
            "scripts.war_room_orchestrator.test_expert_availability",
            new_callable=AsyncMock,
            return_value=False,
        ):
            # Mock Haiku fallback to return success
            with patch.object(
                orchestrator,
                "_invoke_haiku_fallback",
                new_callable=AsyncMock,
                return_value="Haiku fallback response",
            ):
                result = await orchestrator._invoke_expert(
                    "scout", "test prompt", session, "intel"
                )

        assert result == "Haiku fallback response"
        assert any("Scout" in n for n in _haiku_fallback_notices)

        # Verify model recorded is Haiku, not original
        node = list(session.merkle_dag.nodes.values())[0]
        assert node.expert_model == "claude-haiku-3"

    @pytest.mark.asyncio
    async def test_invoke_haiku_fallback_prepends_role(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_invoke_haiku_fallback prepends role context to prompt."""
        fake_expert = ExpertConfig(
            role="Test Expert",
            service="test",
            model="test-model",
            description="Expert for testing",
            phases=["test"],
            command=["test"],
        )

        # Capture the command that would be executed
        captured_cmd = []

        async def mock_subprocess(*args, **_kwargs):
            captured_cmd.extend(args)

            class MockProcess:
                returncode = 0

                async def communicate(self):
                    return (b"test response", b"")

            return MockProcess()

        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess):
                with patch("asyncio.wait_for", side_effect=lambda coro, **_: coro):
                    await orchestrator._invoke_haiku_fallback(
                        fake_expert, "original prompt"
                    )

        # The prompt should contain role prefix
        prompt_arg = captured_cmd[-1]
        assert "Test Expert" in prompt_arg
        assert "Expert for testing" in prompt_arg
        assert "original prompt" in prompt_arg
