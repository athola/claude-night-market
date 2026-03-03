"""Phase implementations for War Room deliberation.

Contains _phase_intel, _phase_assessment, _phase_coa_development,
_phase_red_team, _phase_voting, _phase_premortem, _phase_synthesis,
plus escalation logic and Borda count scoring.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scripts.war_room.experts import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
)
from scripts.war_room.models import WarRoomSession
from scripts.war_room.prompts import (
    ASSESSMENT_PROMPT,
    COA_PROMPT,
    INTEL_PROMPT_OFFICER,
    INTEL_PROMPT_SCOUT,
    PREMORTEM_PROMPT,
    RED_TEAM_PROMPT,
    SYNTHESIS_PROMPT,
    VOTING_PROMPT,
)

if TYPE_CHECKING:
    from scripts.war_room.orchestrator import WarRoomOrchestrator


async def phase_intel(
    orch: WarRoomOrchestrator,
    session: WarRoomSession,
    context_files: list[str] | None,
) -> None:
    """Phase 1: Intelligence Gathering (Scout + Intel Officer in parallel)."""
    context_str = ", ".join(context_files) if context_files else "None provided"
    experts_to_invoke: list[str] = []
    prompts: dict[str, str] = {}

    # Scout always runs (fast, cheap)
    prompts["scout"] = INTEL_PROMPT_SCOUT.format(
        problem=session.problem_statement,
        context_files=context_str,
    )
    experts_to_invoke.append("scout")

    # Intel Officer only in full council mode
    if session.mode == "full_council":
        prompts["intelligence_officer"] = INTEL_PROMPT_OFFICER.format(
            problem=session.problem_statement,
            context_files=context_str,
        )
        experts_to_invoke.append("intelligence_officer")

    results = await orch._invoke_parallel(experts_to_invoke, prompts, session, "intel")

    session.artifacts["intel"] = {
        "scout_report": results.get("scout", "[Scout unavailable]"),
        "intel_report": results.get(
            "intelligence_officer", "[Intel Officer not invoked - lightweight mode]"
        ),
        "context_files": context_files,
    }
    session.phases_completed.append("intel")


async def phase_assessment(orch: WarRoomOrchestrator, session: WarRoomSession) -> None:
    """Phase 2: Situation Assessment (Chief Strategist)."""
    intel = session.artifacts.get("intel", {})

    prompt = ASSESSMENT_PROMPT.format(
        problem=session.problem_statement,
        scout_report=intel.get("scout_report", "N/A"),
        intel_report=intel.get("intel_report", "N/A"),
    )

    # Chief Strategist is native (Sonnet) - invoke directly
    result = await orch._invoke_expert(
        "chief_strategist", prompt, session, "assessment"
    )

    session.artifacts["assessment"] = {
        "content": result,
    }
    session.phases_completed.append("assessment")


async def phase_coa_development(
    orch: WarRoomOrchestrator, session: WarRoomSession
) -> None:
    """Phase 3: COA Development (parallel, anonymized)."""
    assessment = session.artifacts.get("assessment", {}).get("content", "N/A")

    experts_to_invoke = ["chief_strategist"]  # Always includes strategist
    if session.mode == "full_council":
        experts_to_invoke.extend(["field_tactician", "logistics_officer"])

    expertise_map = {
        "chief_strategist": "Strategic architecture and long-term viability",
        "field_tactician": "Implementation feasibility and technical complexity",
        "logistics_officer": "Resource requirements and dependency management",
    }

    prompts: dict[str, str] = {}
    for expert_key in experts_to_invoke:
        expert = EXPERT_CONFIGS.get(expert_key)
        if expert:
            prompts[expert_key] = COA_PROMPT.format(
                role=expert.role,
                problem=session.problem_statement,
                assessment=assessment,
                expertise=expertise_map.get(expert_key, "General analysis"),
            )

    results = await orch._invoke_parallel(experts_to_invoke, prompts, session, "coa")

    # Store raw COAs (with attribution sealed in Merkle-DAG)
    session.artifacts["coa"] = {
        "raw_coas": results,
        "count": len(results),
    }
    session.phases_completed.append("coa")


async def should_escalate(session: WarRoomSession) -> bool:
    """Check if Supreme Commander should escalate to full council.

    Escalation triggers:
    1. COA count < 2 (need more perspectives)
    2. Keywords indicating complexity in assessment
    3. High disagreement detected (placeholder for future)
    """
    coa_count = session.artifacts.get("coa", {}).get("count", 0)
    if coa_count < 2:
        session.escalation_reason = "Insufficient COA diversity"
        return True

    assessment = session.artifacts.get("assessment", {}).get("content", "")
    complexity_keywords = [
        "complex",
        "trade-off",
        "significant risk",
        "irreversible",
        "architectural",
        "migration",
        "breaking change",
        "high stakes",
    ]
    assessment_lower = assessment.lower()
    complexity_hits = sum(1 for kw in complexity_keywords if kw in assessment_lower)
    if complexity_hits >= 3:
        session.escalation_reason = (
            f"High complexity detected ({complexity_hits} indicators)"
        )
        return True

    return False


async def escalate(
    orch: WarRoomOrchestrator,
    session: WarRoomSession,
    context_files: list[str] | None,
) -> None:
    """Escalate to full council by invoking additional experts."""
    session.mode = "full_council"

    # Invoke additional intel if not already done
    if "intel_report" not in session.artifacts.get("intel", {}):
        context_str = ", ".join(context_files) if context_files else "None"
        prompt = INTEL_PROMPT_OFFICER.format(
            problem=session.problem_statement,
            context_files=context_str,
        )
        result = await orch._invoke_expert(
            "intelligence_officer", prompt, session, "intel"
        )
        session.artifacts["intel"]["intel_report"] = result

    # Get additional COAs from new experts
    assessment = session.artifacts.get("assessment", {}).get("content", "N/A")
    additional_experts = ["field_tactician", "logistics_officer"]

    expertise_map = {
        "field_tactician": "Implementation feasibility and technical complexity",
        "logistics_officer": "Resource requirements and dependency management",
    }

    prompts: dict[str, str] = {}
    for expert_key in additional_experts:
        expert = EXPERT_CONFIGS.get(expert_key)
        if expert:
            prompts[expert_key] = COA_PROMPT.format(
                role=expert.role,
                problem=session.problem_statement,
                assessment=assessment,
                expertise=expertise_map.get(expert_key, "General analysis"),
            )

    results = await orch._invoke_parallel(additional_experts, prompts, session, "coa")

    # Merge with existing COAs
    existing_coas = session.artifacts.get("coa", {}).get("raw_coas", {})
    existing_coas.update(results)
    session.artifacts["coa"]["raw_coas"] = existing_coas
    session.artifacts["coa"]["count"] = len(existing_coas)
    session.artifacts["coa"]["escalated"] = True


async def phase_red_team(orch: WarRoomOrchestrator, session: WarRoomSession) -> None:
    """Phase 4: Red Team Challenge."""
    # Get anonymized view of COAs
    anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
    coas_text = "\n\n---\n\n".join(
        f"### {coa['label']}\n{coa['content']}" for coa in anonymized_coas
    )

    prompt = RED_TEAM_PROMPT.format(
        problem=session.problem_statement,
        anonymized_coas=coas_text,
    )

    result = await orch._invoke_expert("red_team", prompt, session, "red_team")

    session.artifacts["red_team"] = {
        "challenges": result,
        "coas_reviewed": len(anonymized_coas),
    }
    session.phases_completed.append("red_team")


async def phase_voting(orch: WarRoomOrchestrator, session: WarRoomSession) -> None:
    """Phase 5: Voting and Narrowing using Borda count."""
    # Prepare COAs with Red Team challenges
    anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
    challenges = session.artifacts.get("red_team", {}).get("challenges", "N/A")

    coas_with_challenges = "\n\n".join(
        f"### {coa['label']}\n{coa['content']}" for coa in anonymized_coas
    )
    coas_with_challenges += f"\n\n## RED TEAM CHALLENGES\n{challenges}"

    # Get active panel for voting
    panel = FULL_COUNCIL if session.mode == "full_council" else LIGHTWEIGHT_PANEL
    voting_experts = [e for e in panel if e != "supreme_commander"]

    prompts: dict[str, str] = {}
    for expert_key in voting_experts:
        expert = EXPERT_CONFIGS.get(expert_key)
        if expert:
            prompts[expert_key] = VOTING_PROMPT.format(
                role=expert.role,
                problem=session.problem_statement,
                coas_with_challenges=coas_with_challenges,
            )

    results = await orch._invoke_parallel(voting_experts, prompts, session, "voting")

    # Parse votes and compute Borda count
    coa_labels = [coa["label"] for coa in anonymized_coas]
    borda_scores = compute_borda_scores(results, coa_labels)

    # Select top 2-3 finalists
    sorted_coas = sorted(borda_scores.items(), key=lambda x: x[1], reverse=True)
    finalists = [label for label, _ in sorted_coas[: min(3, len(sorted_coas))]]

    session.artifacts["voting"] = {
        "raw_votes": results,
        "borda_scores": borda_scores,
        "finalists": finalists,
    }
    session.phases_completed.append("voting")


def compute_borda_scores(
    votes: dict[str, str], coa_labels: list[str]
) -> dict[str, int]:
    """Compute Borda count scores from expert votes.

    Borda count: N points for 1st, N-1 for 2nd, etc.
    """
    scores: dict[str, int] = dict.fromkeys(coa_labels, 0)
    n = len(coa_labels)

    for vote_text in votes.values():
        # Simple parsing: look for numbered list with COA labels
        for label in coa_labels:
            # Check if this label appears with a rank number
            for rank in range(1, n + 1):
                if f"{rank}." in vote_text and label in vote_text:
                    # Approximate: give points based on where label appears
                    pos = vote_text.find(label)
                    rank_pos = vote_text.find(f"{rank}.")
                    if 0 <= rank_pos < pos < rank_pos + 200:
                        scores[label] += n - rank + 1
                        break

    return scores


async def phase_premortem(orch: WarRoomOrchestrator, session: WarRoomSession) -> None:
    """Phase 6: Premortem Analysis on top finalist."""
    finalists = session.artifacts.get("voting", {}).get("finalists", [])
    if not finalists:
        session.artifacts["premortem"] = {"error": "No finalists to analyze"}
        session.phases_completed.append("premortem")
        return

    # Get the top COA content
    top_label = finalists[0]
    anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
    selected_coa = next(
        (c["content"] for c in anonymized_coas if c["label"] == top_label),
        "N/A",
    )

    # All active experts do premortem
    panel = FULL_COUNCIL if session.mode == "full_council" else LIGHTWEIGHT_PANEL
    premortem_experts = [e for e in panel if e != "supreme_commander"]

    prompts: dict[str, str] = {}
    for expert_key in premortem_experts:
        expert = EXPERT_CONFIGS.get(expert_key)
        if expert:
            prompts[expert_key] = PREMORTEM_PROMPT.format(
                role=expert.role,
                problem=session.problem_statement,
                selected_coa=selected_coa,
            )

    results = await orch._invoke_parallel(
        premortem_experts, prompts, session, "premortem"
    )

    session.artifacts["premortem"] = {
        "selected_coa": top_label,
        "analyses": results,
    }
    session.phases_completed.append("premortem")


async def phase_synthesis(orch: WarRoomOrchestrator, session: WarRoomSession) -> None:
    """Phase 7: Supreme Commander Synthesis."""
    # Unseal the Merkle-DAG to reveal full attribution
    unsealed = session.merkle_dag.unseal()
    coa_entries = [n for n in unsealed if n["phase"] == "coa"]
    coas_unsealed = "\n\n".join(
        f"### {n['label']} (by {n['expert_role']} / {n['expert_model']})\n"
        f"{n['content']}"
        for n in coa_entries
    )

    intel = session.artifacts.get("intel", {})
    scout = intel.get("scout_report", "N/A")
    intel_rpt = intel.get("intel_report", "N/A")
    intel_text = f"Scout: {scout}\n\nIntel Officer: {intel_rpt}"

    prompt = SYNTHESIS_PROMPT.format(
        problem=session.problem_statement,
        intel=intel_text,
        assessment=session.artifacts.get("assessment", {}).get("content", "N/A"),
        coas_unsealed=coas_unsealed,
        red_team=session.artifacts.get("red_team", {}).get("challenges", "N/A"),
        voting=json.dumps(session.artifacts.get("voting", {}), indent=2),
        premortem=json.dumps(session.artifacts.get("premortem", {}), indent=2),
    )

    # Supreme Commander synthesis (native Opus)
    result = await orch._invoke_expert(
        "supreme_commander", prompt, session, "synthesis"
    )

    session.artifacts["synthesis"] = {
        "decision": result,
        "attribution_revealed": True,
    }
    session.phases_completed.append("synthesis")
