"""The default-on posture lives in prose, so prose is what these guard.

Feature: Delegation By Default
  As an operator
  I want every workflow that reaches execution work to delegate it
  So that installed CLIs are used without anyone remembering to ask

The executor's behaviour has its own tests. What those cannot catch is
the posture being reverted in the text a session actually reads: a
`When To Use` list restored to delegation-core, or the size threshold
put back into task-assessment, would turn delegation opt-in again with
every Python test still green.

Each assertion anchors on a clause unique to the passage it guards, so
deleting that passage turns this file red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DELEGATION_CORE = REPO / "plugins/conjure/skills/delegation-core/SKILL.md"
TASK_ASSESSMENT = (
    REPO / "plugins/conjure/skills/delegation-core/modules/task-assessment.md"
)
MISSION = REPO / "plugins/attune/skills/mission-orchestrator/SKILL.md"
EXECUTION = REPO / "plugins/attune/skills/project-execution/SKILL.md"
SUMMON = REPO / "plugins/egregore/skills/summon/SKILL.md"
WAR_ROOM = REPO / "plugins/attune/skills/war-room/SKILL.md"


@pytest.mark.bdd
def test_delegation_core_states_the_default_rather_than_the_occasion() -> None:
    """GIVEN the delegation-core skill.

    WHEN a session reads it to decide whether to delegate
    THEN it finds a default posture and an exception list

    The `When To Use` list this replaced was accurate about when
    delegation pays and silent about who had to remember. An occasion
    nobody remembers is an opt-in.
    """
    text = DELEGATION_CORE.read_text()

    assert "## Default Posture" in text
    assert "Declining it is the step that takes a decision" in text
    assert "## Keep Local" in text
    assert "## When To Use" not in text


@pytest.mark.bdd
def test_delegation_core_documents_both_ways_out() -> None:
    """GIVEN an operator who does not want external models.

    WHEN they look for how to decline
    THEN both switches and their precedence are stated

    A default-on feature whose opt-out is undocumented is not opt-out.
    """
    text = DELEGATION_CORE.read_text()

    assert "CONJURE_DELEGATION" in text
    assert '"enabled": false' in text
    assert "environment over file" in text


@pytest.mark.bdd
def test_delegation_core_tells_the_caller_what_an_exhausted_chain_means() -> None:
    """GIVEN a delegation where no provider answered.

    WHEN the skill is consulted
    THEN it names the result as an instruction to work locally

    Without this the fallback reads as an error, and a mission that
    stops on it does less than the opt-in version did.
    """
    text = DELEGATION_CORE.read_text()

    assert "providers_exhausted" in text
    assert "instruction to do the work locally" in text


@pytest.mark.bdd
def test_size_thresholds_rank_payoff_and_gate_nothing() -> None:
    """GIVEN the task-assessment module.

    WHEN a task is measured against its thresholds
    THEN no threshold can hold eligible work local

    This is the passage that made delegation opt-in in practice. Its
    "keep local under 10,000 tokens and 20 files" row exempted most
    real tasks while the surrounding text said to delegate.
    """
    text = TASK_ASSESSMENT.read_text()

    assert "**Keep local**: <10,000 tokens and <20 files" not in text
    assert "no row here is a" in text
    assert "Keep Local clause" in text


@pytest.mark.bdd
@pytest.mark.parametrize(
    ("path", "anchor"),
    [
        (MISSION, "## Delegation During a Mission"),
        (EXECUTION, "### Delegation Check (First, Per Task)"),
        (SUMMON, "### Delegation Inside the Loop"),
    ],
    ids=["mission-orchestrator", "project-execution", "egregore-summon"],
)
def test_each_orchestrator_carries_the_posture(path: Path, anchor: str) -> None:
    """GIVEN a workflow that reaches execution work.

    WHEN it runs
    THEN its own skill text states that delegation is the default

    delegation-core stating the posture is not enough. A mission phase
    reads the mission skill, and a posture it never encounters is one
    it will not apply.
    """
    text = path.read_text()

    assert anchor in text
    assert "conjure:delegation-core" in text


@pytest.mark.bdd
@pytest.mark.parametrize(
    ("path", "anchor"),
    [
        (MISSION, "providers_exhausted"),
        (EXECUTION, "fallback_reason"),
        (SUMMON, "not a step failure"),
    ],
    ids=["mission-orchestrator", "project-execution", "egregore-summon"],
)
def test_each_orchestrator_handles_the_fallback(path: Path, anchor: str) -> None:
    """GIVEN a delegation that produced no answer.

    WHEN the workflow receives it
    THEN its skill says to complete the work rather than stop

    The egregore case is the one with teeth: an exhausted chain counted
    as a step failure would spend the retry budget on a machine where
    nothing is broken.
    """
    assert anchor in path.read_text()


@pytest.mark.bdd
def test_the_war_room_refuses_to_fill_empty_seats_with_claude() -> None:
    """GIVEN a war room that cannot reach any external model.

    WHEN delegation falls back
    THEN the skill forbids presenting a single model as a panel

    Everywhere else a local fallback costs time. Here it would
    misrepresent the result: seven roles played by one model produce
    agreement that reads as consensus.
    """
    text = WAR_ROOM.read_text()

    assert "is not a panel" in text
    assert "Do not fill the empty seats with Claude" in text
