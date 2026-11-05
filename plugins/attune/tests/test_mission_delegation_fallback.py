"""Guard where a mission sends execution work when no external CLI answers.

Feature: Session-model fallback for delegated execution
  As an operator without gemini, codex or the other conjure CLIs installed
  I want /mission to hand eligible tasks to a subagent in whatever harness runs it
  So that the work still runs in isolation, on the model I chose

The rule lives in one module that both orchestrators point to, so prose is
what these guard. Text is whitespace-normalized before matching, so a
rewrap never turns a test red. Each anchor appears once in its file, so
deleting the passage it guards does.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1] / "skills"
MISSION = SKILLS / "mission-orchestrator" / "SKILL.md"
EXECUTION = SKILLS / "project-execution" / "SKILL.md"
MODULE = SKILLS / "project-execution" / "modules" / "subagent-fallback.md"
IMPLEMENTER = SKILLS.parent / "agents" / "project-implementer.md"

ORCHESTRATORS = pytest.mark.parametrize(
    "path", [MISSION, EXECUTION], ids=["mission-orchestrator", "project-execution"]
)


def _read(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text())


def _single(text: str, anchor: str, path: Path) -> None:
    count = text.count(anchor)
    assert count == 1, f"{path.name} has {count} copies of {anchor!r}; expected one"


@pytest.mark.bdd
@ORCHESTRATORS
def test_orchestrator_points_at_the_fallback_module(path: Path) -> None:
    """GIVEN a delegation that returns providers_exhausted.

    WHEN the orchestrator reads its own skill text
    THEN it is sent to the one module that carries the fallback rule
    """
    text = _read(path)

    assert "subagent-fallback.md" in text
    _single(text, "conjure is not installed", path)


def test_execution_frontmatter_lists_the_module() -> None:
    """The repo audit expects every module the skill uses to be listed.

    `meta_evaluation.py` reads the `modules:` key; the runtime load path is
    the prose pointer pinned by `test_orchestrator_points_at_the_fallback_module`.
    """
    front = EXECUTION.read_text().split("---")[1]

    assert "- modules/subagent-fallback.md" in front


@pytest.mark.bdd
@ORCHESTRATORS
def test_declined_delegation_stays_in_the_session(path: Path) -> None:
    """GIVEN fallback_reason is delegation_disabled.

    WHEN either orchestrator handles it
    THEN both say to work locally, so the two skills cannot disagree

    project-execution once branched on any fallback_reason and sent a
    declined delegation to a subagent while the mission kept it local.
    """
    text = _read(path)

    assert "`delegation_disabled`" in text
    _single(text, "a subagent is still a delegation", path)
    blanket = "If the result carries a `fallback_reason`, no external model ran."
    assert blanket not in text


@pytest.mark.bdd
@ORCHESTRATORS
def test_no_orchestrator_keeps_the_inline_default(path: Path) -> None:
    """The retired wording must not come back beside the new rule."""
    text = _read(path).lower()

    assert "do the task in the mission itself" not in text
    assert "always work inline" not in text


@pytest.mark.bdd
@pytest.mark.parametrize(
    "anchor",
    [
        "the host harness's own subagent tool",
        "only when the harness has no subagent tool",
        "In Codex, OpenCode or another harness",
    ],
)
def test_module_is_not_tied_to_claude_code(anchor: str) -> None:
    """GIVEN the mission runs in Codex, OpenCode or another harness.

    WHEN no conjure CLI answers
    THEN the module names that harness's subagent tool, and inline work
    is the exception for a harness that has none
    """
    _single(_read(MODULE), anchor, MODULE)


@pytest.mark.bdd
@pytest.mark.parametrize(
    "anchor",
    [
        "Execute tasks go to `attune:project-implementer`",
        "Review-phase tasks go to `general-purpose`",
        "`Skill(imbue:proof-of-work)`",
        "the same TDD workflow",
    ],
)
def test_module_picks_the_agent_by_phase(anchor: str) -> None:
    """GIVEN a review mission whose tasks are findings, not code.

    WHEN the fallback dispatches one
    THEN it goes to a general agent validated by evidence, not to the
    implementer validated by a RED test
    """
    _single(_read(MODULE), anchor, MODULE)


@pytest.mark.bdd
@pytest.mark.parametrize(
    "anchor",
    [
        "Always pass `model`",
        "`CLAUDE_CODE_SUBAGENT_MODEL`",
        "`CLAUDE_CODE_SUBAGENT_MODEL_FORCE`",
        "The agent pins `sonnet`",
        "`effort`",
    ],
)
def test_module_keeps_the_session_model(anchor: str) -> None:
    """GIVEN project-implementer pins `model: sonnet` and `effort: medium`.

    WHEN the fallback dispatches it
    THEN the module passes the session model on every call, and names
    the settings that replace an omitted or passed model
    """
    _single(_read(MODULE), anchor, MODULE)


@pytest.mark.bdd
@pytest.mark.parametrize(
    "anchor",
    ['`worktree.baseRef` is `"head"`', "Merge the worktree branch"],
)
def test_module_keeps_work_on_the_mission_branch(anchor: str) -> None:
    """GIVEN project-implementer runs in a worktree.

    WHEN `worktree.baseRef` is left at its default
    THEN the module says the worktree starts from the default branch,
    and how the result comes back to the mission branch
    """
    _single(_read(MODULE), anchor, MODULE)


@pytest.mark.bdd
@pytest.mark.parametrize("anchor", ["is not a panel", "Batch small tasks"])
def test_module_bounds_panels_and_cost(anchor: str) -> None:
    """GIVEN several seats or many small tasks reach the fallback.

    WHEN one model would fill every seat, or one subagent each task
    THEN the module defers to war-room for panels and batches small tasks
    """
    _single(_read(MODULE), anchor, MODULE)


@pytest.mark.bdd
def test_mission_exit_criterion_allows_the_inline_exception() -> None:
    """The exit criterion must be meetable on a harness with no subagent tool."""
    anchor = "or inline when the harness has no subagent tool"
    _single(_read(MISSION), anchor, MISSION)


def test_implementer_still_pins_sonnet() -> None:
    """The override instruction exists because of this pin.

    If the pin changes to `inherit` or another model, the module's
    reason no longer holds and its text needs revising.
    """
    front = IMPLEMENTER.read_text().split("---")[1]
    pins = re.findall(r"^model:\s*(\S+)\s*$", front, flags=re.MULTILINE)

    assert pins == ["sonnet"]
