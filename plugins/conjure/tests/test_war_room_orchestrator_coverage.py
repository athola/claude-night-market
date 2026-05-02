"""Tests for war_room/orchestrator.py uncovered paths.

Targets _invoke_expert, _invoke_external, _invoke_haiku_fallback,
and _invoke_parallel to raise orchestrator.py coverage above 60%.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scripts.war_room import WarRoomOrchestrator
from scripts.war_room.experts import (
    ExpertConfig,
    _haiku_fallback_notices,
    clear_availability_cache,
)
from scripts.war_room.models import WarRoomSession


@pytest.fixture(autouse=True)
def _clean_availability():
    """Clear availability cache before and after each test."""
    clear_availability_cache()
    yield
    clear_availability_cache()


@pytest.fixture
def orchestrator(tmp_path: Path) -> WarRoomOrchestrator:
    """Create orchestrator with temp Strategeion path."""
    return WarRoomOrchestrator(strategeion_path=tmp_path)


@pytest.fixture
def session() -> WarRoomSession:
    """Create a minimal test session."""
    return WarRoomSession(
        session_id="orch-test",
        problem_statement="Test orchestrator paths",
    )


# -------------------------------------------------------------------
# _invoke_expert
# -------------------------------------------------------------------


class TestInvokeExpert:
    """Test _invoke_expert with different expert types."""

    @pytest.mark.asyncio
    async def test_invoke_native_expert(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Native experts return a placeholder response."""
        result = await orchestrator._invoke_expert(
            "supreme_commander",
            "Test prompt",
            session,
            "synthesis",
        )

        assert "[Native expert" in result
        assert "Supreme Commander" in result
        # Verify node was added to merkle dag
        assert len(session.merkle_dag.nodes) == 1
        node = list(session.merkle_dag.nodes.values())[0]
        assert node.phase == "synthesis"
        assert node.expert_role == "Supreme Commander"

    @pytest.mark.asyncio
    async def test_invoke_available_external_expert(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Patch the resolver and assert the orchestrator delegates to the external expert."""
        with patch(
            "scripts.war_room.experts.check_expert_availability",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch.object(
                orchestrator,
                "_invoke_external",
                new_callable=AsyncMock,
                return_value="External response",
            ) as mock_external:
                result = await orchestrator._invoke_expert(
                    "intelligence_officer",
                    "prompt",
                    session,
                    "intel",
                )

        assert result == "External response"
        mock_external.assert_called_once()
        # Verify merkle dag recorded it
        assert len(session.merkle_dag.nodes) == 1

    @pytest.mark.asyncio
    async def test_invoke_unavailable_expert_falls_back_to_haiku(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Unavailable external expert falls back to Haiku."""
        with patch(
            "scripts.war_room.experts.check_expert_availability",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with patch.object(
                orchestrator,
                "_invoke_haiku_fallback",
                new_callable=AsyncMock,
                return_value="Haiku fallback response",
            ) as mock_haiku:
                result = await orchestrator._invoke_expert(
                    "intelligence_officer",
                    "prompt",
                    session,
                    "intel",
                )

        assert result == "Haiku fallback response"
        mock_haiku.assert_called_once()
        # Fallback notice should be recorded
        assert len(_haiku_fallback_notices) == 1
        assert "Intelligence Officer" in _haiku_fallback_notices[0]
        # Merkle dag should record haiku model
        node = list(session.merkle_dag.nodes.values())[0]
        assert node.expert_model == "claude-haiku-3"


# -------------------------------------------------------------------
# _invoke_external
# -------------------------------------------------------------------


class TestInvokeExternal:
    """Test _invoke_external error paths."""

    @pytest.fixture
    def gemini_expert(self) -> ExpertConfig:
        """Create a gemini expert config for testing."""
        return ExpertConfig(
            role="Intelligence Officer",
            service="gemini",
            model="gemini-2.5-pro-exp",
            description="Test expert",
            phases=["intel"],
            command=["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
        )

    @pytest.mark.asyncio
    async def test_invoke_external_success(
        self,
        orchestrator: WarRoomOrchestrator,
        gemini_expert: ExpertConfig,
    ) -> None:
        """Successful external invocation returns stdout."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"Expert analysis result",
            b"",
        )

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_proc,
        ):
            result = await orchestrator._invoke_external(
                gemini_expert,
                "Analyze this",
            )

        assert result == "Expert analysis result"

    @pytest.mark.asyncio
    async def test_invoke_external_nonzero_exit(
        self,
        orchestrator: WarRoomOrchestrator,
        gemini_expert: ExpertConfig,
    ) -> None:
        """Non-zero exit code returns error message."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"API error")

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_proc,
        ):
            result = await orchestrator._invoke_external(
                gemini_expert,
                "Analyze",
            )

        assert "failed" in result
        assert "API error" in result

    @pytest.mark.asyncio
    async def test_invoke_external_timeout(
        self,
        orchestrator: WarRoomOrchestrator,
        gemini_expert: ExpertConfig,
    ) -> None:
        """Timeout returns timeout message."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = TimeoutError("timed out")

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_proc,
        ):
            result = await orchestrator._invoke_external(
                gemini_expert,
                "Analyze",
            )

        assert "timed out" in result

    @pytest.mark.asyncio
    async def test_invoke_external_command_not_found(
        self,
        orchestrator: WarRoomOrchestrator,
        gemini_expert: ExpertConfig,
    ) -> None:
        """FileNotFoundError returns command-not-found message."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("gemini not found"),
        ):
            result = await orchestrator._invoke_external(
                gemini_expert,
                "Analyze",
            )

        assert "command not found" in result

    @pytest.mark.asyncio
    async def test_invoke_external_generic_exception(
        self,
        orchestrator: WarRoomOrchestrator,
        gemini_expert: ExpertConfig,
    ) -> None:
        """Generic exception returns error message."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=RuntimeError("Unexpected"),
        ):
            result = await orchestrator._invoke_external(
                gemini_expert,
                "Analyze",
            )

        assert "error" in result
        assert "Unexpected" in result


# -------------------------------------------------------------------
# _invoke_haiku_fallback
# -------------------------------------------------------------------


class TestInvokeHaikuFallback:
    """Test _invoke_haiku_fallback error paths."""

    @pytest.fixture
    def mock_expert(self) -> MagicMock:
        """Create a mock expert with role and description."""
        expert = MagicMock()
        expert.role = "Field Tactician"
        expert.description = "Implementation feasibility"
        return expert

    @pytest.mark.asyncio
    async def test_haiku_fallback_success(
        self,
        orchestrator: WarRoomOrchestrator,
        mock_expert: MagicMock,
    ) -> None:
        """Successful Haiku fallback returns response."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Haiku response", b"")

        with patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            return_value=["claude", "--model", "claude-haiku-3", "-p"],
        ):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ):
                result = await orchestrator._invoke_haiku_fallback(
                    mock_expert,
                    "Test prompt",
                )

        assert result == "Haiku response"

    @pytest.mark.asyncio
    async def test_haiku_fallback_nonzero_exit(
        self,
        orchestrator: WarRoomOrchestrator,
        mock_expert: MagicMock,
    ) -> None:
        """Non-zero exit code returns failure message."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"CLI error")

        with patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            return_value=["claude", "--model", "claude-haiku-3", "-p"],
        ):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ):
                result = await orchestrator._invoke_haiku_fallback(
                    mock_expert,
                    "prompt",
                )

        assert "Haiku fallback" in result
        assert "failed" in result

    @pytest.mark.asyncio
    async def test_haiku_fallback_timeout(
        self,
        orchestrator: WarRoomOrchestrator,
        mock_expert: MagicMock,
    ) -> None:
        """Timeout returns timeout message with role."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = TimeoutError()

        with patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            return_value=["claude", "-p"],
        ):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ):
                result = await orchestrator._invoke_haiku_fallback(
                    mock_expert,
                    "prompt",
                )

        assert "timed out" in result
        assert "Field Tactician" in result

    @pytest.mark.asyncio
    async def test_haiku_fallback_cli_not_found(
        self,
        orchestrator: WarRoomOrchestrator,
        mock_expert: MagicMock,
    ) -> None:
        """FileNotFoundError returns CLI-not-found message."""
        with patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            return_value=["claude", "-p"],
        ):
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=FileNotFoundError(),
            ):
                result = await orchestrator._invoke_haiku_fallback(
                    mock_expert,
                    "prompt",
                )

        assert "CLI not found" in result

    @pytest.mark.asyncio
    async def test_haiku_fallback_generic_error(
        self,
        orchestrator: WarRoomOrchestrator,
        mock_expert: MagicMock,
    ) -> None:
        """Generic exception returns error with role."""
        with patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            return_value=["claude", "-p"],
        ):
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=RuntimeError("Unexpected"),
            ):
                result = await orchestrator._invoke_haiku_fallback(
                    mock_expert,
                    "prompt",
                )

        assert "Haiku fallback" in result
        assert "error" in result


# -------------------------------------------------------------------
# _invoke_parallel
# -------------------------------------------------------------------


class TestInvokeParallel:
    """Test _invoke_parallel with mixed results."""

    @pytest.mark.asyncio
    async def test_parallel_all_succeed(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """All experts succeed and results are collected."""
        with patch.object(
            orchestrator,
            "_invoke_expert",
            new_callable=AsyncMock,
        ) as mock_invoke:
            mock_invoke.side_effect = [
                "Response from commander",
                "Response from strategist",
            ]

            results = await orchestrator._invoke_parallel(
                ["supreme_commander", "chief_strategist"],
                {
                    "supreme_commander": "prompt1",
                    "chief_strategist": "prompt2",
                },
                session,
                "intel",
            )

        assert results["supreme_commander"] == "Response from commander"
        assert results["chief_strategist"] == "Response from strategist"
        assert mock_invoke.call_count == 2

    @pytest.mark.asyncio
    async def test_parallel_one_raises_exception(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Exception from one expert is captured as error string."""
        with patch.object(
            orchestrator,
            "_invoke_expert",
            new_callable=AsyncMock,
        ) as mock_invoke:
            mock_invoke.side_effect = [
                "Good response",
                RuntimeError("Expert failed"),
            ]

            results = await orchestrator._invoke_parallel(
                ["supreme_commander", "chief_strategist"],
                {
                    "supreme_commander": "prompt1",
                    "chief_strategist": "prompt2",
                },
                session,
                "coa",
            )

        assert results["supreme_commander"] == "Good response"
        assert "[Error:" in results["chief_strategist"]

    @pytest.mark.asyncio
    async def test_parallel_unknown_expert_skipped(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Unknown expert keys are filtered out."""
        with patch.object(
            orchestrator,
            "_invoke_expert",
            new_callable=AsyncMock,
        ) as mock_invoke:
            mock_invoke.return_value = "response"

            results = await orchestrator._invoke_parallel(
                ["supreme_commander", "nonexistent_expert"],
                {"supreme_commander": "prompt"},
                session,
                "intel",
            )

        # Only valid expert should have been invoked
        assert "supreme_commander" in results
        assert "nonexistent_expert" not in results
        mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_uses_default_prompt(
        self,
        orchestrator: WarRoomOrchestrator,
        session: WarRoomSession,
    ) -> None:
        """Missing per-expert prompt falls back to 'default' key."""
        with patch.object(
            orchestrator,
            "_invoke_expert",
            new_callable=AsyncMock,
        ) as mock_invoke:
            mock_invoke.return_value = "response"

            results = await orchestrator._invoke_parallel(
                ["supreme_commander"],
                {"default": "fallback prompt"},
                session,
                "voting",
            )

        assert "supreme_commander" in results
        # Verify the default prompt was used
        prompt_arg = mock_invoke.call_args.args[1]
        assert prompt_arg == "fallback prompt"
