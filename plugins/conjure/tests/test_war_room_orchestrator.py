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


class TestStrategeionPersistence:
    """Test Phase 3: Enhanced Strategeion persistence."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_persist_creates_subdirectories(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Persistence creates intelligence/, battle-plans/, wargames/, orders/."""
        session = WarRoomSession(
            session_id="subdir-test",
            problem_statement="Test subdirectories",
        )
        session.artifacts = {
            "intel": {"scout_report": "Scout data"},
            "assessment": {"content": "Assessment content"},
            "coa": {"raw_coas": {"chief_strategist": "COA content"}},
            "red_team": {"challenges": "Red team challenges"},
            "premortem": {"analyses": {"expert1": "Premortem analysis"}},
            "synthesis": {"decision": "Final decision document"},
        }
        session.status = "completed"

        orchestrator._persist_session(session)

        session_dir = orchestrator.strategeion / "war-table" / "subdir-test"
        assert (session_dir / "intelligence").is_dir()
        assert (session_dir / "battle-plans").is_dir()
        assert (session_dir / "wargames").is_dir()
        assert (session_dir / "orders").is_dir()

        # Check files created
        assert (session_dir / "intelligence" / "scout-report.md").exists()
        assert (session_dir / "intelligence" / "situation-assessment.md").exists()
        assert (session_dir / "battle-plans" / "coa-chief_strategist.md").exists()
        assert (session_dir / "wargames" / "red-team-challenges.md").exists()
        assert (session_dir / "wargames" / "premortem-analyses.md").exists()
        assert (session_dir / "orders" / "supreme-commander-decision.md").exists()

    def test_archive_session(self, orchestrator: WarRoomOrchestrator) -> None:
        """Completed sessions can be archived to campaign-archive."""
        session = WarRoomSession(
            session_id="archive-test",
            problem_statement="Test archiving",
        )
        session.status = "completed"

        orchestrator._persist_session(session)

        # Archive it
        archive_path = orchestrator.archive_session(
            "archive-test", project="test-project"
        )

        assert archive_path is not None
        assert "campaign-archive" in str(archive_path)
        assert "test-project" in str(archive_path)

        # Original location should be gone
        original = orchestrator.strategeion / "war-table" / "archive-test"
        assert not original.exists()

    def test_archive_incomplete_session_fails(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Incomplete sessions cannot be archived."""
        session = WarRoomSession(
            session_id="incomplete-test",
            problem_statement="Incomplete session",
        )
        session.status = "in_progress"

        orchestrator._persist_session(session)

        result = orchestrator.archive_session("incomplete-test")
        assert result is None

    def test_list_sessions(self, orchestrator: WarRoomOrchestrator) -> None:
        """List sessions shows active and optionally archived."""
        # Create two sessions
        for i in range(2):
            session = WarRoomSession(
                session_id=f"list-test-{i}",
                problem_statement=f"Problem {i}",
            )
            session.status = "completed" if i == 0 else "in_progress"
            orchestrator._persist_session(session)

        sessions = orchestrator.list_sessions()
        assert len(sessions) == 2

        # Archive one
        orchestrator.archive_session("list-test-0")

        # Without archived
        active = orchestrator.list_sessions(include_archived=False)
        assert len(active) == 1

        # With archived
        all_sessions = orchestrator.list_sessions(include_archived=True)
        assert len(all_sessions) == 2

    def test_load_session_reconstructs_merkle_dag(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """Loading session fully reconstructs MerkleDAG."""
        session = WarRoomSession(
            session_id="dag-test",
            problem_statement="Test DAG reconstruction",
        )
        session.merkle_dag.add_contribution(
            content="Test COA",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )

        orchestrator._persist_session(session)

        # Load and verify
        loaded = orchestrator.load_session("dag-test")
        assert loaded is not None
        assert len(loaded.merkle_dag.nodes) == 1

        node = list(loaded.merkle_dag.nodes.values())[0]
        assert node.phase == "coa"
        assert node.anonymous_label == "Response A"


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
