"""BDD tests for leyline risk-classification skill structure.

Feature: Risk Classification Skill Validation
  As a plugin developer
  I want the risk-classification skill to follow ecosystem conventions
  So that the 4-tier risk model integrates correctly with the leyline
  plugin system and downstream orchestrators
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "risk-classification"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

EXPECTED_MODULES = [
    "tier-definitions.md",
    "heuristic-classifier.md",
    "verification-gates.md",
]

RISK_TIERS = ["GREEN", "YELLOW", "RED", "CRITICAL"]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestRiskClassificationSkillFile:
    """
    Feature: Skill file existence and readability

    As a plugin validator
    I want the risk-classification SKILL.md to exist and be readable
    So that the skill can be discovered and loaded by the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the leyline plugin
        When checking for risk-classification skill
        Then SKILL.md should exist on disk
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_file_is_readable(self) -> None:
        """Scenario: Skill file readable
        Given the risk-classification SKILL.md exists
        When reading the file
        Then it should return non-empty content
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"
        content = SKILL_FILE.read_text()
        assert len(content) > 0, "SKILL.md is empty"


class TestRiskClassificationFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the risk-classification frontmatter to contain required fields
    So that the skill is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_name(self) -> None:
        """Scenario: Name field present
        Given the risk-classification SKILL.md
        When parsing frontmatter
        Then the name field should equal 'risk-classification'
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "risk-classification", (
            f"Expected name='risk-classification', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present and non-trivial
        Given the risk-classification SKILL.md
        When parsing frontmatter
        Then the description field should be present with meaningful content
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description' field"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"

    @pytest.mark.bdd
    def test_frontmatter_has_version_or_complexity(self) -> None:
        """Scenario: Version marker present
        Given the risk-classification SKILL.md
        When parsing frontmatter
        Then either 'version' or 'complexity' should be present
        to establish the skill maturity level
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        has_version = "version" in fm
        has_complexity = "complexity" in fm
        assert has_version or has_complexity, (
            "Frontmatter must have 'version' or 'complexity' field"
        )

    @pytest.mark.bdd
    def test_frontmatter_declares_modules(self) -> None:
        """Scenario: Module declarations match expected modules
        Given the risk-classification SKILL.md frontmatter
        When checking the modules list
        Then all three classifier modules should be declared
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "modules" in fm, "Frontmatter missing 'modules' field"
        declared = [Path(m).name for m in fm["modules"]]
        for expected in EXPECTED_MODULES:
            assert expected in declared, (
                f"Module '{expected}' not declared in frontmatter modules list"
            )

    @pytest.mark.bdd
    def test_frontmatter_category_is_infrastructure(self) -> None:
        """Scenario: Category reflects infrastructure/safety purpose
        Given the risk-classification SKILL.md
        When parsing the category field
        Then it should indicate an infrastructure or safety category
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"
        assert fm["category"] in (
            "infrastructure",
            "safety",
            "risk-management",
        ), f"Expected infrastructure/safety category, got {fm['category']!r}"


class TestRiskClassificationSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the risk-classification to contain standard required sections
    So that I can understand when and how to invoke the skill
    """

    @pytest.mark.bdd
    def test_has_overview_section(self) -> None:
        """Scenario: Overview section present
        Given the risk-classification SKILL.md
        When scanning for section headings
        Then an Overview section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## Overview" in content, "Missing required '## Overview' section"

    @pytest.mark.bdd
    def test_has_when_to_use_section(self) -> None:
        """Scenario: When To Use section present
        Given the risk-classification SKILL.md
        When scanning for section headings
        Then a 'When To Use' section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## When To Use" in content, "Missing required '## When To Use' section"

    @pytest.mark.bdd
    def test_has_exit_criteria_section(self) -> None:
        """Scenario: Exit Criteria section present
        Given the risk-classification SKILL.md
        When scanning for section headings
        Then an Exit Criteria section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## Exit Criteria" in content, (
            "Missing required '## Exit Criteria' section"
        )

    @pytest.mark.bdd
    def test_documents_all_four_tiers(self) -> None:
        """Scenario: All risk tiers documented in SKILL.md
        Given the risk-classification SKILL.md
        When scanning for tier names
        Then GREEN, YELLOW, RED, and CRITICAL should all appear
        """
        content = SKILL_FILE.read_text()
        for tier in RISK_TIERS:
            assert tier in content, f"Risk tier '{tier}' not documented in SKILL.md"


class TestRiskClassificationModules:
    """
    Feature: Module files exist on disk

    As a skill consumer
    I want all modules declared in the skill to exist on disk
    So that the progressive loading system can load them on demand
    """

    @pytest.mark.bdd
    def test_modules_dir_exists(self) -> None:
        """Scenario: Modules directory present
        Given the risk-classification skill
        When checking for the modules subdirectory
        Then the directory should exist
        """
        assert MODULES_DIR.exists(), f"modules/ directory not found at {MODULES_DIR}"

    @pytest.mark.bdd
    def test_all_modules_exist(self) -> None:
        """Scenario: All declared modules are present on disk
        Given the risk-classification skill directory
        When checking each declared module file
        Then every module should exist on disk
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )

    @pytest.mark.bdd
    def test_tier_definitions_module_documents_all_tiers(self) -> None:
        """Scenario: tier-definitions module covers all risk tiers
        Given the tier-definitions.md module
        When reading content
        Then GREEN, YELLOW, RED, and CRITICAL should all be defined
        """
        module_path = MODULES_DIR / "tier-definitions.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        for tier in RISK_TIERS:
            assert tier in content, (
                f"Risk tier '{tier}' not defined in tier-definitions.md"
            )

    @pytest.mark.bdd
    def test_heuristic_classifier_references_file_patterns(self) -> None:
        """Scenario: heuristic-classifier documents pattern-matching approach
        Given the heuristic-classifier.md module
        When reading content
        Then it should reference file patterns or pattern matching
        """
        module_path = MODULES_DIR / "heuristic-classifier.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        assert "pattern" in content.lower() or "match" in content.lower(), (
            "heuristic-classifier.md does not document file-pattern matching"
        )

    @pytest.mark.bdd
    def test_verification_gates_references_tiers(self) -> None:
        """Scenario: verification-gates module references risk tiers
        Given the verification-gates.md module
        When reading content
        Then at least two risk tier names should appear
        """
        module_path = MODULES_DIR / "verification-gates.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        found_count = sum(1 for tier in RISK_TIERS if tier in content)
        assert found_count >= 2, (
            f"verification-gates.md only references {found_count}/4 risk tiers"
        )


class TestRiskClassificationPluginRegistration:
    """
    Feature: Plugin registry integration

    As the plugin system
    I want risk-classification registered in plugin.json
    So that it is discoverable by consumers
    """

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """Scenario: plugin.json includes risk-classification
        Given the leyline plugin.json
        When checking the skills array
        Then risk-classification should be registered
        """
        plugin_json = (
            Path(__file__).resolve().parent.parent.parent.parent
            / ".claude-plugin"
            / "plugin.json"
        )
        assert plugin_json.exists(), f"plugin.json not found at {plugin_json}"
        config = json.loads(plugin_json.read_text())
        skill_paths = config.get("skills", [])
        assert any("risk-classification" in s for s in skill_paths), (
            "risk-classification not registered in plugin.json skills array"
        )
