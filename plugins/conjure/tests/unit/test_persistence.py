"""BDD tests for War Room persistence audit trail integration.

Feature: Audit Report Auto-generation on Session Persistence
  As a War Room operator
  I want an audit report generated automatically every time a session is saved
  So that every completed session has an immutable integrity record without
  requiring a separate manual step
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.war_room.audit_trail import AUDIT_REPORT_FILENAME
from scripts.war_room.models import ExpertInfo, WarRoomSession
from scripts.war_room.persistence import persist_session

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_session(session_id: str = "audit-persist-test") -> WarRoomSession:
    """Return a minimal completed WarRoomSession."""
    session = WarRoomSession(
        session_id=session_id,
        problem_statement="Test problem for audit persistence",
        mode="lightweight",
        status="completed",
    )
    session.phases_completed = ["intel", "coa"]
    session.artifacts = {
        "intel": {"scout_report": "Scout findings"},
        "coa": {
            "raw_coas": {"chief_strategist": "Strategy A"},
            "count": 1,
        },
        "synthesis": {
            "decision": "Proceed with Strategy A",
            "rationale": "Lowest risk path",
            "attribution_revealed": True,
        },
    }
    session.metrics = {
        "start_time": "2026-03-03T10:00:00+00:00",
        "end_time": "2026-03-03T10:03:00+00:00",
    }
    return session


# ===========================================================================
# TestPersistSessionAuditIntegration
# ===========================================================================


class TestPersistSessionAuditIntegration:
    """Feature: persist_session() generates an audit report as a side-effect.

    As a War Room operator
    I want the audit report written automatically on every persist_session() call
    So that no session can be saved without an accompanying integrity record
    """

    @pytest.mark.unit
    def test_persist_session_creates_audit_report_file(self, tmp_path: Path) -> None:
        """Scenario: Audit report file created alongside session.json
        Given a WarRoomSession and a temp strategeion directory
        When persist_session() is called
        Then audit-report.json appears in the session directory.
        """
        session = _minimal_session()

        persist_session(tmp_path, session)

        audit_file = tmp_path / "war-table" / session.session_id / AUDIT_REPORT_FILENAME
        assert audit_file.exists(), (
            f"Expected audit report at {audit_file} but it was not created"
        )

    @pytest.mark.unit
    def test_persist_session_audit_report_is_valid_json(self, tmp_path: Path) -> None:
        """Scenario: Audit report file contains parseable JSON
        Given a persisted session
        When the audit-report.json file is read
        Then it parses without error and contains the correct session_id.
        """
        session = _minimal_session(session_id="audit-json-test")

        persist_session(tmp_path, session)

        audit_file = tmp_path / "war-table" / session.session_id / AUDIT_REPORT_FILENAME
        data = json.loads(audit_file.read_text())
        assert data["session_id"] == "audit-json-test"
        assert data["status"] == "completed"

    @pytest.mark.unit
    def test_persist_session_audit_report_merkle_verification_present(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Audit report includes Merkle-DAG verification block
        Given a session with Merkle-DAG contributions
        When persist_session() is called
        Then the audit report contains a 'merkle_verification' key with a
             'verified' field.
        """
        session = _minimal_session(session_id="audit-merkle-test")
        session.merkle_dag.add_contribution(
            content="COA content for merkle",
            phase="coa",
            round_number=1,
            expert=ExpertInfo(role="Chief Strategist", model="claude-sonnet-4"),
        )

        persist_session(tmp_path, session)

        audit_file = tmp_path / "war-table" / session.session_id / AUDIT_REPORT_FILENAME
        data = json.loads(audit_file.read_text())
        assert "merkle_verification" in data
        assert "verified" in data["merkle_verification"]

    @pytest.mark.unit
    def test_persist_session_audit_report_does_not_break_session_json(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Existing session.json is unaffected by audit report generation
        Given persist_session() now also writes an audit report
        When the session directory is inspected
        Then session.json still exists with correct content.
        """
        session = _minimal_session(session_id="audit-coexist-test")

        persist_session(tmp_path, session)

        session_file = tmp_path / "war-table" / session.session_id / "session.json"
        assert session_file.exists()
        data = json.loads(session_file.read_text())
        assert data["session_id"] == "audit-coexist-test"
        assert data["problem_statement"] == "Test problem for audit persistence"
