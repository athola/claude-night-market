"""clear-context caps its self-grading loop and its handoff chain (ADR-0025).

Both caps live only in prose: nothing executes them, so a test on the
prose is the whole guard. Each assertion anchors on a clause that
appears once in the file and only inside the passage it guards, so
deleting or loosening that passage turns this red. A bare substring
like "handoff_depth" is not enough, because the file names the variable
in three places and only one of them states the bound.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL = Path(__file__).resolve().parents[2] / "skills" / "clear-context" / "SKILL.md"


@pytest.fixture(scope="module")
def skill_text() -> str:
    """Return the SKILL.md body, read once."""
    return _SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill_prose(skill_text: str) -> str:
    """Return the body with runs of whitespace collapsed to spaces.

    The file wraps at 80 columns, so a sentence worth anchoring on is
    usually split across lines. Matching the collapsed form keeps the
    anchor a whole clause instead of whatever fragment fits one line.
    """
    return " ".join(skill_text.split())


def test_skill_documents_a_rescore_cap(skill_prose: str) -> None:
    """The self-grading loop stops at two re-scores, and says what then."""
    assert "Re-score at most twice." in skill_prose
    assert "A draft that fails a third time is handed to the user" in skill_prose


def test_skill_gives_the_reason_the_rescore_loop_is_capped(
    skill_prose: str,
) -> None:
    """The rationale is the part a future editor needs to weigh."""
    assert (
        "the writer of the state file is also its grader here, and a loop of "
        "self-grading converges on confidence, not on clarity" in skill_prose
    )


def test_skill_documents_a_handoff_depth_cap(skill_prose: str) -> None:
    """The continuation chain stops at depth 3 and reports to the user."""
    assert "Increment `handoff_depth` in `session-state.md`. At depth 3," in skill_prose
    assert "stop and report to the user instead of spawning again" in skill_prose


def test_skill_gives_the_reason_the_handoff_chain_is_capped(
    skill_prose: str,
) -> None:
    """Without the reason, the cap reads as an arbitrary number."""
    assert (
        "three continuations without finishing is a task that needs splitting"
        in skill_prose
    )


def test_the_rescore_cap_is_stated_once(skill_prose: str) -> None:
    """Two statements of one bound are two places for it to drift."""
    assert skill_prose.count("Re-score at most twice") == 1
