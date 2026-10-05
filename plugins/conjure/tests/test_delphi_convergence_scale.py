"""Convergence is normalized against the points compute_borda_scores awards.

Math review finding C3. _max_borda_cv assumed Borda points n-1..0, but
compute_borda_scores awards N..1. Five unanimous experts on three COAs
score 15/10/5: CV 0.408 against an assumed ceiling of 0.816, so
convergence read 0.5 and never reached the 0.85 threshold.
"""

from __future__ import annotations

import pytest
from scripts.war_room.delphi import compute_convergence
from scripts.war_room.models import WarRoomSession
from scripts.war_room.phases import compute_borda_scores


def _ballot(order: list[str]) -> str:
    return "\n".join(f"{rank}. {label} - reason" for rank, label in enumerate(order, 1))


def _convergence(ballots: list[list[str]], labels: list[str]) -> float:
    votes = {f"expert{n}": _ballot(order) for n, order in enumerate(ballots)}
    session = WarRoomSession(session_id="s", problem_statement="p")
    session.artifacts["voting"] = {"borda_scores": compute_borda_scores(votes, labels)}
    return compute_convergence(session)


@pytest.mark.parametrize("count", [2, 3, 5])
@pytest.mark.parametrize("experts", [1, 5])
def test_a_unanimous_panel_converges_fully(count: int, experts: int) -> None:
    """Identical ballots through the real tally give 1.0."""
    labels = [f"COA-{chr(65 + i)}" for i in range(count)]

    assert _convergence([labels] * experts, labels) == pytest.approx(1.0)


def test_a_split_panel_lands_strictly_between() -> None:
    """Two experts disagreeing on first place converge partway."""
    labels = ["COA-A", "COA-B", "COA-C"]
    split = _convergence(
        [["COA-A", "COA-B", "COA-C"], ["COA-B", "COA-A", "COA-C"]], labels
    )

    assert 0.0 < split < 1.0
