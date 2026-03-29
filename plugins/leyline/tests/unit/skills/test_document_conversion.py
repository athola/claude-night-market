"""BDD tests for leyline document-conversion skill structure.

Feature: Document Conversion Skill Validation
  As a plugin developer
  I want the document-conversion skill to follow ecosystem conventions
  So that the three-tier fallback pattern integrates correctly with
  consumer plugins (knowledge-intake, papers, doc-importer)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "document-conversion"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
PLUGIN_JSON = (
    Path(__file__).resolve().parent.parent.parent.parent
    / ".claude-plugin"
    / "plugin.json"
)

EXPECTED_MODULES = [
    "format-matrix.md",
    "fallback-tiers.md",
    "uri-construction.md",
]

REQUIRED_FRONTMATTER_KEYS = [
    "name",
    "description",
    "category",
    "tags",
    "dependencies",
    "provides",
    "usage_patterns",
    "complexity",
    "estimated_tokens",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestDocumentConversionSkillFile:
    """Feature: Skill file existence and readability.

    As a plugin validator
    I want the document-conversion SKILL.md to exist and be readable
    So that the skill can be discovered and loaded by the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the leyline plugin
        When checking for document-conversion skill
        Then SKILL.md should exist on disk.
        """
        assert SKILL_FILE.exists(), f"Missing {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_file_has_frontmatter(self) -> None:
        """Scenario: Valid YAML frontmatter
        Given the document-conversion SKILL.md
        When parsing the frontmatter
        Then it should be valid YAML with required keys.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm, "Frontmatter is empty or missing"
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in fm, f"Missing frontmatter key: {key}"

    @pytest.mark.bdd
    def test_skill_name_matches(self) -> None:
        """Scenario: Skill name matches directory
        Given the document-conversion SKILL.md
        When reading the name field
        Then it should be 'document-conversion'.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm["name"] == "document-conversion"

    @pytest.mark.bdd
    def test_category_is_infrastructure(self) -> None:
        """Scenario: Category is infrastructure
        Given the document-conversion skill
        When reading the category field
        Then it should be 'infrastructure' (leyline convention).
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm["category"] == "infrastructure"

    @pytest.mark.bdd
    def test_provides_document_conversion(self) -> None:
        """Scenario: Provides document-conversion capability
        Given the document-conversion skill
        When reading the provides field
        Then it should declare document-conversion infrastructure.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        provides = fm.get("provides", {})
        infra = provides.get("infrastructure", [])
        assert "document-conversion" in infra

    @pytest.mark.bdd
    def test_depends_on_content_sanitization(self) -> None:
        """Scenario: Depends on content-sanitization
        Given the document-conversion skill
        When reading the dependencies field
        Then it should include content-sanitization.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        deps = fm.get("dependencies", [])
        assert "content-sanitization" in deps

    @pytest.mark.bdd
    def test_progressive_loading_enabled(self) -> None:
        """Scenario: Progressive loading is enabled
        Given the document-conversion skill has modules
        When reading the progressive_loading field
        Then it should be true.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm.get("progressive_loading") is True


class TestDocumentConversionModules:
    """Feature: Module files exist and have valid frontmatter.

    As a plugin validator
    I want all declared modules to exist on disk
    So that progressive loading works correctly
    """

    @pytest.mark.bdd
    @pytest.mark.parametrize("module_name", EXPECTED_MODULES)
    def test_module_file_exists(self, module_name: str) -> None:
        """Scenario: Module file present
        Given the document-conversion skill
        When checking for module '{module_name}'
        Then the file should exist in modules/.
        """
        module_path = MODULES_DIR / module_name
        assert module_path.exists(), f"Missing module: {module_path}"

    @pytest.mark.bdd
    @pytest.mark.parametrize("module_name", EXPECTED_MODULES)
    def test_module_has_frontmatter(self, module_name: str) -> None:
        """Scenario: Module has valid frontmatter
        Given the module '{module_name}'
        When parsing its frontmatter
        Then it should have name and description fields.
        """
        content = (MODULES_DIR / module_name).read_text()
        fm = _parse_frontmatter(content)
        assert fm, f"Module {module_name} has no frontmatter"
        assert "name" in fm, f"Module {module_name} missing 'name'"
        assert "description" in fm, f"Module {module_name} missing 'description'"

    @pytest.mark.bdd
    def test_frontmatter_modules_match_disk(self) -> None:
        """Scenario: Declared modules match files on disk
        Given the SKILL.md declares modules in frontmatter
        When comparing to files in modules/
        Then every declared module should exist.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        declared = fm.get("modules", [])
        for mod_path in declared:
            full_path = SKILL_DIR / mod_path
            assert full_path.exists(), f"Declared module missing: {mod_path}"


class TestDocumentConversionContent:
    """Feature: Skill content covers the three-tier protocol.

    As a consumer skill author
    I want the skill to document all three fallback tiers
    So that I can implement the protocol correctly
    """

    @pytest.mark.bdd
    def test_mentions_three_tiers(self) -> None:
        """Scenario: All three tiers documented
        Given the document-conversion SKILL.md
        When searching for tier references
        Then Tier 1, Tier 2, and Tier 3 should all appear.
        """
        content = SKILL_FILE.read_text()
        assert "Tier 1" in content
        assert "Tier 2" in content
        assert "Tier 3" in content

    @pytest.mark.bdd
    def test_mentions_mcp_tool(self) -> None:
        """Scenario: MCP tool referenced
        Given the document-conversion SKILL.md
        When searching for the MCP tool name
        Then convert_to_markdown should appear.
        """
        content = SKILL_FILE.read_text()
        assert "convert_to_markdown" in content

    @pytest.mark.bdd
    def test_mentions_sanitization(self) -> None:
        """Scenario: Content sanitization referenced
        Given the document-conversion SKILL.md
        When searching for sanitization
        Then content-sanitization should be referenced.
        """
        content = SKILL_FILE.read_text()
        assert "content-sanitization" in content

    @pytest.mark.bdd
    def test_fallback_tiers_module_covers_formats(self) -> None:
        """Scenario: Fallback tiers module covers key formats
        Given the fallback-tiers module
        When reading its content
        Then it should cover PDF, HTML, and image fallbacks.
        """
        content = (MODULES_DIR / "fallback-tiers.md").read_text()
        assert "PDF" in content or "pdf" in content
        assert "HTML" in content or "html" in content
        assert "Image" in content or "image" in content


class TestPluginRegistration:
    """Feature: Skill registered in plugin.json.

    As a plugin system
    I want document-conversion to appear in the skills array
    So that it is discovered and loaded automatically
    """

    @pytest.mark.bdd
    def test_registered_in_plugin_json(self) -> None:
        """Scenario: Skill appears in plugin.json
        Given the leyline plugin.json
        When reading the skills array
        Then './skills/document-conversion' should be listed.
        """
        plugin_data = json.loads(PLUGIN_JSON.read_text())
        skills = plugin_data.get("skills", [])
        assert "./skills/document-conversion" in skills
