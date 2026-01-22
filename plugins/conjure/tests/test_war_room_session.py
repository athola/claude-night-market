"""Tests for War Room session management.

Tests session initialization, persistence, and loading:
- Session creation with defaults
- Strategeion persistence
- Session loading and reconstruction
- Archive operations
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.war_room_orchestrator import (
    MerkleDAG,
    WarRoomOrchestrator,
    WarRoomSession,
)


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


class TestStrategeionPersistence:
    """Test Phase 3: Enhanced Strategeion persistence."""

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

    def test_initialize_session_creates_unique_id(
        self, orchestrator: WarRoomOrchestrator
    ) -> None:
        """_initialize_session creates session with timestamp-based ID."""
        session = orchestrator._initialize_session("Test problem", "lightweight")

        assert session.session_id.startswith("war-room-")
        assert session.problem_statement == "Test problem"
        assert session.mode == "lightweight"
        assert session.status == "initialized"
