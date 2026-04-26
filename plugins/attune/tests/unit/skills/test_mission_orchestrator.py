"""BDD tests for attune mission-orchestrator skill structure.

Feature: Mission Orchestrator Skill Validation
  As a plugin developer
  I want the mission-orchestrator skill to follow ecosystem conventions
  So that the unified lifecycle orchestrator integrates correctly
  with the attune plugin system
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "mission-orchestrator"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

EXPECTED_MODULES = [
    "mission-types.md",
    "state-detection.md",
    "phase-routing.md",
    "mission-state.md",
    "plan-review.md",
    "plan-versioner.md",
    "feedback-collector.md",
    "context-injector.md",
    "iteration-governor.md",
    "reflexion-buffer.md",
    "trust-tier.md",
    "adaptive-constraints.md",
]

REQUIRED_SECTIONS = [
    "## Overview",
    "## When To Use",
    "## Exit Criteria",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestMissionOrchestratorSkillFile:
    """
    Feature: Skill file existence and readability

    As a plugin validator
    I want the mission-orchestrator SKILL.md to exist and be readable
    So that the skill can be discovered and loaded by the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the attune plugin
        When checking for mission-orchestrator skill
        Then SKILL.md should exist on disk
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_file_is_readable(self) -> None:
        """Scenario: Skill file readable
        Given the mission-orchestrator SKILL.md exists
        When reading the file
        Then it should return non-empty content
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"
        content = SKILL_FILE.read_text()
        assert len(content) > 0, "SKILL.md is empty"


class TestMissionOrchestratorFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the mission-orchestrator frontmatter to contain required fields
    So that the skill is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_name(self) -> None:
        """Scenario: Name field present
        Given the mission-orchestrator SKILL.md
        When parsing frontmatter
        Then the name field should equal 'mission-orchestrator'
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "mission-orchestrator", (
            f"Expected name='mission-orchestrator', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present and non-trivial
        Given the mission-orchestrator SKILL.md
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
        Given the mission-orchestrator SKILL.md
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
        Given the mission-orchestrator SKILL.md frontmatter
        When checking the modules list
        Then all four lifecycle modules should be declared
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
    def test_frontmatter_category_is_workflow(self) -> None:
        """Scenario: Category reflects workflow orchestration purpose
        Given the mission-orchestrator SKILL.md
        When parsing the category field
        Then it should indicate a workflow or orchestration category
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"
        assert (
            "workflow" in fm["category"].lower()
            or "orchestrat" in fm["category"].lower()
        ), f"Expected workflow/orchestration category, got {fm['category']!r}"


class TestMissionOrchestratorSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the mission-orchestrator to contain standard required sections
    So that I can understand when and how to invoke the skill
    """

    @pytest.mark.bdd
    def test_has_overview_section(self) -> None:
        """Scenario: Overview section present
        Given the mission-orchestrator SKILL.md
        When scanning for section headings
        Then an Overview section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## Overview" in content, "Missing required '## Overview' section"

    @pytest.mark.bdd
    def test_has_when_to_use_section(self) -> None:
        """Scenario: When To Use section present
        Given the mission-orchestrator SKILL.md
        When scanning for section headings
        Then a 'When To Use' section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## When To Use" in content, "Missing required '## When To Use' section"

    @pytest.mark.bdd
    def test_has_exit_criteria_section(self) -> None:
        """Scenario: Exit Criteria section present
        Given the mission-orchestrator SKILL.md
        When scanning for section headings
        Then an Exit Criteria section should exist
        """
        content = SKILL_FILE.read_text()
        assert "## Exit Criteria" in content, (
            "Missing required '## Exit Criteria' section"
        )


class TestMissionOrchestratorModules:
    """
    Feature: Module files exist on disk

    As a skill consumer
    I want all modules declared in the skill to exist on disk
    So that the progressive loading system can load them on demand
    """

    @pytest.mark.bdd
    def test_all_modules_exist(self) -> None:
        """Scenario: All declared modules are present
        Given the mission-orchestrator skill directory
        When checking each declared module file
        Then every module should exist on disk
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module '{module_name}' not found at {module_path}"
            )

    @pytest.mark.bdd
    def test_modules_dir_exists(self) -> None:
        """Scenario: Modules directory present
        Given the mission-orchestrator skill
        When checking for the modules subdirectory
        Then the directory should exist
        """
        assert MODULES_DIR.exists(), f"modules/ directory not found at {MODULES_DIR}"

    @pytest.mark.bdd
    def test_mission_types_module_documents_mission_types(self) -> None:
        """Scenario: mission-types module documents recognized mission types
        Given the mission-types.md module
        When reading content
        Then the four auto-detectable mission types should be documented
        """
        module_path = MODULES_DIR / "mission-types.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        for mission_type in ["full", "standard", "tactical", "quickfix"]:
            assert mission_type in content, (
                f"Mission type '{mission_type}' not documented in mission-types.md"
            )

    @pytest.mark.bdd
    def test_state_detection_module_references_artifacts(self) -> None:
        """Scenario: state-detection module covers known artifact files
        Given the state-detection.md module
        When reading content
        Then it should reference at least one known project artifact filename
        """
        module_path = MODULES_DIR / "state-detection.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        known_artifacts = [
            "project-brief.md",
            "specification.md",
            "implementation-plan.md",
        ]
        found = any(artifact in content for artifact in known_artifacts)
        assert found, (
            "state-detection.md does not reference any known project artifact files"
        )

    @pytest.mark.bdd
    def test_phase_routing_module_references_phases(self) -> None:
        """Scenario: phase-routing module covers the core lifecycle phases
        Given the phase-routing.md module
        When reading content
        Then at least three of the four lifecycle phase names should appear
        """
        module_path = MODULES_DIR / "phase-routing.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        phases = ["brainstorm", "specify", "plan", "execute"]
        found_count = sum(1 for phase in phases if phase in content.lower())
        assert found_count >= 3, (
            f"phase-routing.md only documents {found_count}/4 lifecycle phases"
        )

    @pytest.mark.bdd
    def test_mission_state_module_references_state_file(self) -> None:
        """Scenario: mission-state module documents the state persistence file
        Given the mission-state.md module
        When reading content
        Then it should reference the mission-state.json file
        """
        module_path = MODULES_DIR / "mission-state.md"
        assert module_path.exists(), f"Module not found at {module_path}"
        content = module_path.read_text()
        assert "mission-state.json" in content or "mission_state" in content.lower(), (
            "mission-state.md does not reference the state persistence file"
        )


class TestMissionOrchestratorPluginRegistration:
    """
    Feature: Plugin registry integration

    As the plugin system
    I want mission-orchestrator registered in plugin.json
    So that it is discoverable by consumers
    """

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """Scenario: plugin.json includes mission-orchestrator
        Given the attune plugin.json
        When checking the skills array
        Then mission-orchestrator should be registered
        """
        plugin_json = (
            Path(__file__).resolve().parent.parent.parent.parent
            / ".claude-plugin"
            / "plugin.json"
        )
        assert plugin_json.exists(), f"plugin.json not found at {plugin_json}"
        config = json.loads(plugin_json.read_text())
        skill_paths = config.get("skills", [])
        assert any("mission-orchestrator" in s for s in skill_paths), (
            "mission-orchestrator not registered in plugin.json skills array"
        )


class TestInteractivePlanReview:
    """
    Feature: Interactive plan review modules

    As a mission user
    I want the plan-to-execute transition to include interactive review
    So that plans are scrutinized before execution begins
    """

    @pytest.mark.bdd
    def test_plan_review_module_references_war_room(self) -> None:
        """Scenario: Plan review requires mandatory war-room gate
        Given the plan-review.md module
        When reading content
        Then it should reference the war-room as a mandatory gate
        """
        content = (MODULES_DIR / "plan-review.md").read_text()
        assert "war" in content.lower() and "room" in content.lower(), (
            "plan-review.md must reference the war-room gate"
        )
        assert "mandatory" in content.lower(), (
            "plan-review.md must describe the war-room gate as mandatory"
        )

    @pytest.mark.bdd
    def test_plan_review_module_references_bias_defense(self) -> None:
        """Scenario: Plan review integrates additive bias scanning
        Given the plan-review.md module
        When reading content
        Then it should reference additive-bias-defense
        """
        content = (MODULES_DIR / "plan-review.md").read_text()
        assert "additive-bias-defense" in content, (
            "plan-review.md must reference leyline:additive-bias-defense"
        )

    @pytest.mark.bdd
    def test_feedback_collector_defines_verdict_types(self) -> None:
        """Scenario: Feedback collector defines all three verdict types
        Given the feedback-collector.md module
        When reading content
        Then approve, revise, and reject verdicts should be documented
        """
        content = (MODULES_DIR / "feedback-collector.md").read_text()
        for verdict in ["approve", "revise", "reject"]:
            assert verdict in content.lower(), (
                f"feedback-collector.md must document '{verdict}' verdict"
            )

    @pytest.mark.bdd
    def test_iteration_governor_enforces_cap(self) -> None:
        """Scenario: Iteration governor enforces 3-round cap
        Given the iteration-governor.md module
        When reading content
        Then it should document a maximum of 3 rounds
        """
        content = (MODULES_DIR / "iteration-governor.md").read_text()
        assert "3" in content, "iteration-governor.md must reference the 3-round cap"
        assert "escalat" in content.lower(), (
            "iteration-governor.md must document escalation behavior"
        )

    @pytest.mark.bdd
    def test_context_injector_never_modifies_plan(self) -> None:
        """Scenario: Context injector is read-only on plans
        Given the context-injector.md module
        When reading content
        Then it should state it never modifies the plan directly
        """
        content = (MODULES_DIR / "context-injector.md").read_text()
        assert "never" in content.lower() and "modif" in content.lower(), (
            "context-injector.md must state it never modifies the plan"
        )

    @pytest.mark.bdd
    def test_plan_versioner_uses_attune_directory(self) -> None:
        """Scenario: Plan versioner stores versions in .attune/
        Given the plan-versioner.md module
        When reading content
        Then it should reference the .attune/plan-history/ path
        """
        content = (MODULES_DIR / "plan-versioner.md").read_text()
        assert ".attune/plan-history/" in content, (
            "plan-versioner.md must reference .attune/plan-history/"
        )

    @pytest.mark.bdd
    def test_phase_routing_references_review_loop(self) -> None:
        """Scenario: Phase routing wires in the interactive review loop
        Given the phase-routing.md module
        When reading content
        Then the plan-to-execute transition should reference the review loop
        """
        content = (MODULES_DIR / "phase-routing.md").read_text()
        assert "interactive review loop" in content.lower(), (
            "phase-routing.md must reference 'Interactive Review Loop'"
        )

    @pytest.mark.bdd
    def test_mission_state_includes_plan_review_schema(self) -> None:
        """Scenario: Mission state defines plan_review object
        Given the mission-state.md module
        When reading content
        Then it should define the plan_review state schema
        """
        content = (MODULES_DIR / "mission-state.md").read_text()
        assert "plan_review" in content, (
            "mission-state.md must define the plan_review schema"
        )

    @pytest.mark.bdd
    def test_orchestrator_skill_declares_version_1_9(self) -> None:
        """Scenario: Orchestrator skill version is 1.9.0
        Given the mission-orchestrator SKILL.md
        When parsing frontmatter
        Then version should be 1.9.0
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("version") == "1.9.0", (
            f"Expected version='1.9.0', got {fm.get('version')!r}"
        )

    @pytest.mark.bdd
    def test_orchestrator_depends_on_bias_defense(self) -> None:
        """Scenario: Orchestrator declares additive-bias-defense dependency
        Given the mission-orchestrator SKILL.md
        When parsing frontmatter dependencies
        Then leyline:additive-bias-defense should be listed
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        deps = fm.get("dependencies", [])
        assert "leyline:additive-bias-defense" in deps, (
            "mission-orchestrator must depend on leyline:additive-bias-defense"
        )

    @pytest.mark.bdd
    def test_adaptive_constraints_documents_user_directive_override(
        self,
    ) -> None:
        """Scenario: Adaptive constraints documents directive override
        Given the adaptive-constraints.md module
        When reading content
        Then it should document the User Directive Override parsing table
        with at least the canonical trust-signal phrases.
        """
        content = (MODULES_DIR / "adaptive-constraints.md").read_text()
        assert "User Directive Override" in content, (
            "adaptive-constraints.md must document the User Directive "
            "Override section so natural-language trust signals are "
            "recognized without requiring --constraints= flags."
        )
        for phrase in (
            "ignore scope guard",
            "ultrathink",
            "stop asking",
            "be autonomous",
        ):
            assert phrase in content, (
                f"directive override table must include phrase: {phrase!r}"
            )

    @pytest.mark.bdd
    def test_skill_md_references_user_directive_overrides(self) -> None:
        """Scenario: SKILL.md surfaces directive override capability
        Given the mission-orchestrator SKILL.md
        When reading content
        Then it should reference User Directive Overrides so a reader
        landing on the SKILL.md alone learns the natural-language path
        before drilling into modules.
        """
        content = SKILL_FILE.read_text()
        assert "User Directive Override" in content, (
            "SKILL.md must surface User Directive Overrides at the "
            "skill index level, not bury them only in adaptive-constraints"
        )
