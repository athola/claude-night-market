"""BDD contract tests for the palace-diagram skill wiring.

Feature: Palace Diagram is wired into /palace
  As a memory-palace user
  I want `/palace diagram <palace-id>` to invoke palace-diagram
  So that an orphan skill (issue #574) has a real invocation path
  and its documented backing renderer actually exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_FILE = PLUGIN_ROOT / "skills" / "palace-diagram" / "SKILL.md"
PALACE_COMMAND = PLUGIN_ROOT / "commands" / "palace.md"
RENDERER = PLUGIN_ROOT / "src" / "memory_palace" / "palace_renderer.py"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestSkillFileExists:
    """Feature: Skill file is present and parseable."""

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Given the palace-diagram directory, SKILL.md must exist."""
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_frontmatter_names_the_skill(self) -> None:
        """Frontmatter name must be palace-diagram."""
        fm = _parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))
        assert fm.get("name") == "palace-diagram"


class TestSkillIsWired:
    """Feature: the skill has a real invocation path (#574)."""

    @pytest.mark.bdd
    def test_command_documents_diagram_subcommand(self) -> None:
        """Scenario: /palace exposes diagram
        Given the /palace command doc
        When searching for the diagram subcommand
        Then `/palace diagram` and the skill invocation must be present.
        """
        text = PALACE_COMMAND.read_text(encoding="utf-8")
        assert "/palace diagram" in text
        assert "Skill(memory-palace:palace-diagram)" in text

    @pytest.mark.bdd
    def test_skill_no_longer_claims_unwired(self) -> None:
        """The skill must not advertise itself as unwired once wired."""
        text = SKILL_FILE.read_text(encoding="utf-8")
        assert "Status: unwired" not in text
        assert "Status: wired" in text

    @pytest.mark.bdd
    def test_no_reference_to_missing_palace_manager(self) -> None:
        """The stale palace_manager.py reference must be gone (no script)."""
        text = SKILL_FILE.read_text(encoding="utf-8")
        assert "palace_manager.py" not in text
        assert not (PLUGIN_ROOT / "scripts" / "palace_manager.py").exists()


class TestBackingRendererExists:
    """Feature: documented renderer API is real, not hallucinated."""

    @pytest.mark.bdd
    def test_renderer_methods_exist(self) -> None:
        """PalaceRenderer must define the four documented render methods."""
        src = RENDERER.read_text(encoding="utf-8")
        for method in (
            "palace_map",
            "entity_graph",
            "synapse_heatmap",
            "ascii_overview",
        ):
            assert f"def {method}(" in src, f"PalaceRenderer.{method} missing"
