"""BDD tests for attune skill-library-mission skill structure.

Feature: Skill Library Mission Skill Validation
  As a plugin developer
  I want the skill-library-mission skill to follow ecosystem conventions
  So that the retiring-fellow knowledge-transfer mission can be
  dispatched reliably from the attune plugin system
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

PLUGIN_DIR = Path(__file__).resolve().parent.parent.parent.parent
SKILL_DIR = PLUGIN_DIR / "skills" / "skill-library-mission"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
REFERENCES_DIR = SKILL_DIR / "references"
COMMAND_FILE = PLUGIN_DIR / "commands" / "skill-library.md"

EXPECTED_MODULES = [
    "taxonomy.md",
    "authoring-rules.md",
    "review-protocol.md",
]

EXPECTED_REFERENCES = [
    "mission-prompt.md",
]

REQUIRED_SECTIONS = [
    "## When To Use",
    "## When NOT To Use",
    "## Exit Criteria",
    "## Provenance and Maintenance",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestSkillLibraryMissionSkillFile:
    """
    Feature: Skill file existence and frontmatter contract

    As a plugin validator
    I want the SKILL.md to exist with a complete frontmatter contract
    So that discovery and progressive loading work
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: SKILL.md exists
        Given the attune plugin skills directory
        When I look for skill-library-mission/SKILL.md
        Then the file exists and is non-empty
        """
        assert SKILL_FILE.exists(), f"missing {SKILL_FILE}"
        assert SKILL_FILE.read_text(encoding="utf-8").strip()

    @pytest.mark.unit
    def test_frontmatter_contract(self):
        """
        Scenario: frontmatter carries name, description, and modules
        Given the SKILL.md frontmatter
        When I parse it as YAML
        Then name matches the directory and description states
        when to use it and when not to
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))
        assert fm.get("name") == "skill-library-mission"
        description = fm.get("description", "")
        assert "Use when" in description
        assert "Do not use" in description
        assert fm.get("modules") == [f"modules/{m}" for m in EXPECTED_MODULES]

    @pytest.mark.unit
    def test_required_sections_present(self):
        """
        Scenario: skill body contains the required sections
        Given the SKILL.md body
        When I scan for headings
        Then usage boundaries, exit criteria, and provenance exist
        """
        content = SKILL_FILE.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in content, f"missing section: {section}"


class TestSkillLibraryMissionModules:
    """
    Feature: Progressive-loading modules and references exist

    As a mission dispatcher
    I want every declared module and reference on disk
    So that phase guidance loads without dangling paths
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("module", EXPECTED_MODULES)
    def test_module_exists(self, module):
        """
        Scenario: declared module file exists
        Given the modules directory
        When I look for the declared module
        Then it exists and is non-empty
        """
        path = MODULES_DIR / module
        assert path.exists(), f"missing module: {path}"
        assert path.read_text(encoding="utf-8").strip()

    @pytest.mark.unit
    @pytest.mark.parametrize("reference", EXPECTED_REFERENCES)
    def test_reference_exists(self, reference):
        """
        Scenario: the generalized mission prompt is preserved
        Given the references directory
        When I look for mission-prompt.md
        Then it exists and contains all three mission phases
        """
        path = REFERENCES_DIR / reference
        assert path.exists(), f"missing reference: {path}"
        content = path.read_text(encoding="utf-8")
        for phase in ("Phase 1", "Phase 2", "Phase 3"):
            assert phase in content, f"prompt lost {phase}"


class TestSkillLibraryCommand:
    """
    Feature: /attune:skill-library command registration

    As a user
    I want a slash command that dispatches the mission
    So that the library can be rebuilt in any repository
    """

    @pytest.mark.unit
    def test_command_file_exists_and_routes_to_skill(self):
        """
        Scenario: command exists and invokes the skill
        Given the attune commands directory
        When I read skill-library.md
        Then it references Skill(attune:skill-library-mission)
        """
        assert COMMAND_FILE.exists(), f"missing {COMMAND_FILE}"
        content = COMMAND_FILE.read_text(encoding="utf-8")
        assert "attune:skill-library-mission" in content

    @pytest.mark.unit
    def test_registered_in_plugin_manifest(self):
        """
        Scenario: manifest registers both command and skill
        Given the plugin.json manifest
        When I parse commands and skills
        Then both new entries are present
        """
        manifest = json.loads(
            (PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert "./commands/skill-library.md" in manifest["commands"]
        assert "./skills/skill-library-mission" in manifest["skills"]
