"""BDD tests for scribe doc-importer skill structure.

Feature: Document Importer Skill Validation
  As a plugin developer
  I want the doc-importer skill to follow ecosystem conventions
  So that external document import integrates correctly with
  the scribe doc-generator remediation workflow
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "doc-importer"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
PLUGIN_JSON = (
    Path(__file__).resolve().parent.parent.parent.parent
    / ".claude-plugin"
    / "plugin.json"
)


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestDocImporterSkillFile:
    """Feature: Skill file existence and valid frontmatter.

    As a plugin validator
    I want the doc-importer SKILL.md to exist with valid metadata
    So that the skill can be discovered and loaded
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the scribe plugin
        When checking for doc-importer skill
        Then SKILL.md should exist on disk.
        """
        assert SKILL_FILE.exists(), f"Missing {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_name_matches(self) -> None:
        """Scenario: Skill name matches directory
        Given the doc-importer SKILL.md
        When reading the name field
        Then it should be 'doc-importer'.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm["name"] == "doc-importer"

    @pytest.mark.bdd
    def test_depends_on_document_conversion(self) -> None:
        """Scenario: Depends on leyline document-conversion
        Given the doc-importer skill
        When reading dependencies
        Then leyline:document-conversion should be listed.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        deps = fm.get("dependencies", [])
        assert "leyline:document-conversion" in deps

    @pytest.mark.bdd
    def test_depends_on_doc_generator(self) -> None:
        """Scenario: Depends on scribe doc-generator
        Given the doc-importer skill
        When reading dependencies
        Then scribe:doc-generator should be listed for handoff.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        deps = fm.get("dependencies", [])
        assert "scribe:doc-generator" in deps


class TestDocImporterContent:
    """Feature: Skill content covers the import workflow.

    As a user importing a document
    I want clear workflow steps
    So that I get clean markdown output
    """

    @pytest.mark.bdd
    def test_mentions_conversion_protocol(self) -> None:
        """Scenario: References document-conversion protocol
        Given the doc-importer SKILL.md
        When reading the content
        Then it should reference leyline:document-conversion.
        """
        content = SKILL_FILE.read_text()
        assert "document-conversion" in content

    @pytest.mark.bdd
    def test_mentions_sanitization(self) -> None:
        """Scenario: References content sanitization
        Given the doc-importer SKILL.md
        When reading the content
        Then it should reference content-sanitization.
        """
        content = SKILL_FILE.read_text()
        assert "content-sanitization" in content

    @pytest.mark.bdd
    def test_has_exit_criteria(self) -> None:
        """Scenario: Has exit criteria
        Given the doc-importer SKILL.md
        When reading the content
        Then it should have an exit criteria section.
        """
        content = SKILL_FILE.read_text()
        assert "Exit Criteria" in content


class TestDocImporterRegistration:
    """Feature: Skill registered in scribe plugin.json.

    As the plugin system
    I want doc-importer in the skills array
    So that it is discovered automatically
    """

    @pytest.mark.bdd
    def test_registered_in_plugin_json(self) -> None:
        """Scenario: Skill appears in plugin.json
        Given the scribe plugin.json
        When reading the skills array
        Then './skills/doc-importer' should be listed.
        """
        plugin_data = json.loads(PLUGIN_JSON.read_text())
        skills = plugin_data.get("skills", [])
        assert "./skills/doc-importer" in skills
