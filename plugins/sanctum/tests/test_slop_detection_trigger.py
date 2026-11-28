"""Test: a slop score routes review attention, it is not the defect.

Feature: the score is a trigger, not a verdict

As a reviewer reading a flagged PR
I want the score to send me to the document's claims
So that the false claim is what gets sanctioned, not the wording

Caldara and Fernandez-Villaverde (2026) argue the same for journals: a
detector flag triggers a closer reading (Result 3), a detector is
informative in one direction because false negatives are sought and
false positives are not (section 2.1), and one visible mistake in
flagged text raises the odds of hidden ones (Result 2). Each assertion
anchors on a clause unique to the passage it guards.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "skills/pr-review-playbook/modules/slop-detection.md"
)


@pytest.fixture(scope="module")
def module_text() -> str:
    # Prose wraps at 80 columns, so a clause may span a line break.
    return " ".join(MODULE.read_text(encoding="utf-8").split())


@pytest.mark.parametrize(
    "clause",
    [
        "A high score sends the reviewer to the claims",
        "A low score is weak evidence",
        "check every claim in that document",
        "The finding to report is the false claim",
    ],
)
def test_the_module_treats_the_score_as_a_trigger(
    module_text: str, clause: str
) -> None:
    """GIVEN the slop-detection module of pr-review.

    WHEN a reviewer reads how to act on a score
    THEN each trigger-not-verdict clause is present
    """
    assert clause in module_text
