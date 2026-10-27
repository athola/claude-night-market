"""BDD contract tests for the memory-palace-architect skill wiring.

Feature: memory-palace-architect is loaded by the palace-architect agent
  As a memory-palace user
  I want the agent that designs palaces to load the skill that holds
  the design method
  So that the skill has a real invocation path (#618) and the commands
  both documents give actually run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_FILE = PLUGIN_ROOT / "skills" / "memory-palace-architect" / "SKILL.md"
AGENT_FILE = PLUGIN_ROOT / "agents" / "palace-architect.md"


class TestSkillIsWired:
    """Feature: the skill has a real invocation path (#618)."""

    @pytest.mark.bdd
    def test_agent_loads_the_skill(self) -> None:
        """Given the palace-architect agent, it must invoke the skill."""
        text = AGENT_FILE.read_text(encoding="utf-8")
        assert "Skill(memory-palace:memory-palace-architect)" in text

    @pytest.mark.bdd
    def test_skill_no_longer_claims_unwired(self) -> None:
        """The skill must not advertise itself as unwired once wired."""
        text = SKILL_FILE.read_text(encoding="utf-8")
        assert "Status: unwired" not in text
        assert "Status: wired" in text


class TestDocumentedCommandsRun:
    """Feature: no document tells the reader to run a script that cannot run."""

    @pytest.mark.bdd
    @pytest.mark.parametrize("doc", [SKILL_FILE, AGENT_FILE], ids=["skill", "agent"])
    def test_no_palace_manager_command(self, doc: Path) -> None:
        """palace_manager.py has no CLI entry point, so it cannot be run.

        The skill cited ``scripts/palace_manager.py``, which does not
        exist, and the agent cited the module under ``src/``, which has
        no ``__main__``. Both must point at ``memory_palace_cli.py``.
        """
        text = doc.read_text(encoding="utf-8")
        assert "palace_manager.py" not in text
        assert "memory_palace_cli.py create" in text
