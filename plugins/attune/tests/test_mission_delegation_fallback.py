"""Guard where a mission sends execution work when no external CLI answers.

Feature: Session-model fallback for delegated execution
  As an operator without gemini, codex or the other conjure CLIs installed
  I want /mission to hand eligible tasks to a subagent in whatever harness runs it
  So that the work still runs in isolation, on the model I chose

The fallback lives in skill prose, so prose is what these guard. Each
anchor appears once in its file, so deleting the passage turns a test red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1] / "skills"
MISSION = SKILLS / "mission-orchestrator" / "SKILL.md"
EXECUTION = SKILLS / "project-execution" / "SKILL.md"

ORCHESTRATORS = pytest.mark.parametrize(
    "path", [MISSION, EXECUTION], ids=["mission-orchestrator", "project-execution"]
)


def _single(text: str, anchor: str, path: Path) -> None:
    assert text.count(anchor) == 1, (
        f"{path.parent.name}/SKILL.md has {text.count(anchor)} copies of "
        f"{anchor!r}; expected exactly one"
    )


@pytest.mark.bdd
@ORCHESTRATORS
def test_exhausted_chain_dispatches_a_claude_subagent(path: Path) -> None:
    """GIVEN a delegation whose fallback_reason is providers_exhausted.

    WHEN the orchestrator reads its own skill text
    THEN it is told to dispatch the implementer subagent, not work inline
    """
    text = path.read_text()

    _single(text, "hand the task to a subagent", path)
    assert "Agent(attune:project-implementer)" in text


@pytest.mark.bdd
@ORCHESTRATORS
def test_subagent_runs_on_the_session_model(path: Path) -> None:
    """GIVEN project-implementer pins `model: sonnet` in its frontmatter.

    WHEN the fallback dispatches it
    THEN the skill says to override the model with the session's own

    Without the override an Opus mission would silently run its
    execute phase on Sonnet.
    """
    text = path.read_text()

    _single(text, "the session's own", path)
    _single(text, "dispatch `general-purpose`", path)


@pytest.mark.bdd
@ORCHESTRATORS
def test_missing_conjure_takes_the_same_path(path: Path) -> None:
    """GIVEN conjure is not installed, so delegation-core cannot load.

    WHEN the orchestrator reaches an eligible task
    THEN it falls back to the subagent exactly as for an exhausted chain
    """
    text = path.read_text()

    _single(text, "conjure is not installed", path)


def test_implementer_still_pins_a_model_the_fallback_overrides() -> None:
    """The override instruction exists because of this pin.

    If the agent stops pinning a model, the override is dead text and
    the skill passages above should be simplified.
    """
    agent = (SKILLS.parent / "agents" / "project-implementer.md").read_text()

    assert "\nmodel: " in agent


@pytest.mark.bdd
@ORCHESTRATORS
def test_fallback_is_not_tied_to_claude_code(path: Path) -> None:
    """GIVEN the mission runs in a harness other than Claude Code.

    WHEN no conjure CLI answers
    THEN the skill names the host harness's own subagent primitive

    Codex and OpenCode have no `Agent` tool. A fallback written only
    in Claude Code terms would leave those sessions working inline.
    """
    text = path.read_text()

    _single(text, "the host harness's own subagent", path)
    _single(text, "In Claude Code,", path)
