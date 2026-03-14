"""BDD tests for War Room audit trail functionality.

Feature: Audit Trail for War Room Checkpoints
  As a War Room operator
  I want every checkpoint decision and session to be recorded in an immutable trail
  So that I can verify integrity, review decisions, and satisfy compliance requirements
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest
from scripts.war_room.audit_trail import (
    AUDIT_REPORT_FILENAME,
    CHECKPOINT_DIR,
    AuditReport,
    AuditTrailManager,
    CheckpointEntry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_checkpoint(
    session_id: str = "sess-001",
    checkpoint_id: str = "cp-001",
    phase: str = "coa",
    action: str = "express",
    reversibility_score: float = 0.35,
) -> CheckpointEntry:
    return CheckpointEntry(
        checkpoint_id=checkpoint_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        phase=phase,
        action=action,
        reversibility_score=reversibility_score,
        dimensions={"reversal_cost": 2, "blast_radius": 1},
        decision_context="Test decision",
        files_affected=["src/main.py"],
        confidence=0.9,
        requires_user_confirmation=False,
    )


def _make_session_data(session_id: str = "sess-001") -> dict:
    """Build a minimal session_data dict matching persistence.py's format."""
    return {
        "session_id": session_id,
        "problem_statement": "Should we refactor the auth module?",
        "mode": "lightweight",
        "status": "completed",
        "escalated": False,
        "escalation_reason": None,
        "phases_completed": ["intel", "assessment", "coa", "voting", "synthesis"],
        "artifacts": {
            "coa": {
                "raw_coas": {
                    "chief_strategist": "Use OAuth2 with PKCE",
                    "field_tactician": "Incremental migration path",
                },
                "count": 2,
            },
            "voting": {
                "borda_scores": {"Response A": 10, "Response B": 6},
                "finalists": ["Response A"],
            },
            "synthesis": {
                "decision": "Adopt OAuth2 with PKCE immediately",
                "rationale": "Best security posture with low migration cost",
                "attribution_revealed": True,
            },
        },
        "metrics": {
            "start_time": "2026-03-03T10:00:00+00:00",
            "end_time": "2026-03-03T10:05:00+00:00",
        },
        "merkle_dag": {
            "session_id": session_id,
            "sealed": False,
            "root_hash": None,
            "label_counter": {},
            "nodes": {},
        },
    }


def _make_session_data_with_merkle(session_id: str = "sess-merkle") -> dict:
    """Build session data with a valid Merkle-DAG node."""
    content = "Test COA content"
    role = "Chief Strategist"
    model = "claude-sonnet-4"

    content_hash = sha256(content.encode()).hexdigest()
    metadata_hash = sha256(f"{role}:{model}".encode()).hexdigest()
    combined_hash = sha256(f"{content_hash}:{metadata_hash}".encode()).hexdigest()
    node_id = combined_hash[:16]
    root_hash = sha256(combined_hash.encode()).hexdigest()

    node = {
        "node_id": node_id,
        "parent_id": None,
        "round_number": 1,
        "phase": "coa",
        "anonymous_label": "Response A",
        "content": content,
        "expert_role": role,
        "expert_model": model,
        "content_hash": content_hash,
        "metadata_hash": metadata_hash,
        "combined_hash": combined_hash,
        "timestamp": "2026-03-03T10:01:00",
    }

    data = _make_session_data(session_id)
    data["merkle_dag"] = {
        "session_id": session_id,
        "sealed": False,
        "root_hash": root_hash,
        "label_counter": {"coa": 1},
        "nodes": {node_id: node},
    }
    return data, node_id, combined_hash, root_hash


# ===========================================================================
# TestCheckpointEntry
# ===========================================================================


class TestCheckpointEntry:
    """Feature: CheckpointEntry data model.

    As a checkpoint logger
    I want to serialise and deserialise checkpoint events
    So that they survive round-trips through JSON on disk
    """

    @pytest.mark.unit
    def test_to_dict_contains_all_fields(self) -> None:
        """Scenario: Serialise a checkpoint entry
        Given a fully-populated CheckpointEntry
        When to_dict() is called
        Then every field is present in the returned dict.
        """
        entry = _make_checkpoint()
        result = entry.to_dict()

        assert result["checkpoint_id"] == "cp-001"
        assert result["session_id"] == "sess-001"
        assert result["phase"] == "coa"
        assert result["action"] == "express"
        assert result["reversibility_score"] == 0.35
        assert result["dimensions"] == {"reversal_cost": 2, "blast_radius": 1}
        assert result["files_affected"] == ["src/main.py"]
        assert result["confidence"] == 0.9
        assert result["requires_user_confirmation"] is False

    @pytest.mark.unit
    def test_from_dict_roundtrip(self) -> None:
        """Scenario: Deserialise a checkpoint entry
        Given a dict produced by to_dict()
        When from_dict() is called
        Then the resulting entry is equal to the original.
        """
        original = _make_checkpoint()
        reconstructed = CheckpointEntry.from_dict(original.to_dict())

        assert reconstructed.checkpoint_id == original.checkpoint_id
        assert reconstructed.session_id == original.session_id
        assert reconstructed.phase == original.phase
        assert reconstructed.action == original.action
        assert reconstructed.reversibility_score == original.reversibility_score
        assert reconstructed.dimensions == original.dimensions
        assert reconstructed.confidence == original.confidence

    @pytest.mark.unit
    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Scenario: Deserialise with extra keys
        Given a dict that contains keys not in the dataclass
        When from_dict() is called
        Then unknown keys are silently ignored.
        """
        data = _make_checkpoint().to_dict()
        data["future_field"] = "ignored"
        entry = CheckpointEntry.from_dict(data)
        assert entry.checkpoint_id == "cp-001"

    @pytest.mark.unit
    def test_default_fields_are_populated(self) -> None:
        """Scenario: Minimal CheckpointEntry construction
        Given only required fields are provided
        When the entry is created
        Then mutable default fields are empty containers, not shared references.
        """
        e1 = CheckpointEntry(
            checkpoint_id="a",
            timestamp="t",
            session_id="s",
            phase="p",
            action="express",
            reversibility_score=0.1,
        )
        e2 = CheckpointEntry(
            checkpoint_id="b",
            timestamp="t",
            session_id="s",
            phase="p",
            action="express",
            reversibility_score=0.2,
        )
        e1.files_affected.append("x.py")
        assert e2.files_affected == [], "mutable defaults must not be shared"


# ===========================================================================
# TestAuditReport
# ===========================================================================


class TestAuditReport:
    """Feature: AuditReport data model.

    As a compliance officer
    I want a structured audit report
    So that I can review full session history in one document
    """

    @pytest.mark.unit
    def test_creation_with_defaults(self) -> None:
        """Scenario: Create a minimal AuditReport
        Given required scalar fields
        When AuditReport is constructed
        Then list and dict fields default to empty containers.
        """
        report = AuditReport(
            session_id="s",
            generated_at="t",
            problem_statement="p",
            mode="lightweight",
            status="completed",
            duration_seconds=42.0,
        )
        assert report.phases_completed == []
        assert report.checkpoints == []
        assert report.voting_summary == {}
        assert report.escalation_history == []

    @pytest.mark.unit
    def test_to_dict_is_json_serialisable(self) -> None:
        """Scenario: Serialise an AuditReport to JSON
        Given a populated AuditReport
        When to_dict() result is passed to json.dumps()
        Then no exception is raised and the output is valid JSON.
        """
        report = AuditReport(
            session_id="s",
            generated_at="t",
            problem_statement="p",
            mode="lightweight",
            status="completed",
            duration_seconds=10.5,
            phases_completed=["intel", "coa"],
            final_decision="Go ahead",
        )
        dumped = json.dumps(report.to_dict())
        reloaded = json.loads(dumped)
        assert reloaded["session_id"] == "s"
        assert reloaded["final_decision"] == "Go ahead"


# ===========================================================================
# TestAuditTrailManager
# ===========================================================================


class TestAuditTrailManager:
    """Feature: AuditTrailManager persistence and reporting.

    As a War Room operator
    I want to log checkpoints and generate audit reports
    So that every decision is traceable and verifiable
    """

    # -----------------------------------------------------------------------
    # Checkpoint I/O
    # -----------------------------------------------------------------------

    @pytest.mark.unit
    def test_log_checkpoint_creates_file(self, tmp_path: Path) -> None:
        """Scenario: Log a checkpoint
        Given an AuditTrailManager pointed at a temp directory
        When log_checkpoint() is called
        Then a JSON file is created in checkpoints/{date}/{id}.json.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        entry = _make_checkpoint(checkpoint_id="cp-log-01")

        filepath = manager.log_checkpoint(entry)

        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert filepath.stem == "cp-log-01"
        # Must be inside the checkpoints directory
        assert CHECKPOINT_DIR in str(filepath)

    @pytest.mark.unit
    def test_log_checkpoint_content_is_valid_json(self, tmp_path: Path) -> None:
        """Scenario: Checkpoint file contains correct JSON
        Given a logged checkpoint
        When the file is read back
        Then it deserialises to the original entry's fields.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        entry = _make_checkpoint(checkpoint_id="cp-json-01", session_id="sess-json")

        filepath = manager.log_checkpoint(entry)
        data = json.loads(filepath.read_text())

        assert data["checkpoint_id"] == "cp-json-01"
        assert data["session_id"] == "sess-json"
        assert data["reversibility_score"] == 0.35

    @pytest.mark.unit
    def test_get_checkpoints_by_session_id(self, tmp_path: Path) -> None:
        """Scenario: Filter checkpoints by session
        Given checkpoints for two different sessions
        When get_checkpoints() is called with one session id
        Then only that session's checkpoints are returned.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-A", checkpoint_id="cp-A1")
        )
        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-A", checkpoint_id="cp-A2")
        )
        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-B", checkpoint_id="cp-B1")
        )

        results = manager.get_checkpoints("sess-A")

        assert len(results) == 2
        assert all(r.session_id == "sess-A" for r in results)
        ids = {r.checkpoint_id for r in results}
        assert ids == {"cp-A1", "cp-A2"}

    @pytest.mark.unit
    def test_get_checkpoints_empty_when_dir_missing(self, tmp_path: Path) -> None:
        """Scenario: No checkpoints directory exists
        Given a fresh strategeion directory with no checkpoints folder
        When get_checkpoints() is called
        Then an empty list is returned without raising.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        # Do NOT create checkpoints_dir
        results = manager.get_checkpoints("sess-ghost")
        assert results == []

    @pytest.mark.unit
    def test_get_checkpoints_returns_empty_for_unknown_session(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Query checkpoints for a session with no entries
        Given checkpoints exist for sess-X only
        When get_checkpoints("sess-Y") is called
        Then an empty list is returned.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-X", checkpoint_id="cp-X1")
        )

        results = manager.get_checkpoints("sess-Y")
        assert results == []

    # -----------------------------------------------------------------------
    # Merkle-DAG verification
    # -----------------------------------------------------------------------

    @pytest.mark.unit
    def test_verify_merkle_dag_empty_nodes(self, tmp_path: Path) -> None:
        """Scenario: Verify a session with no Merkle-DAG nodes
        Given session data with an empty nodes dict
        When verify_merkle_dag() is called
        Then verified=True and node_count=0.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()  # merkle_dag.nodes == {}

        result = manager.verify_merkle_dag(session_data)

        assert result["verified"] is True
        assert result["node_count"] == 0

    @pytest.mark.unit
    def test_verify_merkle_dag_valid_node(self, tmp_path: Path) -> None:
        """Scenario: Verify an untampered session
        Given a session whose node hashes were computed by MerkleDAG.add_contribution()
        When verify_merkle_dag() is called
        Then verified=True and all node results report valid=True.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, node_id, _, _ = _make_session_data_with_merkle()

        result = manager.verify_merkle_dag(session_data)

        assert result["verified"] is True
        assert result["node_count"] == 1
        assert result["nodes"][0]["valid"] is True
        assert result["nodes"][0]["content_hash_valid"] is True
        assert result["nodes"][0]["metadata_hash_valid"] is True
        assert result["nodes"][0]["combined_hash_valid"] is True

    @pytest.mark.unit
    def test_verify_merkle_dag_tampered_content(self, tmp_path: Path) -> None:
        """Scenario: Detect tampered node content
        Given a session where a node's content has been modified after hashing
        When verify_merkle_dag() is called
        Then verified=False and the tampered node reports content_hash_valid=False.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, node_id, _, _ = _make_session_data_with_merkle()

        # Tamper with content without updating the hash
        session_data["merkle_dag"]["nodes"][node_id]["content"] = "TAMPERED content"

        result = manager.verify_merkle_dag(session_data)

        assert result["verified"] is False
        node_result = result["nodes"][0]
        assert node_result["content_hash_valid"] is False

    @pytest.mark.unit
    def test_verify_merkle_dag_tampered_root_hash(self, tmp_path: Path) -> None:
        """Scenario: Detect a falsified root hash
        Given a session where the root_hash has been replaced with a fake value
        When verify_merkle_dag() is called
        Then verified=False and root_hash_valid=False.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, _, _, _ = _make_session_data_with_merkle()

        # Replace the root hash with garbage
        session_data["merkle_dag"]["root_hash"] = "deadbeef" * 8

        result = manager.verify_merkle_dag(session_data)

        assert result["verified"] is False
        assert result["root_hash_valid"] is False

    @pytest.mark.unit
    def test_verify_merkle_dag_no_root_hash(self, tmp_path: Path) -> None:
        """Scenario: Session has nodes but no root hash stored
        Given nodes are present but root_hash is None or absent
        When verify_merkle_dag() is called
        Then nodes are still verified and root_hash_valid=True (nothing to check).
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, _, _, _ = _make_session_data_with_merkle()
        session_data["merkle_dag"]["root_hash"] = None

        result = manager.verify_merkle_dag(session_data)

        # Content/metadata hashes should still pass; root is vacuously valid
        assert result["root_hash_valid"] is True
        assert result["nodes"][0]["content_hash_valid"] is True

    @pytest.mark.unit
    def test_verify_merkle_dag_sealed_nodes_skip_metadata(self, tmp_path: Path) -> None:
        """Scenario: Verify sealed session where expert identity is masked
        Given a session node where expert_role and expert_model are '[SEALED]'
        When verify_merkle_dag() is called
        Then the node is reported as sealed and not failed on metadata.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, node_id, _, _ = _make_session_data_with_merkle()

        node = session_data["merkle_dag"]["nodes"][node_id]
        node["expert_role"] = "[SEALED]"
        node["expert_model"] = "[SEALED]"

        result = manager.verify_merkle_dag(session_data)

        node_result = result["nodes"][0]
        assert node_result["sealed"] is True
        # Content hash is still verifiable
        assert node_result["content_hash_valid"] is True
        # metadata and combined are skipped (trusted)
        assert node_result["metadata_hash_valid"] is True
        assert node_result["combined_hash_valid"] is True

    # -----------------------------------------------------------------------
    # generate_audit_report
    # -----------------------------------------------------------------------

    @pytest.mark.unit
    def test_generate_audit_report_basic_fields(self, tmp_path: Path) -> None:
        """Scenario: Generate an audit report from session data
        Given a completed session with standard artifacts
        When generate_audit_report() is called
        Then the report captures session metadata correctly.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()

        report = manager.generate_audit_report(session_data)

        assert report.session_id == "sess-001"
        assert report.problem_statement == "Should we refactor the auth module?"
        assert report.mode == "lightweight"
        assert report.status == "completed"
        assert report.phases_completed == [
            "intel",
            "assessment",
            "coa",
            "voting",
            "synthesis",
        ]

    @pytest.mark.unit
    def test_generate_audit_report_duration_calculation(self, tmp_path: Path) -> None:
        """Scenario: Duration is calculated from metrics start/end times
        Given a session with start_time and end_time 5 minutes apart
        When generate_audit_report() is called
        Then duration_seconds equals 300.0.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()

        report = manager.generate_audit_report(session_data)

        assert report.duration_seconds == 300.0

    @pytest.mark.unit
    def test_generate_audit_report_expert_panel(self, tmp_path: Path) -> None:
        """Scenario: Expert panel is extracted from COA artifacts
        Given a session with two experts in raw_coas
        When generate_audit_report() is called
        Then expert_panel contains those expert keys.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()

        report = manager.generate_audit_report(session_data)

        assert set(report.expert_panel) == {"chief_strategist", "field_tactician"}

    @pytest.mark.unit
    def test_generate_audit_report_voting_summary(self, tmp_path: Path) -> None:
        """Scenario: Voting summary is extracted from voting artifact
        Given a session with borda_scores and finalists
        When generate_audit_report() is called
        Then voting_summary contains borda_scores, finalists, and unanimity.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()

        report = manager.generate_audit_report(session_data)

        assert report.voting_summary["borda_scores"] == {
            "Response A": 10,
            "Response B": 6,
        }
        assert report.voting_summary["finalists"] == ["Response A"]
        assert "unanimity" in report.voting_summary

    @pytest.mark.unit
    def test_generate_audit_report_with_escalation(self, tmp_path: Path) -> None:
        """Scenario: Escalation history captured when session was escalated
        Given a session where escalated=True with a reason
        When generate_audit_report() is called
        Then escalation_history contains one entry with the reason.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        session_data["escalated"] = True
        session_data["escalation_reason"] = "Insufficient COA diversity"

        report = manager.generate_audit_report(session_data)

        assert len(report.escalation_history) == 1
        assert report.escalation_history[0]["escalated"] is True
        assert report.escalation_history[0]["reason"] == "Insufficient COA diversity"

    @pytest.mark.unit
    def test_generate_audit_report_no_escalation(self, tmp_path: Path) -> None:
        """Scenario: No escalation history when session was not escalated
        Given a session where escalated=False
        When generate_audit_report() is called
        Then escalation_history is empty.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        session_data["escalated"] = False

        report = manager.generate_audit_report(session_data)

        assert report.escalation_history == []

    @pytest.mark.unit
    def test_generate_audit_report_final_decision(self, tmp_path: Path) -> None:
        """Scenario: Final decision is extracted from synthesis artifact
        Given a session with a synthesis.decision value
        When generate_audit_report() is called
        Then final_decision matches the stored synthesis decision.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()

        report = manager.generate_audit_report(session_data)

        assert report.final_decision == "Adopt OAuth2 with PKCE immediately"
        assert (
            report.decision_rationale == "Best security posture with low migration cost"
        )

    @pytest.mark.unit
    def test_generate_audit_report_includes_checkpoints(self, tmp_path: Path) -> None:
        """Scenario: Logged checkpoints appear in the audit report
        Given two checkpoints logged for a session
        When generate_audit_report() is called for that session
        Then the report's checkpoints list contains both entries.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data(session_id="sess-cp")

        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-cp", checkpoint_id="cp-1")
        )
        manager.log_checkpoint(
            _make_checkpoint(session_id="sess-cp", checkpoint_id="cp-2")
        )

        report = manager.generate_audit_report(session_data)

        assert len(report.checkpoints) == 2
        cp_ids = {c["checkpoint_id"] for c in report.checkpoints}
        assert cp_ids == {"cp-1", "cp-2"}

    @pytest.mark.unit
    def test_generate_audit_report_merkle_verification_present(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Merkle verification is embedded in the report
        Given a valid session with merkle_dag data
        When generate_audit_report() is called
        Then merkle_verification contains a 'verified' key.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data, _, _, _ = _make_session_data_with_merkle()

        report = manager.generate_audit_report(session_data)

        assert "verified" in report.merkle_verification
        assert report.merkle_verification["verified"] is True

    @pytest.mark.unit
    def test_generate_audit_report_bad_timestamps_yield_zero_duration(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Graceful handling of missing or malformed timestamps
        Given a session with missing start_time and end_time in metrics
        When generate_audit_report() is called
        Then duration_seconds is 0.0 without raising.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        session_data["metrics"] = {}

        report = manager.generate_audit_report(session_data)

        assert report.duration_seconds == 0.0

    # -----------------------------------------------------------------------
    # save_audit_report / list_audited_sessions
    # -----------------------------------------------------------------------

    @pytest.mark.unit
    def test_save_audit_report_creates_file(self, tmp_path: Path) -> None:
        """Scenario: Save an audit report to disk
        Given a generated AuditReport
        When save_audit_report() is called
        Then audit-report.json appears in the session directory.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        report = manager.generate_audit_report(session_data)

        filepath = manager.save_audit_report(report)

        assert filepath.exists()
        assert filepath.name == AUDIT_REPORT_FILENAME
        # Must be inside war-table/{session_id}/
        assert "war-table" in str(filepath)
        assert "sess-001" in str(filepath)

    @pytest.mark.unit
    def test_save_audit_report_is_valid_json(self, tmp_path: Path) -> None:
        """Scenario: Saved audit report can be parsed as JSON
        Given a saved audit report file
        When the file is read and parsed
        Then it contains the expected session_id.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        report = manager.generate_audit_report(session_data)
        filepath = manager.save_audit_report(report)

        data = json.loads(filepath.read_text())
        assert data["session_id"] == "sess-001"
        assert data["status"] == "completed"

    @pytest.mark.unit
    def test_list_audited_sessions_empty(self, tmp_path: Path) -> None:
        """Scenario: No audit reports exist
        Given an empty strategeion directory
        When list_audited_sessions() is called
        Then an empty list is returned.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        result = manager.list_audited_sessions()
        assert result == []

    @pytest.mark.unit
    def test_list_audited_sessions_discovery(self, tmp_path: Path) -> None:
        """Scenario: Discover multiple saved audit reports
        Given two sessions each with a saved audit report
        When list_audited_sessions() is called
        Then both sessions are returned with summary metadata.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)

        for sid in ("sess-001", "sess-002"):
            data = _make_session_data(session_id=sid)
            report = manager.generate_audit_report(data)
            manager.save_audit_report(report)

        results = manager.list_audited_sessions()

        assert len(results) == 2
        session_ids = {r["session_id"] for r in results}
        assert session_ids == {"sess-001", "sess-002"}

    @pytest.mark.unit
    def test_list_audited_sessions_summary_fields(self, tmp_path: Path) -> None:
        """Scenario: Listed sessions carry required summary fields
        Given a saved audit report
        When list_audited_sessions() is called
        Then each entry has session_id, generated_at, problem_statement,
             status, and merkle_verified.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        session_data = _make_session_data()
        report = manager.generate_audit_report(session_data)
        manager.save_audit_report(report)

        results = manager.list_audited_sessions()
        entry = results[0]

        assert "session_id" in entry
        assert "generated_at" in entry
        assert "problem_statement" in entry
        assert "status" in entry
        assert "merkle_verified" in entry

    # -----------------------------------------------------------------------
    # _calculate_unanimity
    # -----------------------------------------------------------------------

    @pytest.mark.unit
    def test_calculate_unanimity_clear_winner(self, tmp_path: Path) -> None:
        """Scenario: Clear winner in voting
        Given borda_scores {"A": 10, "B": 2}
        When _calculate_unanimity() is called
        Then the score reflects the wide gap.
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        score = manager._calculate_unanimity({"borda_scores": {"A": 10, "B": 2}})
        assert 0.0 < score <= 1.0
        # gap=8, total=12 → 8/12 ≈ 0.667
        assert abs(score - 8 / 12) < 1e-9

    @pytest.mark.unit
    def test_calculate_unanimity_equal_scores(self, tmp_path: Path) -> None:
        """Scenario: Tied vote
        Given borda_scores {"A": 5, "B": 5}
        When _calculate_unanimity() is called
        Then score is 0.0 (no gap).
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        score = manager._calculate_unanimity({"borda_scores": {"A": 5, "B": 5}})
        assert score == 0.0

    @pytest.mark.unit
    def test_calculate_unanimity_single_option(self, tmp_path: Path) -> None:
        """Scenario: Only one COA option
        Given borda_scores {"A": 7}
        When _calculate_unanimity() is called
        Then score is 1.0 (trivially unanimous).
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        score = manager._calculate_unanimity({"borda_scores": {"A": 7}})
        assert score == 1.0

    @pytest.mark.unit
    def test_calculate_unanimity_empty_scores(self, tmp_path: Path) -> None:
        """Scenario: No voting data
        Given an empty borda_scores dict
        When _calculate_unanimity() is called
        Then score is 1.0 (vacuously unanimous).
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        score = manager._calculate_unanimity({"borda_scores": {}})
        assert score == 1.0

    @pytest.mark.unit
    def test_calculate_unanimity_all_zero_scores(self, tmp_path: Path) -> None:
        """Scenario: All scores are zero (no votes cast)
        Given borda_scores {"A": 0, "B": 0}
        When _calculate_unanimity() is called
        Then score is 1.0 (no meaningful distinction).
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        score = manager._calculate_unanimity({"borda_scores": {"A": 0, "B": 0}})
        assert score == 1.0

    @pytest.mark.unit
    def test_calculate_unanimity_capped_at_one(self, tmp_path: Path) -> None:
        """Scenario: Unanimity score never exceeds 1.0
        Given any borda_scores combination
        When _calculate_unanimity() is called
        Then the returned value is always in [0.0, 1.0].
        """
        manager = AuditTrailManager(strategeion_dir=tmp_path)
        for scores in [
            {"A": 100, "B": 0},
            {"A": 1, "B": 0},
            {"A": 5, "B": 3, "C": 1},
        ]:
            s = manager._calculate_unanimity({"borda_scores": scores})
            assert 0.0 <= s <= 1.0, f"score {s} out of range for {scores}"
