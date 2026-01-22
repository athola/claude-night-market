"""Tests for War Room full flow orchestration.

Tests complete orchestration flows:
- Full convene() workflow
- Convene with escalation
- Convene failure handling
- Delphi convene flow
- Hook auto-trigger detection
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room_orchestrator import (
    WarRoomOrchestrator,
    _expert_availability,
    _haiku_fallback_notices,
)


class TestHookAutoTrigger:
    """Test Phase 4: Hook auto-trigger detection."""

    def test_suggest_war_room_strategic_keywords(self) -> None:
        """Strategic keywords trigger War Room suggestion with multiple matches."""
        # Multiple strategic keywords needed to hit threshold
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a critical architectural decision with significant trade-offs. "
            "Should we migrate to a new platform?"
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
            "We're facing a complex choice between microservices or monolith "
            "with significant architectural implications"
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
            "There's a complex trade-off here that could be risky and "
            "requires considering multiple approaches"
        )

        assert result["suggest"] is True
        assert "trade-off" in result["keywords_matched"]

    def test_suggest_war_room_threshold_configurable(self) -> None:
        """Complexity threshold is configurable."""
        message = "Should we refactor this module?"

        # Default threshold
        default_result = WarRoomOrchestrator.should_suggest_war_room(message)

        # Lower threshold
        low_result = WarRoomOrchestrator.should_suggest_war_room(
            message, complexity_threshold=0.2
        )

        # Higher threshold
        high_result = WarRoomOrchestrator.should_suggest_war_room(
            message, complexity_threshold=0.95
        )

        # Same confidence, different suggestions based on threshold
        assert low_result["confidence"] == default_result["confidence"]
        assert low_result["suggest"] is True  # Low threshold = easier to trigger
        assert high_result["suggest"] is False  # High threshold = harder to trigger

    def test_suggest_war_room_returns_correct_reason(self) -> None:
        """should_suggest_war_room returns appropriate reason strings."""
        # Test multi-option reason
        result = WarRoomOrchestrator.should_suggest_war_room(
            "Should we use microservices or monolith architecture?"
        )
        assert result["suggest"] is True
        assert "Multiple approaches" in result["reason"]

        # Test strategic reason (without multi-option)
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a critical architectural migration decision"
        )
        assert result["suggest"] is True
        assert "Strategic decision" in result["reason"]

        # Test high-stakes reason (stakes keywords only)
        result = WarRoomOrchestrator.should_suggest_war_room(
            "This is a risky uncertain complicated task that is critical"
        )
        assert result["suggest"] is True


class TestFullConveneFlow:
    """Test full convene() flow with all phases."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_convene_full_flow_mocked(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Test full convene() flow with all phases mocked."""
        # Mock all phase methods
        with patch.object(
            orchestrator, "_phase_intel", new_callable=AsyncMock
        ) as mock_intel:
            with patch.object(
                orchestrator, "_phase_assessment", new_callable=AsyncMock
            ) as mock_assessment:
                with patch.object(
                    orchestrator, "_phase_coa_development", new_callable=AsyncMock
                ) as mock_coa:
                    with patch.object(
                        orchestrator, "_should_escalate", new_callable=AsyncMock
                    ) as mock_escalate:
                        with patch.object(
                            orchestrator, "_phase_red_team", new_callable=AsyncMock
                        ) as mock_red_team:
                            with patch.object(
                                orchestrator, "_phase_voting", new_callable=AsyncMock
                            ) as mock_voting:
                                with patch.object(
                                    orchestrator,
                                    "_phase_premortem",
                                    new_callable=AsyncMock,
                                ) as mock_premortem:
                                    with patch.object(
                                        orchestrator,
                                        "_phase_synthesis",
                                        new_callable=AsyncMock,
                                    ) as mock_synthesis:
                                        mock_escalate.return_value = False

                                        session = await orchestrator.convene(
                                            problem="Test full flow",
                                            context_files=["*.py"],
                                            mode="lightweight",
                                        )

        assert session.status == "completed"
        assert session.session_id.startswith("war-room-")
        mock_intel.assert_called_once()
        mock_assessment.assert_called_once()
        mock_coa.assert_called_once()
        mock_red_team.assert_called_once()
        mock_voting.assert_called_once()
        mock_premortem.assert_called_once()
        mock_synthesis.assert_called_once()

    @pytest.mark.asyncio
    async def test_convene_with_escalation(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Test convene() flow triggers escalation when needed."""
        with patch.object(orchestrator, "_phase_intel", new_callable=AsyncMock):
            with patch.object(
                orchestrator, "_phase_assessment", new_callable=AsyncMock
            ):
                with patch.object(
                    orchestrator, "_phase_coa_development", new_callable=AsyncMock
                ):
                    with patch.object(
                        orchestrator, "_should_escalate", new_callable=AsyncMock
                    ) as mock_escalate:
                        with patch.object(
                            orchestrator, "_escalate", new_callable=AsyncMock
                        ) as mock_do_escalate:
                            with patch.object(
                                orchestrator, "_phase_red_team", new_callable=AsyncMock
                            ):
                                with patch.object(
                                    orchestrator,
                                    "_phase_voting",
                                    new_callable=AsyncMock,
                                ):
                                    with patch.object(
                                        orchestrator,
                                        "_phase_premortem",
                                        new_callable=AsyncMock,
                                    ):
                                        with patch.object(
                                            orchestrator,
                                            "_phase_synthesis",
                                            new_callable=AsyncMock,
                                        ):
                                            mock_escalate.return_value = True

                                            session = await orchestrator.convene(
                                                problem="Complex problem",
                                                mode="lightweight",
                                            )

        assert session.escalated is True
        assert session.mode == "full_council"
        mock_do_escalate.assert_called_once()

    @pytest.mark.asyncio
    async def test_convene_failure_persists_session(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Test convene() persists session even on failure."""
        with patch.object(
            orchestrator, "_phase_intel", new_callable=AsyncMock
        ) as mock_intel:
            mock_intel.side_effect = RuntimeError("Simulated failure")

            with pytest.raises(RuntimeError, match="Simulated failure"):
                await orchestrator.convene(problem="Failing test")

        # Session should still be persisted
        sessions = orchestrator.list_sessions()
        assert len(sessions) == 1
        assert "failed" in sessions[0]["status"]

    @pytest.mark.asyncio
    async def test_convene_clears_availability_cache(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """convene clears availability cache at start of session."""
        # Pre-populate cache
        _expert_availability["test:model"] = True

        # Mock all phases to do nothing
        with patch.object(orchestrator, "_phase_intel", new_callable=AsyncMock):
            with patch.object(
                orchestrator, "_phase_assessment", new_callable=AsyncMock
            ):
                with patch.object(
                    orchestrator, "_phase_coa_development", new_callable=AsyncMock
                ):
                    with patch.object(
                        orchestrator,
                        "_should_escalate",
                        new_callable=AsyncMock,
                        return_value=False,
                    ):
                        with patch.object(
                            orchestrator, "_phase_red_team", new_callable=AsyncMock
                        ):
                            with patch.object(
                                orchestrator, "_phase_voting", new_callable=AsyncMock
                            ):
                                with patch.object(
                                    orchestrator,
                                    "_phase_premortem",
                                    new_callable=AsyncMock,
                                ):
                                    with patch.object(
                                        orchestrator,
                                        "_phase_synthesis",
                                        new_callable=AsyncMock,
                                    ):
                                        await orchestrator.convene("test problem")

        # Cache should have been cleared
        assert "test:model" not in _expert_availability

    @pytest.mark.asyncio
    async def test_convene_captures_fallback_notice(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """convene captures fallback notices in session artifacts."""

        # Mock _phase_intel to add a fallback notice (simulating fallback during session)
        async def mock_intel_with_fallback(*_args, **_kwargs):
            _haiku_fallback_notices.append("Test fallback notice")

        # Mock all phases, with intel adding a fallback notice
        with patch.object(
            orchestrator, "_phase_intel", side_effect=mock_intel_with_fallback
        ):
            with patch.object(
                orchestrator, "_phase_assessment", new_callable=AsyncMock
            ):
                with patch.object(
                    orchestrator, "_phase_coa_development", new_callable=AsyncMock
                ):
                    with patch.object(
                        orchestrator,
                        "_should_escalate",
                        new_callable=AsyncMock,
                        return_value=False,
                    ):
                        with patch.object(
                            orchestrator, "_phase_red_team", new_callable=AsyncMock
                        ):
                            with patch.object(
                                orchestrator, "_phase_voting", new_callable=AsyncMock
                            ):
                                with patch.object(
                                    orchestrator,
                                    "_phase_premortem",
                                    new_callable=AsyncMock,
                                ):
                                    with patch.object(
                                        orchestrator,
                                        "_phase_synthesis",
                                        new_callable=AsyncMock,
                                    ):
                                        session = await orchestrator.convene(
                                            "test problem"
                                        )

        assert "fallback_notice" in session.artifacts
        assert "Test fallback notice" in session.artifacts["fallback_notice"]


class TestDelphiConvene:
    """Test Delphi convene flow."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_convene_delphi_full_flow(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Test Delphi convene flow with convergence."""
        with patch.object(orchestrator, "_phase_intel", new_callable=AsyncMock):
            with patch.object(
                orchestrator, "_phase_assessment", new_callable=AsyncMock
            ):
                with patch.object(
                    orchestrator, "_phase_coa_development", new_callable=AsyncMock
                ):
                    with patch.object(
                        orchestrator, "_phase_red_team", new_callable=AsyncMock
                    ):
                        with patch.object(
                            orchestrator, "_phase_voting", new_callable=AsyncMock
                        ):
                            with patch.object(
                                orchestrator, "_compute_convergence"
                            ) as mock_conv:
                                with patch.object(
                                    orchestrator,
                                    "_delphi_revision_round",
                                    new_callable=AsyncMock,
                                ):
                                    with patch.object(
                                        orchestrator,
                                        "_phase_premortem",
                                        new_callable=AsyncMock,
                                    ):
                                        with patch.object(
                                            orchestrator,
                                            "_phase_synthesis",
                                            new_callable=AsyncMock,
                                        ):
                                            # First call low, then high to exit loop
                                            mock_conv.side_effect = [0.5, 0.9]

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
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Delphi convene persists session on failure."""
        with patch.object(
            orchestrator, "_phase_intel", new_callable=AsyncMock
        ) as mock_intel:
            mock_intel.side_effect = RuntimeError("Delphi failure")

            with pytest.raises(RuntimeError, match="Delphi failure"):
                await orchestrator.convene_delphi(problem="Failing Delphi test")

        # Session should still be persisted
        sessions = orchestrator.list_sessions()
        assert len(sessions) == 1
        assert "failed" in sessions[0]["status"]
