"""Tests for War Room full flow orchestration.

Tests complete orchestration flows:
- Full convene() workflow
- Convene with escalation
- Convene failure handling
- Delphi convene flow
- Hook auto-trigger detection
"""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scripts.war_room_orchestrator import (
    WarRoomOrchestrator,
    _expert_availability,
    _haiku_fallback_notices,
)

# Phase method names that get mocked in convene tests
_CONVENE_PHASES = (
    "_phase_intel",
    "_phase_assessment",
    "_phase_coa_development",
    "_should_escalate",
    "_phase_red_team",
    "_phase_voting",
    "_phase_premortem",
    "_phase_synthesis",
)

_DELPHI_PHASES = (
    "_phase_intel",
    "_phase_assessment",
    "_phase_coa_development",
    "_phase_red_team",
    "_phase_voting",
    "_compute_convergence",
    "_delphi_revision_round",
    "_phase_premortem",
    "_phase_synthesis",
)


@pytest.fixture
def orchestrator(tmp_path: Path) -> WarRoomOrchestrator:
    """Create orchestrator with temp Strategeion path."""
    return WarRoomOrchestrator(strategeion_path=tmp_path)


@pytest.fixture
def convene_mocks(orchestrator: WarRoomOrchestrator):
    """Patch all convene phase methods and yield a name-to-mock dict.

    Each phase is patched as an AsyncMock. The caller can
    configure individual mocks via the returned dict.
    """
    with ExitStack() as stack:
        mocks: dict[str, AsyncMock] = {}
        for name in _CONVENE_PHASES:
            mock = stack.enter_context(
                patch.object(
                    orchestrator,
                    name,
                    new_callable=AsyncMock,
                )
            )
            mocks[name] = mock
        # Default: no escalation
        mocks["_should_escalate"].return_value = False
        yield mocks


@pytest.fixture
def delphi_mocks(orchestrator: WarRoomOrchestrator):
    """Patch all Delphi-flow phase methods and yield a name-to-mock dict."""
    with ExitStack() as stack:
        mocks: dict[str, AsyncMock] = {}
        for name in _DELPHI_PHASES:
            kw = {"new_callable": AsyncMock} if name != "_compute_convergence" else {}
            mock = stack.enter_context(patch.object(orchestrator, name, **kw))
            mocks[name] = mock
        yield mocks


# -------------------------------------------------------------------
# Hook auto-trigger detection
# -------------------------------------------------------------------


class TestHookAutoTrigger:
    """Test Phase 4: Hook auto-trigger detection."""

    def test_suggest_war_room_strategic_keywords(self) -> None:
        """Strategic keywords trigger War Room suggestion."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a critical architectural decision with significant "
            "trade-offs. Should we migrate to a new platform?"
        )

        assert result["suggest"] is True
        assert "architecture" in result["keywords_matched"] or any(
            kw in result["keywords_matched"]
            for kw in ["critical", "trade-off", "migration"]
        )
        assert result["confidence"] >= 0.7

    def test_suggest_war_room_multi_option(self) -> None:
        """Multi-option plus other keywords triggers suggestion."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "We're facing a complex choice between microservices or "
            "monolith with significant architectural implications"
        )

        assert result["suggest"] is True
        assert "microservices or monolith" in result["keywords_matched"]

    def test_suggest_war_room_low_complexity(self) -> None:
        """Simple tasks don't trigger suggestion."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "Add a button to the homepage"
        )

        assert result["suggest"] is False
        assert result["confidence"] < 0.7

    def test_suggest_war_room_trade_off(self) -> None:
        """Trade-off with complexity triggers suggestion."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "There's a complex trade-off here that could be risky "
            "and requires considering multiple approaches"
        )

        assert result["suggest"] is True
        assert "trade-off" in result["keywords_matched"]

    def test_suggest_war_room_threshold_configurable(self) -> None:
        """Complexity threshold is configurable."""
        message = "Should we refactor this module?"

        default_result = WarRoomOrchestrator.should_suggest_war_room(message)
        low_result = WarRoomOrchestrator.should_suggest_war_room(
            message, complexity_threshold=0.2
        )
        high_result = WarRoomOrchestrator.should_suggest_war_room(
            message, complexity_threshold=0.95
        )

        assert low_result["confidence"] == default_result["confidence"]
        assert low_result["suggest"] is True
        assert high_result["suggest"] is False

    def test_reason_multi_option(self) -> None:
        """Multi-option messages produce 'Multiple approaches' reason."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "Should we use microservices or monolith architecture?"
        )
        assert result["suggest"] is True
        assert "Multiple approaches" in result["reason"]

    def test_reason_strategic(self) -> None:
        """Strategic messages without multi-option produce strategic reason."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a critical architectural migration decision"
        )
        assert result["suggest"] is True
        assert "Strategic decision" in result["reason"]

    def test_reason_high_stakes(self) -> None:
        """High-stakes-only messages still trigger suggestion."""
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a risky uncertain complicated task that is critical"
        )
        assert result["suggest"] is True


# -------------------------------------------------------------------
# Full convene() flow
# -------------------------------------------------------------------


class TestFullConveneFlow:
    """Test full convene() flow with all phases."""

    @pytest.mark.asyncio
    async def test_convene_completes_all_phases(
        self,
        orchestrator: WarRoomOrchestrator,
        convene_mocks: dict[str, AsyncMock],
    ) -> None:
        """convene() calls every phase and sets status to completed."""
        session = await orchestrator.convene(
            problem="Test full flow",
            context_files=["*.py"],
            mode="lightweight",
        )

        assert session.status == "completed"
        assert session.session_id.startswith("war-room-")
        for name in _CONVENE_PHASES:
            if name != "_should_escalate":
                convene_mocks[name].assert_called_once()

    @pytest.mark.asyncio
    async def test_convene_triggers_escalation(
        self,
        orchestrator: WarRoomOrchestrator,
        convene_mocks: dict[str, AsyncMock],
    ) -> None:
        """convene() escalates to full_council when _should_escalate is True."""
        convene_mocks["_should_escalate"].return_value = True
        # Add _escalate mock (not in the default fixture)
        with patch.object(
            orchestrator, "_escalate", new_callable=AsyncMock
        ) as mock_escalate:
            session = await orchestrator.convene(
                problem="Complex problem",
                mode="lightweight",
            )

        assert session.escalated is True
        assert session.mode == "full_council"
        mock_escalate.assert_called_once()

    @pytest.mark.asyncio
    async def test_convene_failure_persists_session(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """convene() persists session even on failure."""
        with patch.object(
            orchestrator, "_phase_intel", new_callable=AsyncMock
        ) as mock_intel:
            mock_intel.side_effect = RuntimeError("Simulated failure")

            with pytest.raises(RuntimeError, match="Simulated failure"):
                await orchestrator.convene(problem="Failing test")

        sessions = orchestrator.list_sessions()
        assert len(sessions) == 1
        assert "failed" in sessions[0]["status"]

    @pytest.mark.asyncio
    async def test_convene_clears_availability_cache(
        self,
        orchestrator: WarRoomOrchestrator,
        convene_mocks: dict[str, AsyncMock],
    ) -> None:
        """convene() clears availability cache at start of session."""
        _expert_availability["test:model"] = True

        await orchestrator.convene("test problem")

        assert "test:model" not in _expert_availability

    @pytest.mark.asyncio
    async def test_convene_captures_fallback_notice(
        self,
        orchestrator: WarRoomOrchestrator,
        convene_mocks: dict[str, AsyncMock],
    ) -> None:
        """convene() captures fallback notices in session artifacts."""

        async def mock_intel_with_fallback(*_a, **_k):
            _haiku_fallback_notices.append("Test fallback notice")

        convene_mocks["_phase_intel"].side_effect = mock_intel_with_fallback

        session = await orchestrator.convene("test problem")

        assert "fallback_notice" in session.artifacts
        assert "Test fallback notice" in session.artifacts["fallback_notice"]


# -------------------------------------------------------------------
# Delphi convene flow
# -------------------------------------------------------------------


class TestDelphiConvene:
    """Test Delphi convene flow."""

    @pytest.mark.asyncio
    async def test_convene_delphi_full_flow(
        self,
        orchestrator: WarRoomOrchestrator,
        delphi_mocks: dict[str, AsyncMock],
    ) -> None:
        """Delphi convene iterates until convergence threshold is met."""
        # First call below threshold, second above
        delphi_mocks["_compute_convergence"].side_effect = [0.5, 0.9]

        session = await orchestrator.convene_delphi(
            problem="Delphi test",
            max_rounds=3,
            convergence_threshold=0.85,
        )

        assert session.status == "completed"
        assert session.metrics["delphi_mode"] is True
        assert session.metrics["final_convergence"] == 0.9

    @pytest.mark.asyncio
    async def test_convene_delphi_failure_persists(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """Delphi convene persists session on failure."""
        with patch.object(
            orchestrator, "_phase_intel", new_callable=AsyncMock
        ) as mock_intel:
            mock_intel.side_effect = RuntimeError("Delphi failure")

            with pytest.raises(RuntimeError, match="Delphi failure"):
                await orchestrator.convene_delphi(
                    problem="Failing Delphi test",
                )

        sessions = orchestrator.list_sessions()
        assert len(sessions) == 1
        assert "failed" in sessions[0]["status"]
