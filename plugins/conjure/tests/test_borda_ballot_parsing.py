"""Each ranked line awards its points to the COA named on that line.

Math review finding C6. compute_borda_scores tried ranks 1..n and gave a
label the first rank whose 200-character window contained it, so every
label within 200 characters after "1." took first-place points. Five
unanimous experts writing the VOTING_PROMPT format with 100-character
justifications scored COA-A 15, COA-B 15, COA-C 10 instead of 15/10/5.
"""

from __future__ import annotations

import pytest
from scripts.war_room.phases import compute_borda_scores

LABELS = ["COA-A", "COA-B", "COA-C"]


def _ballot(order: list[str], justification_chars: int) -> str:
    """Write a ballot in the format VOTING_PROMPT asks for."""
    reason = "x" * justification_chars
    lines = [f"{rank}. {label} - {reason}" for rank, label in enumerate(order, 1)]
    return "\n".join([*lines, f"TOP PICK: {order[0]} because it is best."])


@pytest.mark.parametrize("justification_chars", [10, 100, 250])
def test_a_unanimous_panel_scores_n_down_to_one_per_expert(
    justification_chars: int,
) -> None:
    """Five identical ballots give 15, 10 and 5 points."""
    votes = {f"expert{n}": _ballot(LABELS, justification_chars) for n in range(5)}

    assert compute_borda_scores(votes, LABELS) == {
        "COA-A": 15,
        "COA-B": 10,
        "COA-C": 5,
    }


def test_a_label_mentioned_in_a_justification_keeps_its_own_rank() -> None:
    """Naming a rival in the reason for first place does not promote it."""
    ballot = (
        "1. COA-B - stronger than COA-C on cost\n"
        "2. COA-C - cheaper than COA-A\n"
        "3. COA-A - weakest"
    )

    assert compute_borda_scores({"e": ballot}, LABELS) == {
        "COA-A": 1,
        "COA-B": 3,
        "COA-C": 2,
    }


def test_a_label_that_prefixes_another_scores_only_its_own_line() -> None:
    """COA_1 is a prefix of COA_10; each scores its own rank."""
    labels = [f"COA_{i}" for i in range(12)]
    ballot = "\n".join(
        f"{rank}. {label} is next" for rank, label in enumerate(labels, 1)
    )

    scores = compute_borda_scores({"e": ballot}, labels)

    assert scores == {label: 12 - i for i, label in enumerate(labels)}
