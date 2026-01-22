"""Tests for War Room phase execution.

Tests individual phase implementations:
- Intel gathering (lightweight vs full council)
- Assessment phase
- COA development
- Red team challenges
- Voting and Borda scores
- Premortem analysis
- Synthesis and unsealing
- Escalation logic
- Delphi convergence
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room_orchestrator import (
    WarRoomOrchestrator,
    WarRoomSession,
)


class TestPhaseIntegration:
    """Integration tests for phase flow with mocked externals."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_intel_phase_lightweight(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Intel phase in lightweight mode only invokes Scout."""
        session = WarRoomSession(
            session_id="intel-test",
            problem_statement="Test intel gathering",
            mode="lightweight",
        )

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {"scout": "Scout report here"}

            await orchestrator._phase_intel(session, context_files=None)

            # Verify Scout was invoked
            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args
            experts_invoked = call_args[0][0]
            assert "scout" in experts_invoked
            assert "intelligence_officer" not in experts_invoked

        assert "intel" in session.phases_completed
        assert session.artifacts["intel"]["scout_report"] == "Scout report here"

    @pytest.mark.asyncio
    async def test_intel_phase_full_council(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Intel phase in full council mode invokes both Scout and Intel Officer."""
        session = WarRoomSession(
            session_id="intel-full-test",
            problem_statement="Test full intel",
            mode="full_council",
        )

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {
                "scout": "Scout report",
                "intelligence_officer": "Deep analysis",
            }

            await orchestrator._phase_intel(session, context_files=["*.py"])

            call_args = mock_invoke.call_args
            experts_invoked = call_args[0][0]
            assert "scout" in experts_invoked
            assert "intelligence_officer" in experts_invoked

        assert session.artifacts["intel"]["intel_report"] == "Deep analysis"


class TestAdditionalPhases:
    """Test additional phase implementations with mocked externals."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_assessment_phase(self, orchestrator: WarRoomOrchestrator) -> None:
        """Assessment phase invokes Chief Strategist."""
        session = WarRoomSession(
            session_id="assessment-test",
            problem_statement="Test assessment",
        )
        session.artifacts["intel"] = {
            "scout_report": "Scout findings",
            "intel_report": "Intel findings",
        }

        with patch.object(
            orchestrator, "_invoke_expert", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = "Strategic assessment content"

            await orchestrator._phase_assessment(session)

            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args
            assert call_args[0][0] == "chief_strategist"
            assert call_args[0][3] == "assessment"

        assert "assessment" in session.phases_completed
        assert (
            session.artifacts["assessment"]["content"] == "Strategic assessment content"
        )

    @pytest.mark.asyncio
    async def test_coa_development_phase_lightweight(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """COA development in lightweight mode only uses chief strategist."""
        session = WarRoomSession(
            session_id="coa-light-test",
            problem_statement="Test COA lightweight",
            mode="lightweight",
        )
        session.artifacts["assessment"] = {"content": "Assessment text"}

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {"chief_strategist": "COA from strategist"}

            await orchestrator._phase_coa_development(session)

            call_args = mock_invoke.call_args
            experts_invoked = call_args[0][0]
            assert experts_invoked == ["chief_strategist"]

        assert "coa" in session.phases_completed
        assert session.artifacts["coa"]["count"] == 1

    @pytest.mark.asyncio
    async def test_coa_development_phase_full_council(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """COA development in full council mode uses multiple experts."""
        session = WarRoomSession(
            session_id="coa-full-test",
            problem_statement="Test COA full council",
            mode="full_council",
        )
        session.artifacts["assessment"] = {"content": "Assessment text"}

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {
                "chief_strategist": "COA 1",
                "field_tactician": "COA 2",
                "logistics_officer": "COA 3",
            }

            await orchestrator._phase_coa_development(session)

            call_args = mock_invoke.call_args
            experts_invoked = call_args[0][0]
            assert "chief_strategist" in experts_invoked
            assert "field_tactician" in experts_invoked
            assert "logistics_officer" in experts_invoked

        assert session.artifacts["coa"]["count"] == 3

    @pytest.mark.asyncio
    async def test_red_team_phase(self, orchestrator: WarRoomOrchestrator) -> None:
        """Red team phase challenges COAs."""
        session = WarRoomSession(
            session_id="red-team-test",
            problem_statement="Test red team",
        )
        # Add some COAs to the merkle dag
        session.merkle_dag.add_contribution(
            content="COA Alpha content",
            phase="coa",
            round_number=1,
            expert_role="Strategist",
            expert_model="model-a",
        )
        session.merkle_dag.add_contribution(
            content="COA Beta content",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="model-b",
        )

        with patch.object(
            orchestrator, "_invoke_expert", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = "Red team challenges..."

            await orchestrator._phase_red_team(session)

            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args
            assert call_args[0][0] == "red_team"
            assert call_args[0][3] == "red_team"

        assert "red_team" in session.phases_completed
        assert session.artifacts["red_team"]["coas_reviewed"] == 2

    @pytest.mark.asyncio
    async def test_voting_phase(self, orchestrator: WarRoomOrchestrator) -> None:
        """Voting phase collects votes and computes Borda scores."""
        session = WarRoomSession(
            session_id="voting-test",
            problem_statement="Test voting",
            mode="lightweight",
        )
        session.merkle_dag.add_contribution(
            content="COA A",
            phase="coa",
            round_number=1,
            expert_role="Strategist",
            expert_model="model",
        )
        session.merkle_dag.add_contribution(
            content="COA B",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="model",
        )
        session.artifacts["red_team"] = {"challenges": "Challenges text"}

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {
                "chief_strategist": "1. Response A\n2. Response B",
                "red_team": "1. Response B\n2. Response A",
            }

            await orchestrator._phase_voting(session)

        assert "voting" in session.phases_completed
        assert "borda_scores" in session.artifacts["voting"]
        assert "finalists" in session.artifacts["voting"]

    @pytest.mark.asyncio
    async def test_premortem_phase_no_finalists(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Premortem phase handles no finalists gracefully."""
        session = WarRoomSession(
            session_id="premortem-empty-test",
            problem_statement="Test premortem empty",
        )
        session.artifacts["voting"] = {"finalists": []}

        await orchestrator._phase_premortem(session)

        assert "premortem" in session.phases_completed
        assert "error" in session.artifacts["premortem"]

    @pytest.mark.asyncio
    async def test_premortem_phase_with_finalists(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Premortem phase analyzes top finalist."""
        session = WarRoomSession(
            session_id="premortem-test",
            problem_statement="Test premortem",
            mode="lightweight",
        )
        session.merkle_dag.add_contribution(
            content="Winning COA content",
            phase="coa",
            round_number=1,
            expert_role="Strategist",
            expert_model="model",
        )
        session.artifacts["voting"] = {"finalists": ["Response A"]}

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {
                "chief_strategist": "Premortem analysis 1",
                "red_team": "Premortem analysis 2",
            }

            await orchestrator._phase_premortem(session)

        assert "premortem" in session.phases_completed
        assert session.artifacts["premortem"]["selected_coa"] == "Response A"


class TestEscalation:
    """Test escalation logic."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_should_escalate_low_coa_count(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Escalation triggers when COA count is too low."""
        session = WarRoomSession(
            session_id="escalate-test",
            problem_statement="Test escalation",
        )
        session.artifacts["coa"] = {"count": 1}
        session.artifacts["assessment"] = {"content": "Simple assessment"}

        should_escalate = await orchestrator._should_escalate(session)

        assert should_escalate is True
        assert session.escalation_reason is not None
        assert "Insufficient COA diversity" in session.escalation_reason

    @pytest.mark.asyncio
    async def test_should_escalate_high_complexity(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Escalation triggers on high complexity keywords."""
        session = WarRoomSession(
            session_id="complexity-test",
            problem_statement="Complex problem",
        )
        session.artifacts["coa"] = {"count": 3}
        # Include enough complexity keywords
        session.artifacts["assessment"] = {
            "content": "This is a complex architectural migration with "
            "significant risk and high stakes trade-off."
        }

        should_escalate = await orchestrator._should_escalate(session)

        assert should_escalate is True
        assert session.escalation_reason is not None
        assert "High complexity detected" in session.escalation_reason

    @pytest.mark.asyncio
    async def test_should_not_escalate_adequate_coas(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """No escalation when COA count and complexity are adequate."""
        session = WarRoomSession(
            session_id="no-escalate-test",
            problem_statement="Simple problem",
        )
        session.artifacts["coa"] = {"count": 3}
        session.artifacts["assessment"] = {"content": "Simple straightforward task."}

        should_escalate = await orchestrator._should_escalate(session)

        assert should_escalate is False
        assert session.escalation_reason is None

    @pytest.mark.asyncio
    async def test_escalate_invokes_additional_experts(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Escalation invokes additional intel and COA experts."""
        session = WarRoomSession(
            session_id="escalate-full-test",
            problem_statement="Complex problem",
            mode="lightweight",
        )
        session.artifacts["intel"] = {"scout_report": "Scout data"}
        session.artifacts["assessment"] = {"content": "Assessment"}
        session.artifacts["coa"] = {
            "raw_coas": {"chief_strategist": "COA 1"},
            "count": 1,
        }

        with patch.object(
            orchestrator, "_invoke_expert", new_callable=AsyncMock
        ) as mock_invoke_expert:
            with patch.object(
                orchestrator, "_invoke_parallel", new_callable=AsyncMock
            ) as mock_invoke_parallel:
                mock_invoke_expert.return_value = "Intel report"
                mock_invoke_parallel.return_value = {
                    "field_tactician": "COA 2",
                    "logistics_officer": "COA 3",
                }

                await orchestrator._escalate(session, context_files=["*.py"])

        assert session.mode == "full_council"
        assert session.artifacts["coa"]["escalated"] is True
        assert session.artifacts["coa"]["count"] == 3


class TestSynthesisPhase:
    """Test synthesis phase."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_synthesis_unseals_dag(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Synthesis phase unseals Merkle-DAG to reveal attribution."""
        session = WarRoomSession(
            session_id="synthesis-test",
            problem_statement="Test synthesis",
        )
        session.merkle_dag.add_contribution(
            content="COA content",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )
        session.artifacts = {
            "intel": {"scout_report": "Scout", "intel_report": "Intel"},
            "assessment": {"content": "Assessment"},
            "red_team": {"challenges": "Challenges"},
            "voting": {"borda_scores": {}, "finalists": []},
            "premortem": {"analyses": {}},
        }

        assert session.merkle_dag.sealed is True

        with patch.object(
            orchestrator, "_invoke_expert", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = "Supreme Commander Decision..."

            await orchestrator._phase_synthesis(session)

        assert session.merkle_dag.sealed is False
        assert "synthesis" in session.phases_completed
        assert session.artifacts["synthesis"]["attribution_revealed"] is True


class TestDelphiMode:
    """Test Phase 4: Delphi iterative convergence."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_compute_convergence_no_scores(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Convergence is 0 when no scores available."""
        session = WarRoomSession(
            session_id="conv-test",
            problem_statement="Test convergence",
        )
        session.artifacts["voting"] = {"borda_scores": {}}

        conv = orchestrator._compute_convergence(session)
        assert conv == 0.0

    def test_compute_convergence_with_scores(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Convergence computed from Borda score spread."""
        session = WarRoomSession(
            session_id="conv-test-2",
            problem_statement="Test convergence",
        )
        # Clear winner = high convergence
        session.artifacts["voting"] = {
            "borda_scores": {"Response A": 10, "Response B": 2, "Response C": 1}
        }

        conv = orchestrator._compute_convergence(session)
        assert 0.0 < conv <= 1.0

    def test_convergence_with_single_score(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Convergence computation handles single score edge case."""
        session = WarRoomSession(
            session_id="conv-single-test",
            problem_statement="Test convergence",
        )
        session.artifacts["voting"] = {"borda_scores": {"Response A": 5}}

        # Single score = no diversity to measure
        conv = orchestrator._compute_convergence(session)
        assert conv == 0.0

    def test_convergence_with_zero_mean(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Convergence handles all-zero scores."""
        session = WarRoomSession(
            session_id="conv-zero-test",
            problem_statement="Test convergence",
        )
        session.artifacts["voting"] = {
            "borda_scores": {"Response A": 0, "Response B": 0}
        }

        conv = orchestrator._compute_convergence(session)
        assert conv == 0.0

    @pytest.mark.asyncio
    async def test_delphi_revision_round(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Delphi revision round updates expert positions."""
        session = WarRoomSession(
            session_id="delphi-revision-test",
            problem_statement="Test Delphi revision",
            mode="full_council",
        )
        session.artifacts["red_team"] = {"challenges": "Red team feedback"}
        session.artifacts["coa"] = {
            "raw_coas": {
                "chief_strategist": "Original COA 1",
                "field_tactician": "Original COA 2",
            }
        }
        session.merkle_dag.add_contribution(
            content="Original COA 1",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="model",
        )

        with patch.object(
            orchestrator, "_invoke_parallel", new_callable=AsyncMock
        ) as mock_invoke:
            mock_invoke.return_value = {
                "chief_strategist": "Revised COA 1",
                "field_tactician": "Revised COA 2",
            }

            await orchestrator._delphi_revision_round(session, round_number=2)

        assert session.artifacts["coa"]["delphi_round"] == 2
        assert (
            session.artifacts["coa"]["raw_coas"]["chief_strategist"] == "Revised COA 1"
        )


class TestBordaScoring:
    """Test Borda count scoring."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_compute_borda_scores(self, orchestrator: WarRoomOrchestrator) -> None:
        """Borda count scoring works correctly."""
        votes = {
            "expert1": "1. Response A - best\n2. Response B - second",
            "expert2": "1. Response B - best\n2. Response A - second",
        }
        labels = ["Response A", "Response B"]

        scores = orchestrator._compute_borda_scores(votes, labels)

        # Both should have similar scores (tie)
        assert "Response A" in scores
        assert "Response B" in scores
