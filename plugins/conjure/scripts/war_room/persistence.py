"""Strategeion persistence for War Room sessions.

Save, load, archive, and list War Room sessions.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.war_room.models import DeliberationNode, MerkleDAG, WarRoomSession


def persist_session(strategeion: Path, session: WarRoomSession) -> None:
    """Save session to Strategeion with organized subdirectories."""
    session_dir = strategeion / "war-table" / session.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories per Strategeion architecture
    intel_dir = session_dir / "intelligence"
    plans_dir = session_dir / "battle-plans"
    wargames_dir = session_dir / "wargames"
    orders_dir = session_dir / "orders"

    for d in [intel_dir, plans_dir, wargames_dir, orders_dir]:
        d.mkdir(exist_ok=True)

    # Save intelligence reports
    intel = session.artifacts.get("intel", {})
    if intel.get("scout_report"):
        (intel_dir / "scout-report.md").write_text(
            f"# Scout Report\n\n{intel['scout_report']}"
        )
    if intel.get("intel_report") and "[Intel Officer not invoked" not in str(
        intel.get("intel_report", "")
    ):
        (intel_dir / "intel-officer-report.md").write_text(
            f"# Intelligence Officer Report\n\n{intel['intel_report']}"
        )

    # Save assessment
    assessment = session.artifacts.get("assessment", {}).get("content")
    if assessment:
        (intel_dir / "situation-assessment.md").write_text(
            f"# Situation Assessment\n\n{assessment}"
        )

    # Save COAs (battle plans)
    coas = session.artifacts.get("coa", {}).get("raw_coas", {})
    for expert, coa_content in coas.items():
        (plans_dir / f"coa-{expert}.md").write_text(
            f"# Course of Action: {expert}\n\n{coa_content}"
        )

    # Save Red Team challenges and Premortem (wargames)
    red_team = session.artifacts.get("red_team", {}).get("challenges")
    if red_team:
        (wargames_dir / "red-team-challenges.md").write_text(
            f"# Red Team Challenges\n\n{red_team}"
        )

    premortem = session.artifacts.get("premortem", {}).get("analyses", {})
    if premortem:
        premortem_content = "\n\n---\n\n".join(
            f"## {expert}\n\n{analysis}" for expert, analysis in premortem.items()
        )
        (wargames_dir / "premortem-analyses.md").write_text(
            f"# Premortem Analyses\n\n{premortem_content}"
        )

    # Save final decision (orders)
    synthesis = session.artifacts.get("synthesis", {}).get("decision")
    if synthesis:
        (orders_dir / "supreme-commander-decision.md").write_text(synthesis)

    # Save main session file (includes all data for reconstruction)
    session_data = {
        "session_id": session.session_id,
        "problem_statement": session.problem_statement,
        "mode": session.mode,
        "status": session.status,
        "escalated": session.escalated,
        "escalation_reason": session.escalation_reason,
        "phases_completed": session.phases_completed,
        "artifacts": session.artifacts,
        "metrics": session.metrics,
        "merkle_dag": session.merkle_dag.to_dict(),
    }

    with open(session_dir / "session.json", "w") as f:
        json.dump(session_data, f, indent=2)


def load_session(strategeion: Path, session_id: str) -> WarRoomSession | None:
    """Load session from Strategeion."""
    session_file = strategeion / "war-table" / session_id / "session.json"
    if not session_file.exists():
        return None

    with open(session_file) as f:
        data = json.load(f)

    # Reconstruct session
    session = WarRoomSession(
        session_id=data["session_id"],
        problem_statement=data["problem_statement"],
        mode=data["mode"],
        status=data["status"],
        escalated=data.get("escalated", False),
        escalation_reason=data.get("escalation_reason"),
        phases_completed=data["phases_completed"],
        artifacts=data["artifacts"],
        metrics=data["metrics"],
    )

    # Reconstruct MerkleDAG
    dag_data = data.get("merkle_dag", {})
    session.merkle_dag = MerkleDAG(session_id=dag_data.get("session_id", ""))
    session.merkle_dag.sealed = dag_data.get("sealed", True)
    session.merkle_dag.root_hash = dag_data.get("root_hash")
    session.merkle_dag.label_counter = dag_data.get("label_counter", {})

    # Reconstruct nodes
    for node_data in dag_data.get("nodes", {}).values():
        node = DeliberationNode(
            node_id=node_data["node_id"],
            parent_id=node_data.get("parent_id"),
            round_number=node_data["round_number"],
            phase=node_data["phase"],
            anonymous_label=node_data["anonymous_label"],
            content=node_data["content"],
            expert_role=node_data.get("expert_role", "[SEALED]"),
            expert_model=node_data.get("expert_model", "[SEALED]"),
            content_hash=node_data["content_hash"],
            metadata_hash=node_data["metadata_hash"],
            combined_hash=node_data["combined_hash"],
            timestamp=node_data["timestamp"],
        )
        session.merkle_dag.nodes[node.node_id] = node

    return session


def archive_session(
    strategeion: Path, session_id: str, project: str | None = None
) -> Path | None:
    """Archive completed session to campaign-archive."""
    session = load_session(strategeion, session_id)
    if not session or session.status != "completed":
        return None

    # Determine archive location
    project_name = project or "default"
    decision_date = datetime.now().strftime("%Y-%m-%d")
    archive_dir = strategeion / "campaign-archive" / project_name / decision_date
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Move session directory
    source = strategeion / "war-table" / session_id
    dest = archive_dir / session_id

    if source.exists():
        shutil.move(str(source), str(dest))
        return dest

    return None


def list_sessions(
    strategeion: Path, include_archived: bool = False
) -> list[dict[str, Any]]:
    """List all War Room sessions."""
    sessions: list[dict[str, Any]] = []

    # Active sessions
    war_table = strategeion / "war-table"
    if war_table.exists():
        for session_dir in war_table.iterdir():
            if session_dir.is_dir():
                session_file = session_dir / "session.json"
                if session_file.exists():
                    with open(session_file) as f:
                        data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data["session_id"],
                            "problem": data["problem_statement"][:100],
                            "status": data["status"],
                            "mode": data["mode"],
                            "archived": False,
                        }
                    )

    # Archived sessions
    if include_archived:
        archive = strategeion / "campaign-archive"
        if archive.exists():
            for project_dir in archive.iterdir():
                if project_dir.is_dir():
                    for date_dir in project_dir.iterdir():
                        if date_dir.is_dir():
                            for session_dir in date_dir.iterdir():
                                session_file = session_dir / "session.json"
                                if session_file.exists():
                                    with open(session_file) as f:
                                        data = json.load(f)
                                    sessions.append(
                                        {
                                            "session_id": data["session_id"],
                                            "problem": data["problem_statement"][:100],
                                            "status": data["status"],
                                            "mode": data["mode"],
                                            "archived": True,
                                            "project": project_dir.name,
                                        }
                                    )

    return sessions
