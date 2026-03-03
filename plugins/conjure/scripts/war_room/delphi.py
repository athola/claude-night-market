"""Delphi mode logic for iterative convergence in War Room sessions.

Contains convene_delphi, revision rounds, and convergence computation.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from scripts.war_room.experts import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    clear_availability_cache,
    get_fallback_notice,
)
from scripts.war_room.models import WarRoomSession
from scripts.war_room.phases import (
    phase_assessment,
    phase_coa_development,
    phase_intel,
    phase_premortem,
    phase_red_team,
    phase_synthesis,
    phase_voting,
)
from scripts.war_room.prompts import DELPHI_REVISION_PROMPT

if TYPE_CHECKING:
    from scripts.war_room.orchestrator import WarRoomOrchestrator


async def convene_delphi(
    orch: WarRoomOrchestrator,
    problem: str,
    context_files: list[str] | None = None,
    max_rounds: int = 5,
    convergence_threshold: float = 0.85,
) -> WarRoomSession:
    """Convene Delphi-style War Room with iterative convergence.

    Args:
        orch: The orchestrator instance
        problem: The problem/decision to deliberate
        context_files: Optional file globs for context
        max_rounds: Maximum Delphi rounds (default 5)
        convergence_threshold: Agreement threshold to stop (default 0.85)

    Returns:
        Completed WarRoomSession with Delphi convergence data

    """
    # Clear availability cache for fresh session
    clear_availability_cache()

    # Initialize with full council for Delphi
    session = orch._initialize_session(problem, "full_council")
    session.metrics["start_time"] = datetime.now().isoformat()
    session.metrics["delphi_mode"] = True
    session.metrics["max_rounds"] = max_rounds
    session.metrics["convergence_threshold"] = convergence_threshold

    try:
        # Round 1: Standard generation
        await phase_intel(orch, session, context_files)
        await phase_assessment(orch, session)
        await phase_coa_development(orch, session)
        await phase_red_team(orch, session)
        await phase_voting(orch, session)

        convergence = compute_convergence(session)
        session.metrics["round_1_convergence"] = convergence

        delphi_round = 2
        while convergence < convergence_threshold and delphi_round <= max_rounds:
            # Delphi revision round
            await delphi_revision_round(orch, session, delphi_round)
            await phase_red_team(orch, session)
            await phase_voting(orch, session)

            convergence = compute_convergence(session)
            session.metrics[f"round_{delphi_round}_convergence"] = convergence
            delphi_round += 1

        session.metrics["final_convergence"] = convergence
        session.metrics["total_rounds"] = delphi_round - 1

        # Final phases
        await phase_premortem(orch, session)
        await phase_synthesis(orch, session)

        session.status = "completed"

    except Exception as e:
        session.status = f"failed: {e}"
        raise

    finally:
        session.metrics["end_time"] = datetime.now().isoformat()
        # Capture any fallback notices
        fallback_notice = get_fallback_notice()
        if fallback_notice:
            session.artifacts["fallback_notice"] = fallback_notice
        orch._persist_session(session)

    return session


async def delphi_revision_round(
    orch: WarRoomOrchestrator, session: WarRoomSession, round_number: int
) -> None:
    """Execute a Delphi revision round where experts revise positions."""
    # Get previous COAs and Red Team feedback
    red_team_feedback = session.artifacts.get("red_team", {}).get("challenges", "N/A")
    previous_coas = session.artifacts.get("coa", {}).get("raw_coas", {})

    # Get anonymized view for other positions
    anonymized = session.merkle_dag.get_anonymized_view(phase="coa")
    other_positions = "\n\n".join(
        f"### {c['label']}\n{c['content']}" for c in anonymized
    )

    # Revision prompts for each expert who contributed COAs
    panel = FULL_COUNCIL
    revision_experts = [
        e
        for e in panel
        if e in previous_coas and e not in ["supreme_commander", "red_team"]
    ]

    prompts: dict[str, str] = {}
    for expert_key in revision_experts:
        expert = EXPERT_CONFIGS.get(expert_key)
        if expert:
            prompts[expert_key] = DELPHI_REVISION_PROMPT.format(
                role=expert.role,
                round_number=round_number,
                problem=session.problem_statement,
                feedback=red_team_feedback,
                previous_position=previous_coas.get(expert_key, "N/A"),
                other_positions=other_positions,
            )

    results = await orch._invoke_parallel(revision_experts, prompts, session, "coa")

    # Update COAs with revised positions
    session.artifacts["coa"]["raw_coas"].update(results)
    session.artifacts["coa"]["delphi_round"] = round_number


def compute_convergence(session: WarRoomSession) -> float:
    """Compute expert convergence score based on voting agreement.

    Returns a score between 0 and 1, where:
    - 1.0 = perfect agreement (all experts rank COAs identically)
    - 0.0 = complete disagreement

    """
    voting = session.artifacts.get("voting", {})
    borda_scores = voting.get("borda_scores", {})

    if not borda_scores or len(borda_scores) < 2:
        return 0.0

    # Compute normalized standard deviation of scores
    scores = list(borda_scores.values())
    if not scores:
        return 0.0

    mean_score = sum(scores) / len(scores)
    if mean_score == 0:
        return 0.0

    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    std_dev = variance**0.5

    # Normalize: higher score spread = higher convergence
    # (clear winner indicates agreement)
    max_possible_spread = mean_score  # Theoretical max
    if max_possible_spread == 0:
        return 0.0

    convergence: float = min(1.0, std_dev / max_possible_spread)
    return convergence
