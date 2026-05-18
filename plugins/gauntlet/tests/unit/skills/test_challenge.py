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


def test_skill_md_documents_in_loop_registration() -> None:
    """Scenario: SKILL.md tells the model to call the registration helper.

    Given the gauntlet:challenge SKILL.md
    When I read the body
    Then it shows the register_in_loop_provider_if_inside_claude_code call.
    """
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "register_in_loop_provider_if_inside_claude_code" in text
    assert "from gauntlet.providers.in_loop import" in text
