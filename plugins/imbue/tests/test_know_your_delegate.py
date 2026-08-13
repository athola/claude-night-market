"""Contract tests for the know-your-delegate module.

Feature: Delegation prompts are written for the delegate that runs them
  A prompt aimed at the wrong capability either over-constrains a
  capable agent or under-specifies for a limited one.
"""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILL = PLUGIN_ROOT / "skills" / "latent-space-engineering"
MODULE = SKILL / "modules" / "know-your-delegate.md"


def test_module_exists() -> None:
    """Scenario: the module is present."""
    assert MODULE.exists(), f"missing {MODULE}"


def test_module_is_linked_from_the_skill() -> None:
    """Scenario: an unlinked module is never loaded."""
    assert "know-your-delegate" in (SKILL / "SKILL.md").read_text()


def test_four_questions_about_the_delegate_are_present() -> None:
    """Scenario: model, tools, capability edge, and missing context."""
    content = MODULE.read_text().lower()
    for probe in ("what model", "what tools", "what context"):
        assert probe in content, f"missing probe: {probe}"


def test_prompts_are_proposals_not_instructions() -> None:
    """Scenario: the central reframing survives edits."""
    content = MODULE.read_text().lower()
    assert "proposals" in content and "compliance" in content


def test_delegate_reviews_the_prompt_before_running() -> None:
    """Scenario: the review-then-iterate step is documented."""
    content = MODULE.read_text().lower()
    assert "review" in content and "before running" in content
