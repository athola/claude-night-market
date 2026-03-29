"""BDD tests for leyline damage-control skill structure.

Feature: Damage Control Skill Validation
  As a plugin developer
  I want the damage-control skill to follow ecosystem conventions
  So that agent recovery protocols integrate correctly with the
  leyline plugin system and downstream orchestrators
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "damage-control"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

EXPECTED_MODULES = [
    "crash-recovery.md",
    "context-overflow.md",
    "merge-conflict-resolution.md",
    "state-reconciliation.md",
]

FAILURE_CLASSES = [
    "crash",
    "context",
    "conflict",
    "state",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestDamageControlSkillFile:
    """Feature: Skill file existence and readability.

    As a plugin validator
    I want the damage-control SKILL.md to exist and be readable
    So that the skill can be discovered and loaded by the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the leyline plugin
        When checking for damage-control skill
        Then SKILL.md should exist on disk.
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_file_is_readable(self) -> None:
        """Scenario: Skill file readable
        Given the damage-control SKILL.md exists
        When reading the file
        Then it should return non-empty content.
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"
        content = SKILL_FILE.read_text()
        assert len(content) > 0, "SKILL.md is empty"


class TestDamageControlFrontmatter:
    """Feature: YAML frontmatter validity.

    As a plugin validator
    I want the damage-control frontmatter to contain required fields
    So that the skill is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_name(self) -> None:
        """Scenario: Name field present
        Given the damage-control SKILL.md
        When parsing frontmatter
        Then the name field should equal 'damage-control'.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "damage-control", (
            f"Expected name='damage-control', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present and non-trivial
        Given the damage-control SKILL.md
        When parsing frontmatter
        Then the description field should be present with meaningful content.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description' field"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"

    @pytest.mark.bdd
    def test_frontmatter_has_version_or_complexity(self) -> None:
        """Scenario: Version marker present
        Given the damage-control SKILL.md
        When parsing frontmatter
        Then either 'version' or 'complexity' should be present
        to establish the skill maturity level.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        has_version = "version" in fm
        has_complexity = "complexity" in fm
        assert has_version or has_complexity, (
            "Frontmatter must have 'version' or 'complexity' field"
        )

    @pytest.mark.bdd
    def test_frontmatter_declares_all_modules(self) -> None:
        """Scenario: Module declarations match expected modules
        Given the damage-control SKILL.md frontmatter
        When checking the modules list
        Then all four recovery modules should be declared.
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
        """Scenario: Category reflects infrastructure purpose
        Given the damage-control SKILL.md
        When parsing the category field
        Then it should indicate an infrastructure or resilience category.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"
        assert fm["category"] in (
            "infrastructure",
            "resilience",
            "recovery",
        ), f"Expected infrastructure/resilience category, got {fm['category']!r}"

    @pytest.mark.bdd
    def test_frontmatter_has_tags(self) -> None:
        """Scenario: Tags field is present and non-empty
        Given the damage-control SKILL.md
        When parsing frontmatter
        Then tags should be a non-empty list.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "tags" in fm, "Frontmatter missing 'tags' field"
        assert isinstance(fm["tags"], list), "tags must be a list"
        assert len(fm["tags"]) > 0, "tags list must not be empty"


class TestDamageControlSections:
    """Feature: Required documentation sections.

    As a skill consumer
    I want damage-control to contain standard required sections
    So that I can understand when and how to invoke the skill
    """

    @pytest.mark.bdd
    def test_has_overview_section(self) -> None:
        """Scenario: Overview section present
        Given the damage-control SKILL.md
        When scanning for section headings
        Then an Overview section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## Overview" in content, "Missing required '## Overview' section"

    @pytest.mark.bdd
    def test_has_when_to_use_section(self) -> None:
        """Scenario: When to Use section present
        Given the damage-control SKILL.md
        When scanning for section headings
        Then a 'When to Use' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## When To Use" in content, "Missing required '## When To Use' section"

    @pytest.mark.bdd
    def test_has_exit_criteria_section(self) -> None:
        """Scenario: Exit Criteria section present
        Given the damage-control SKILL.md
        When scanning for section headings
        Then an Exit Criteria section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## Exit Criteria" in content, (
            "Missing required '## Exit Criteria' section"
        )

    @pytest.mark.bdd
    def test_has_triage_or_decision_tree(self) -> None:
        """Scenario: Triage or decision mechanism documented
        Given the damage-control SKILL.md
        When scanning for triage or routing content
        Then the skill should describe how to pick the right module.
        """
        content = SKILL_FILE.read_text()
        content_lower = content.lower()
        assert "triage" in content_lower or "decision" in content_lower, (
            "SKILL.md must document a triage or decision mechanism"
        )

    @pytest.mark.bdd
    def test_references_all_four_failure_classes(self) -> None:
        """Scenario: All failure classes are referenced
        Given the damage-control SKILL.md
        When scanning for failure class keywords
        Then crash, context, conflict, and state recovery must appear.
        """
        content = SKILL_FILE.read_text().lower()
        for keyword in FAILURE_CLASSES:
            assert keyword in content, (
                f"Failure class keyword '{keyword}' not found in SKILL.md"
            )


class TestDamageControlModules:
    """Feature: Module files exist on disk.

    As a skill consumer
    I want all modules declared in the skill to exist on disk
    So that the progressive loading system can load them on demand
    """

    @pytest.mark.bdd
    def test_modules_dir_exists(self) -> None:
        """Scenario: Modules directory present
        Given the damage-control skill
        When checking for the modules subdirectory
        Then the directory should exist.
        """
        assert MODULES_DIR.exists(), f"modules/ directory not found at {MODULES_DIR}"

    @pytest.mark.bdd
    def test_all_modules_exist(self) -> None:
        """Scenario: All declared modules are present on disk
        Given the damage-control skill directory
        When checking each declared module file
        Then every module should exist on disk.
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )

    @pytest.mark.bdd
    def test_each_module_has_exit_criteria(self) -> None:
        """Scenario: All modules define exit criteria
        Given each damage-control module
        When reading its content
        Then it should contain an Exit Criteria section.
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )
            content = module_path.read_text()
            assert "Exit Criteria" in content, (
                f"Module '{module_name}' is missing an 'Exit Criteria' section"
            )

    @pytest.mark.bdd
    def test_each_module_has_frontmatter(self) -> None:
        """Scenario: All modules have YAML frontmatter
        Given each damage-control module
        When reading the file header
        Then it should begin with valid YAML frontmatter.
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )
            content = module_path.read_text()
            assert content.startswith("---"), (
                f"Module '{module_name}' is missing YAML frontmatter"
            )

    @pytest.mark.bdd
    def test_each_module_declares_parent_skill(self) -> None:
        """Scenario: All modules reference their parent skill
        Given each damage-control module
        When parsing frontmatter
        Then parent_skill should be 'leyline:damage-control'.
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )
            content = module_path.read_text()
            fm = _parse_frontmatter(content)
            assert fm.get("parent_skill") == "leyline:damage-control", (
                f"Module '{module_name}' parent_skill should be "
                f"'leyline:damage-control', got {fm.get('parent_skill')!r}"
            )

    @pytest.mark.bdd
    def test_crash_recovery_module_is_non_empty(self) -> None:
        """Scenario: crash-recovery module has meaningful content
        Given the crash-recovery.md module
        When reading content
        Then it should describe crash recovery steps.
        """
        module_path = MODULES_DIR / "crash-recovery.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        content_lower = content.lower()
        assert "crash" in content_lower or "recover" in content_lower, (
            "crash-recovery.md does not document crash or recovery procedures"
        )

    @pytest.mark.bdd
    def test_context_overflow_module_covers_context(self) -> None:
        """Scenario: context-overflow module addresses context loss
        Given the context-overflow.md module
        When reading content
        Then it should describe how to handle context window exhaustion.
        """
        module_path = MODULES_DIR / "context-overflow.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        content_lower = content.lower()
        assert "context" in content_lower, (
            "context-overflow.md does not address context window handling"
        )

    @pytest.mark.bdd
    def test_merge_conflict_module_references_git(self) -> None:
        """Scenario: merge-conflict-resolution module references git
        Given the merge-conflict-resolution.md module
        When reading content
        Then it should mention git conflict resolution.
        """
        module_path = MODULES_DIR / "merge-conflict-resolution.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        content_lower = content.lower()
        assert "conflict" in content_lower or "git" in content_lower, (
            "merge-conflict-resolution.md does not reference git conflicts"
        )

    @pytest.mark.bdd
    def test_state_reconciliation_module_covers_reconciliation(self) -> None:
        """Scenario: state-reconciliation module addresses state divergence
        Given the state-reconciliation.md module
        When reading content
        Then it should describe how to reconcile divergent state.
        """
        module_path = MODULES_DIR / "state-reconciliation.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        content_lower = content.lower()
        assert "reconcil" in content_lower or "state" in content_lower, (
            "state-reconciliation.md does not describe state reconciliation"
        )


class TestDamageControlPluginRegistration:
    """Feature: Plugin registry integration.

    As the plugin system
    I want damage-control registered in plugin.json
    So that it is discoverable by consumers
    """

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """Scenario: plugin.json includes damage-control
        Given the leyline plugin.json
        When checking the skills array
        Then damage-control should be registered.
        """
        plugin_json = (
            Path(__file__).resolve().parent.parent.parent.parent
            / ".claude-plugin"
            / "plugin.json"
        )
        assert plugin_json.exists(), f"plugin.json not found at {plugin_json}"
        config = json.loads(plugin_json.read_text())
        skill_paths = config.get("skills", [])
        assert any("damage-control" in s for s in skill_paths), (
            "damage-control not registered in plugin.json skills array"
        )
