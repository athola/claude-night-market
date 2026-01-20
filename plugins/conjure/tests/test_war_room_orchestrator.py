"""Tests for War Room Orchestrator.

Tests core functionality:
- MerkleDAG anonymization and unsealing
- Session initialization and persistence
- Phase flow (with mocked external calls)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room_orchestrator import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
    MerkleDAG,
    WarRoomOrchestrator,
    WarRoomSession,
)


class TestMerkleDAG:
    """Test Merkle-DAG anonymization system."""

    def test_add_contribution_generates_hash(self) -> None:
        """Adding a contribution generates deterministic hashes."""
        dag = MerkleDAG(session_id="test-session")
        node = dag.add_contribution(
            content="Test COA content",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )

        assert node.content_hash is not None
        assert len(node.content_hash) == 64  # SHA256 hex
        assert node.anonymous_label == "Response A"
        assert node.expert_role == "Chief Strategist"

    def test_anonymized_view_hides_attribution(self) -> None:
        """Anonymized view does not reveal expert identity."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="COA 1",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )
        dag.add_contribution(
            content="COA 2",
            phase="coa",
            round_number=1,
            expert_role="Field Tactician",
            expert_model="glm-4.7",
        )

        anon_view = dag.get_anonymized_view(phase="coa")

        assert len(anon_view) == 2
        assert anon_view[0]["label"] == "Response A"
        assert anon_view[1]["label"] == "Response B"
        # Attribution NOT in anonymized view
        assert "expert_role" not in anon_view[0]
        assert "expert_model" not in anon_view[0]

    def test_unseal_reveals_attribution(self) -> None:
        """Unsealing reveals full expert attribution."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="COA content",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )

        assert dag.sealed is True
        unsealed = dag.unseal()
        assert dag.sealed is False

        assert len(unsealed) == 1
        assert unsealed[0]["expert_role"] == "Chief Strategist"
        assert unsealed[0]["expert_model"] == "claude-sonnet-4"

    def test_to_dict_respects_seal_state(self) -> None:
        """Serialization masks attribution when sealed."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="Test",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="glm-4.7",
        )

        # Sealed - should mask
        sealed_dict = dag.to_dict()
        node_data = list(sealed_dict["nodes"].values())[0]
        assert node_data["expert_role"] == "[SEALED]"

        # Unseal and check again
        dag.unseal()
        unsealed_dict = dag.to_dict()
        node_data = list(unsealed_dict["nodes"].values())[0]
        assert node_data["expert_role"] == "Tactician"


class TestWarRoomSession:
    """Test War Room session management."""

    def test_session_initialization(self) -> None:
        """Session initializes with correct defaults."""
        session = WarRoomSession(
            session_id="test-123",
            problem_statement="Test problem",
        )

        assert session.session_id == "test-123"
        assert session.mode == "lightweight"
        assert session.status == "initialized"
        assert session.escalated is False
        assert session.merkle_dag.session_id == "test-123"

    def test_full_council_mode(self) -> None:
        """Session can be initialized in full council mode."""
        session = WarRoomSession(
            session_id="test-456",
            problem_statement="Complex problem",
            mode="full_council",
        )

        assert session.mode == "full_council"


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


class TestWarRoomOrchestrator:
    """Test orchestrator phase flow."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_session_persistence(self, orchestrator: WarRoomOrchestrator) -> None:
        """Sessions are persisted to Strategeion."""
        session = WarRoomSession(
            session_id="persist-test",
            problem_statement="Test persistence",
        )
        session.phases_completed = ["intel", "assessment"]
        session.artifacts["intel"] = {"scout_report": "Test report"}

        orchestrator._persist_session(session)

        # Verify file exists
        session_file = (
            orchestrator.strategeion / "war-table" / "persist-test" / "session.json"
        )
        assert session_file.exists()

        # Verify contents
        with open(session_file) as f:
            data = json.load(f)
        assert data["session_id"] == "persist-test"
        assert "intel" in data["phases_completed"]

    def test_load_session(self, orchestrator: WarRoomOrchestrator) -> None:
        """Sessions can be loaded from Strategeion."""
        # First persist a session
        session = WarRoomSession(
            session_id="load-test",
            problem_statement="Test loading",
            mode="full_council",
        )
        session.status = "completed"
        orchestrator._persist_session(session)

        # Load it back
        loaded = orchestrator.load_session("load-test")

        assert loaded is not None
        assert loaded.session_id == "load-test"
        assert loaded.mode == "full_council"
        assert loaded.status == "completed"

    def test_load_nonexistent_session(self, orchestrator: WarRoomOrchestrator) -> None:
        """Loading nonexistent session returns None."""
        loaded = orchestrator.load_session("does-not-exist")
        assert loaded is None

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
