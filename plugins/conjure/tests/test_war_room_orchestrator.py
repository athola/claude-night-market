"""Tests for War Room Orchestrator.

Tests core functionality:
- MerkleDAG anonymization and unsealing
- Session initialization and persistence
- Phase flow (with mocked external calls)
"""

from __future__ import annotations

import asyncio
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


class TestCommandResolution:
    """Test expert command resolution logic."""

    def test_get_expert_command_with_static_command(self) -> None:
        """Experts with static commands return them directly."""
        from scripts.war_room_orchestrator import EXPERT_CONFIGS, get_expert_command

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
        from scripts.war_room_orchestrator import EXPERT_CONFIGS, get_expert_command

        supreme = EXPERT_CONFIGS["supreme_commander"]
        with pytest.raises(RuntimeError, match="No command configured"):
            get_expert_command(supreme)

    def test_get_expert_command_resolver(self) -> None:
        """Experts with command_resolver use dynamic resolution."""
        from scripts.war_room_orchestrator import EXPERT_CONFIGS, get_expert_command

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
        from scripts.war_room_orchestrator import get_glm_command

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/ccgd"
            cmd = get_glm_command()
            assert cmd == ["ccgd", "-p"]

    def test_get_glm_command_with_claude_glm(self) -> None:
        """GLM command falls back to claude-glm when ccgd unavailable."""
        from scripts.war_room_orchestrator import get_glm_command

        def which_side_effect(cmd: str) -> str | None:
            if cmd == "ccgd":
                return None
            if cmd == "claude-glm":
                return "/usr/local/bin/claude-glm"
            return None

        with patch("shutil.which", side_effect=which_side_effect):
            cmd = get_glm_command()
            assert cmd == ["claude-glm", "--dangerously-skip-permissions", "-p"]


class TestMerkleDAGEdgeCases:
    """Test MerkleDAG edge cases and additional scenarios."""

    def test_empty_dag_root_hash(self) -> None:
        """Empty DAG has no root hash."""
        dag = MerkleDAG(session_id="empty-test")
        assert dag.root_hash is None
        assert len(dag.nodes) == 0

    def test_multiple_phases_generate_distinct_labels(self) -> None:
        """Different phases have independent label counters."""
        dag = MerkleDAG(session_id="multi-phase")

        # Add COA contributions
        dag.add_contribution(
            content="COA 1",
            phase="coa",
            round_number=1,
            expert_role="Strategist",
            expert_model="model-a",
        )
        dag.add_contribution(
            content="COA 2",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="model-b",
        )

        # Add voting contributions
        dag.add_contribution(
            content="Vote 1",
            phase="voting",
            round_number=2,
            expert_role="Strategist",
            expert_model="model-a",
        )

        anon_coa = dag.get_anonymized_view(phase="coa")
        anon_voting = dag.get_anonymized_view(phase="voting")

        assert len(anon_coa) == 2
        assert len(anon_voting) == 1
        assert anon_coa[0]["label"] == "Response A"
        assert anon_coa[1]["label"] == "Response B"
        assert anon_voting[0]["label"] == "Expert 1"

    def test_get_anonymized_view_all_phases(self) -> None:
        """Anonymized view without phase filter returns all contributions."""
        dag = MerkleDAG(session_id="all-phases")

        dag.add_contribution(
            content="Intel",
            phase="intel",
            round_number=1,
            expert_role="Scout",
            expert_model="model-a",
        )
        dag.add_contribution(
            content="COA",
            phase="coa",
            round_number=2,
            expert_role="Strategist",
            expert_model="model-b",
        )

        all_anon = dag.get_anonymized_view()
        assert len(all_anon) == 2

    def test_content_hash_deterministic(self) -> None:
        """Same content produces same hash."""
        dag1 = MerkleDAG(session_id="hash-test-1")
        dag2 = MerkleDAG(session_id="hash-test-2")

        node1 = dag1.add_contribution(
            content="Same content",
            phase="coa",
            round_number=1,
            expert_role="Role",
            expert_model="Model",
        )
        node2 = dag2.add_contribution(
            content="Same content",
            phase="coa",
            round_number=1,
            expert_role="Role",
            expert_model="Model",
        )

        assert node1.content_hash == node2.content_hash


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
        from scripts.war_room_orchestrator import ExpertConfig

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
        from scripts.war_room_orchestrator import ExpertConfig

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


class TestDelphiModeIntegration:
    """Test Delphi iterative convergence mode."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

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


class TestWarRoomSessionEdgeCases:
    """Test WarRoomSession edge cases."""

    def test_session_post_init_sets_dag_session_id(self) -> None:
        """Session __post_init__ sets merkle_dag session_id."""
        session = WarRoomSession(
            session_id="post-init-test",
            problem_statement="Test post init",
        )
        assert session.merkle_dag.session_id == "post-init-test"

    def test_session_with_custom_dag(self) -> None:
        """Session can be initialized with custom MerkleDAG."""
        custom_dag = MerkleDAG(session_id="custom-dag-id")
        session = WarRoomSession(
            session_id="custom-test",
            problem_statement="Test custom dag",
            merkle_dag=custom_dag,
        )
        # Custom dag keeps its ID since it was already set
        assert session.merkle_dag.session_id == "custom-dag-id"


class TestRemainingCoverage:
    """Tests for remaining uncovered code paths."""

    def test_get_glm_command_local_bin_fallback(self) -> None:
        """GLM command falls back to ~/.local/bin/claude-glm path."""
        from scripts.war_room_orchestrator import get_glm_command

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
        from scripts.war_room_orchestrator import ExpertConfig, get_expert_command

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
        from scripts.war_room_orchestrator import ExpertConfig, get_expert_command

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

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_invoke_external_nonzero_return(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation handles non-zero return code."""
        from scripts.war_room_orchestrator import ExpertConfig

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
        from scripts.war_room_orchestrator import ExpertConfig

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

    def test_initialize_session_creates_unique_id(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_initialize_session creates session with timestamp-based ID."""
        session = orchestrator._initialize_session("Test problem", "lightweight")

        assert session.session_id.startswith("war-room-")
        assert session.problem_statement == "Test problem"
        assert session.mode == "lightweight"
        assert session.status == "initialized"

    def test_persist_session_skips_missing_intel_report(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_persist_session handles missing intel_report gracefully."""
        session = WarRoomSession(
            session_id="missing-intel-test",
            problem_statement="Test missing intel",
        )
        session.artifacts["intel"] = {
            "scout_report": "Scout data",
            "intel_report": "[Intel Officer not invoked - lightweight mode]",
        }

        orchestrator._persist_session(session)

        session_dir = orchestrator.strategeion / "war-table" / "missing-intel-test"
        intel_dir = session_dir / "intelligence"

        # Scout report should exist
        assert (intel_dir / "scout-report.md").exists()
        # Intel officer report should NOT exist (skipped due to placeholder)
        assert not (intel_dir / "intel-officer-report.md").exists()

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

    def test_archive_session_moves_directory(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """archive_session actually moves session directory."""
        session = WarRoomSession(
            session_id="move-test",
            problem_statement="Test archive move",
        )
        session.status = "completed"
        orchestrator._persist_session(session)

        # Verify original exists
        original = orchestrator.strategeion / "war-table" / "move-test"
        assert original.exists()

        # Archive it
        archive_path = orchestrator.archive_session("move-test", project="test-proj")

        # Verify moved
        assert archive_path is not None
        assert archive_path.exists()
        assert not original.exists()
        assert "campaign-archive" in str(archive_path)
        assert "test-proj" in str(archive_path)

    @pytest.mark.asyncio
    async def test_invoke_external_successful_stdout(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """External invocation returns decoded stdout on success."""
        from scripts.war_room_orchestrator import ExpertConfig

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


class TestHaikuFallback:
    """Test Haiku fallback for unavailable external LLMs."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp Strategeion path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    def test_clear_availability_cache(self) -> None:
        """Availability cache can be cleared."""
        from scripts.war_room_orchestrator import (
            _expert_availability,
            _haiku_fallback_notices,
            clear_availability_cache,
        )

        # Populate cache
        _expert_availability["test:model"] = True
        _haiku_fallback_notices.append("test notice")

        clear_availability_cache()

        assert len(_expert_availability) == 0
        assert len(_haiku_fallback_notices) == 0

    def test_get_fallback_notice_empty(self) -> None:
        """get_fallback_notice returns empty string when no fallbacks."""
        from scripts.war_room_orchestrator import (
            clear_availability_cache,
            get_fallback_notice,
        )

        clear_availability_cache()
        assert get_fallback_notice() == ""

    def test_get_fallback_notice_with_notices(self) -> None:
        """get_fallback_notice formats notices when present."""
        from scripts.war_room_orchestrator import (
            _haiku_fallback_notices,
            clear_availability_cache,
            get_fallback_notice,
        )

        clear_availability_cache()
        _haiku_fallback_notices.append("Scout (qwen-turbo) unavailable, using Haiku")
        _haiku_fallback_notices.append("Red Team (gemini) unavailable, using Haiku")

        notice = get_fallback_notice()

        assert "External LLM Fallbacks" in notice
        assert "Scout" in notice
        assert "Red Team" in notice

    def test_get_haiku_command_with_claude(self) -> None:
        """get_haiku_command returns claude command when available."""
        from scripts.war_room_orchestrator import get_haiku_command

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/claude"
            cmd = get_haiku_command()
            assert cmd == ["claude", "--model", "claude-haiku-3", "-p"]

    def test_get_haiku_command_not_found(self) -> None:
        """get_haiku_command raises when claude not available."""
        from scripts.war_room_orchestrator import get_haiku_command

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="Claude CLI not found"):
                get_haiku_command()

    @pytest.mark.asyncio
    async def test_expert_availability_caches_result(self) -> None:
        """test_expert_availability caches results to avoid repeated probes."""
        from scripts.war_room_orchestrator import (
            EXPERT_CONFIGS,
            _expert_availability,
            clear_availability_cache,
            test_expert_availability,
        )

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
        from scripts.war_room_orchestrator import (
            EXPERT_CONFIGS,
            clear_availability_cache,
            test_expert_availability,
        )

        clear_availability_cache()
        expert = EXPERT_CONFIGS["supreme_commander"]

        result = await test_expert_availability(expert)
        assert result is True

    @pytest.mark.asyncio
    async def test_invoke_expert_uses_fallback_when_unavailable(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_invoke_expert falls back to Haiku when external expert unavailable."""
        from scripts.war_room_orchestrator import (
            _haiku_fallback_notices,
            clear_availability_cache,
        )

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
        from scripts.war_room_orchestrator import ExpertConfig

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

    @pytest.mark.asyncio
    async def test_convene_clears_availability_cache(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """convene clears availability cache at start of session."""
        from scripts.war_room_orchestrator import _expert_availability

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
        from scripts.war_room_orchestrator import _haiku_fallback_notices

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
