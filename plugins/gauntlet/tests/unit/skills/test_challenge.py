"""Test the challenge SKILL.md wires the in-loop provider per #464.

Feature: gauntlet:challenge SKILL.md instructs the model to register
the in-loop variation provider before generating a challenge.
"""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SKILL_FILE = PLUGIN_ROOT / "skills" / "challenge" / "SKILL.md"


def test_skill_md_exists() -> None:
    assert SKILL_FILE.exists()


def test_in_loop_registration_happens_where_the_variation_runs() -> None:
    """Scenario: the provider is registered in the process that varies problems.

    Given the bank variation runs inside challenge_engine.py
    When the skill and the engine are read
    Then the engine calls the registration helper itself, and the skill
    says so instead of asking the model to call it in another process,
    where the registration could never reach the engine.
    """
    engine = SKILL_FILE.parents[2] / "scripts" / "challenge_engine.py"
    assert "register_in_loop_provider_if_inside_claude_code()" in engine.read_text(
        encoding="utf-8"
    )
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "register_in_loop_provider_if_inside_claude_code" in text
    assert "from gauntlet.providers.in_loop import" not in text
