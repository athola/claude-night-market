"""Audit trail generation and verification for war room sessions.

Generates formal audit reports, implements checkpoint logging,
and provides Merkle-DAG integrity verification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT_DIR = "checkpoints"
AUDIT_REPORT_FILENAME = "audit-report.json"


@dataclass
class CheckpointEntry:
    """A single checkpoint event in the audit trail."""

    checkpoint_id: str
    timestamp: str  # ISO format
    session_id: str
    phase: str
    action: str  # "express" | "escalate" | "continue" | "halt"
    reversibility_score: float  # 0.0-1.0
    dimensions: dict[str, int] = field(default_factory=dict)  # RS dimensions
    decision_context: str = ""
    files_affected: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_user_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointEntry:
        """Deserialize from dictionary, ignoring unknown keys."""
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class AuditReport:
    """Complete audit report for a war room session."""

    session_id: str
    generated_at: str
    problem_statement: str
    mode: str
    status: str
    duration_seconds: float
    phases_completed: list[str] = field(default_factory=list)
    expert_panel: list[str] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    voting_summary: dict[str, Any] = field(default_factory=dict)
    dissenting_views: list[dict[str, Any]] = field(default_factory=list)
    escalation_history: list[dict[str, Any]] = field(default_factory=list)
    merkle_verification: dict[str, Any] = field(default_factory=dict)
    final_decision: str = ""
    decision_rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)


class AuditTrailManager:
    """Manages audit trails for war room sessions."""

    def __init__(self, strategeion_dir: Path | None = None) -> None:
        """Initialize manager with strategeion directory."""
        if strategeion_dir is None:
            home = Path.home()
            strategeion_dir = home / ".claude" / "memory-palace" / "strategeion"
        self.strategeion_dir = strategeion_dir
        self.checkpoints_dir = strategeion_dir / CHECKPOINT_DIR

    def _ensure_dirs(self, *paths: Path) -> None:
        """Create directories if they do not exist."""
        for p in paths:
            p.mkdir(parents=True, exist_ok=True)

    def log_checkpoint(self, entry: CheckpointEntry) -> Path:
        """Log a checkpoint event to the audit trail.

        Writes to checkpoints/{YYYY-MM-DD}/{checkpoint_id}.json inside
        the strategeion directory.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        date_dir = self.checkpoints_dir / date_str
        self._ensure_dirs(date_dir)

        filepath = date_dir / f"{entry.checkpoint_id}.json"
        filepath.write_text(json.dumps(entry.to_dict(), indent=2))
        return filepath

    def get_checkpoints(self, session_id: str) -> list[CheckpointEntry]:
        """Retrieve all checkpoints for a session, sorted chronologically."""
        results: list[CheckpointEntry] = []
        if not self.checkpoints_dir.exists():
            return results

        for date_dir in sorted(self.checkpoints_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            for checkpoint_file in sorted(date_dir.glob("*.json")):
                try:
                    data = json.loads(checkpoint_file.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                if data.get("session_id") == session_id:
                    results.append(CheckpointEntry.from_dict(data))

        return results

    def verify_merkle_dag(self, session_data: dict[str, Any]) -> dict[str, Any]:
        """Verify Merkle-DAG integrity for a session.

        Recomputes all node hashes using the same scheme that
        MerkleDAG.add_contribution() uses:

            content_hash  = sha256(content)
            metadata_hash = sha256("{expert_role}:{expert_model}")
            combined_hash = sha256("{content_hash}:{metadata_hash}")

        Root hash is verified with the same algorithm as
        MerkleDAG._update_root_hash():

            root_hash = sha256(":".join(sorted(combined_hashes)))

        Nodes serialised in sealed state have expert fields replaced with
        "[SEALED]". Those nodes skip metadata/combined recomputation but
        still verify the content hash.
        """
        merkle_dag = session_data.get("merkle_dag", {})
        nodes_raw = merkle_dag.get("nodes", {})

        # Nodes may be stored as a dict keyed by node_id or as a list
        if isinstance(nodes_raw, dict):
            nodes = list(nodes_raw.values())
        else:
            nodes = list(nodes_raw)

        if not nodes:
            return {
                "verified": True,
                "node_count": 0,
                "message": "No Merkle-DAG nodes to verify",
            }

        verification_results = []
        all_valid = True
        stored_combined_hashes: list[str] = []

        for node in nodes:
            content = node.get("content", "")
            expert_role = node.get("expert_role", "")
            expert_model = node.get("expert_model", "")

            stored_content_hash = node.get("content_hash", "")
            stored_metadata_hash = node.get("metadata_hash", "")
            stored_combined_hash = node.get("combined_hash", "")

            sealed = expert_role == "[SEALED]" or expert_model == "[SEALED]"

            # Content hash is always recomputable
            computed_content_hash = sha256(content.encode()).hexdigest()
            content_valid = computed_content_hash == stored_content_hash

            if sealed:
                # Cannot recompute metadata when attribution is masked;
                # trust the stored metadata hash for sealed nodes
                metadata_valid = True
                # But we CAN verify combined = sha256(content_hash:stored_metadata_hash)
                computed_combined = sha256(
                    f"{computed_content_hash}:{stored_metadata_hash}".encode()
                ).hexdigest()
                combined_valid = computed_combined == stored_combined_hash
            else:
                computed_metadata_hash = sha256(
                    f"{expert_role}:{expert_model}".encode()
                ).hexdigest()
                computed_combined = sha256(
                    f"{computed_content_hash}:{computed_metadata_hash}".encode()
                ).hexdigest()
                metadata_valid = computed_metadata_hash == stored_metadata_hash
                combined_valid = computed_combined == stored_combined_hash

            node_valid = content_valid and metadata_valid and combined_valid
            if not node_valid:
                all_valid = False

            stored_combined_hashes.append(stored_combined_hash)
            verification_results.append(
                {
                    "node_id": node.get("node_id", "unknown"),
                    "valid": node_valid,
                    "content_hash_valid": content_valid,
                    "metadata_hash_valid": metadata_valid,
                    "combined_hash_valid": combined_valid,
                    "sealed": sealed,
                }
            )

        # Verify root hash using MerkleDAG._update_root_hash() algorithm:
        # sha256(":".join(sorted(combined_hashes)))
        stored_root = merkle_dag.get("root_hash") or ""
        root_valid = True
        if stored_root:
            combined_str = ":".join(sorted(stored_combined_hashes))
            computed_root = sha256(combined_str.encode()).hexdigest()
            root_valid = computed_root == stored_root
            if not root_valid:
                all_valid = False

        return {
            "verified": all_valid,
            "node_count": len(nodes),
            "nodes": verification_results,
            "root_hash_valid": root_valid,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_audit_report(self, session_data: dict[str, Any]) -> AuditReport:
        """Generate a complete audit report from session data dict.

        The session_data format matches what persistence.py writes to
        session.json (the session_data local variable there).
        """
        session_id = session_data.get("session_id", "unknown")
        artifacts = session_data.get("artifacts", {})
        metrics = session_data.get("metrics", {})

        # Voting summary
        voting = artifacts.get("voting", {})
        voting_summary: dict[str, Any] = {}
        if voting:
            voting_summary = {
                "borda_scores": voting.get("borda_scores", {}),
                "finalists": voting.get("finalists", []),
                "unanimity": self._calculate_unanimity(voting),
            }

        # Dissenting views from synthesis artifact
        synthesis = artifacts.get("synthesis", {})
        dissenting_views: list[dict[str, Any]] = []
        if isinstance(synthesis, dict):
            dissent = synthesis.get("dissenting_views", [])
            if isinstance(dissent, list):
                dissenting_views = dissent

        # Expert panel from COA raw_coas keys
        coa = artifacts.get("coa", {})
        expert_panel: list[str] = []
        if isinstance(coa, dict):
            raw_coas = coa.get("raw_coas", {})
            if isinstance(raw_coas, dict):
                expert_panel = list(raw_coas.keys())

        # Escalation history
        escalation_history: list[dict[str, Any]] = []
        if session_data.get("escalated"):
            escalation_history.append(
                {
                    "escalated": True,
                    "reason": session_data.get("escalation_reason", ""),
                }
            )

        # Merkle-DAG integrity verification
        merkle_verification = self.verify_merkle_dag(session_data)

        # Checkpoints logged for this session
        checkpoints = self.get_checkpoints(session_id)

        # Duration from metrics timestamps
        start = metrics.get("start_time", "")
        end = metrics.get("end_time", "")
        duration = 0.0
        if start and end:
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                duration = (end_dt - start_dt).total_seconds()
            except (ValueError, TypeError):
                pass

        # Final decision and rationale from synthesis
        final_decision = ""
        decision_rationale = ""
        if isinstance(synthesis, dict):
            final_decision = synthesis.get("decision", "")
            decision_rationale = synthesis.get("rationale", "")

        return AuditReport(
            session_id=session_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            problem_statement=session_data.get("problem_statement", ""),
            mode=session_data.get("mode", ""),
            status=session_data.get("status", ""),
            duration_seconds=duration,
            phases_completed=session_data.get("phases_completed", []),
            expert_panel=expert_panel,
            checkpoints=[c.to_dict() for c in checkpoints],
            voting_summary=voting_summary,
            dissenting_views=dissenting_views,
            escalation_history=escalation_history,
            merkle_verification=merkle_verification,
            final_decision=final_decision,
            decision_rationale=decision_rationale,
        )

    def save_audit_report(self, report: AuditReport) -> Path:
        """Save an audit report to the session directory.

        Writes to war-table/{session_id}/audit-report.json.
        """
        session_dir = self.strategeion_dir / "war-table" / report.session_id
        self._ensure_dirs(session_dir)

        filepath = session_dir / AUDIT_REPORT_FILENAME
        filepath.write_text(json.dumps(report.to_dict(), indent=2))
        return filepath

    def _calculate_unanimity(self, voting_data: dict[str, Any]) -> float:
        """Calculate voting unanimity score in the range 0.0-1.0.

        Returns the normalised gap between the top Borda score and the
        runner-up.  Returns 1.0 when there is only one option or all
        scores sum to zero (no votes cast).
        """
        scores = voting_data.get("borda_scores", {})
        if not scores or len(scores) < 2:
            return 1.0

        values = sorted(scores.values(), reverse=True)
        top = values[0]
        second = values[1]
        total = sum(values)

        if total == 0:
            return 1.0

        return float(min(1.0, (top - second) / total))

    def list_audited_sessions(self) -> list[dict[str, Any]]:
        """Return summary dicts for all sessions that have saved audit reports."""
        war_table = self.strategeion_dir / "war-table"
        if not war_table.exists():
            return []

        results = []
        for session_dir in sorted(war_table.iterdir()):
            if not session_dir.is_dir():
                continue
            audit_file = session_dir / AUDIT_REPORT_FILENAME
            if not audit_file.exists():
                continue
            try:
                data = json.loads(audit_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            results.append(
                {
                    "session_id": data.get("session_id"),
                    "generated_at": data.get("generated_at"),
                    "problem_statement": data.get("problem_statement", "")[:100],
                    "status": data.get("status"),
                    "merkle_verified": data.get("merkle_verification", {}).get(
                        "verified", False
                    ),
                }
            )

        return results
