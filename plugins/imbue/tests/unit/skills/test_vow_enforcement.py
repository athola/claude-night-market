"""Tests for vow-enforcement skill structure and three-layer enforcement.

Validates that the vow-enforcement SKILL.md defines the three
enforcement layers (soft, hard, Nen Court), vow classification
protocol, graduation criteria, and integration points.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestVowEnforcementSkillStructure:
    """Feature: Vow-enforcement skill has valid structure and frontmatter.

    As a developer designing constraint enforcement
    I want a well-structured vow-enforcement skill
    So that constraints are classified by reliability
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the vow-enforcement skill."""
        return Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Vow-enforcement skill file exists.

        Given the imbue plugin skills directory
        When looking for vow-enforcement
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Skill has complete frontmatter.

        Given the vow-enforcement skill
        When parsing frontmatter
        Then name, description, version, and category should be present
        """
        assert "name: vow-enforcement" in skill_content
        assert "version:" in skill_content
        assert "category:" in skill_content
        assert "description:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_depends_on_proof_of_work(self, skill_content: str) -> None:
        """Scenario: Skill declares proof-of-work dependency.

        Given the vow-enforcement skill
        When checking dependencies
        Then proof-of-work should be listed
        """
        assert "imbue:proof-of-work" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_depends_on_scope_guard(self, skill_content: str) -> None:
        """Scenario: Skill declares scope-guard dependency.

        Given the vow-enforcement skill
        When checking dependencies
        Then scope-guard should be listed
        """
        assert "imbue:scope-guard" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_depends_on_justify(self, skill_content: str) -> None:
        """Scenario: Skill declares justify dependency.

        Given the vow-enforcement skill
        When checking dependencies
        Then justify should be listed
        """
        assert "imbue:justify" in skill_content


class TestThreeEnforcementLayers:
    """Feature: Skill defines three enforcement layers.

    As a developer classifying constraints
    I want clear layer definitions
    So that I pick the right enforcement mechanism
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_three_layers(self, skill_content: str) -> None:
        """Scenario: Skill defines soft, hard, and Nen Court layers.

        Given the vow-enforcement skill
        When reviewing the enforcement layers
        Then soft vow, hard vow, and Nen Court should be defined
        """
        assert "Soft Vow" in skill_content
        assert "Hard Vow" in skill_content
        assert "Nen Court" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_layer_table_includes_compliance_rates(self, skill_content: str) -> None:
        """Scenario: Layer table shows expected compliance rates.

        Given the vow-enforcement skill
        When reviewing the enforcement layer table
        Then compliance rates should be documented for each layer
        """
        assert "~80%" in skill_content
        assert "~100%" in skill_content
        assert "Deterministic" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_soft_vow_describes_mechanism(self, skill_content: str) -> None:
        """Scenario: Soft vow layer describes its mechanism.

        Given the vow-enforcement skill
        When reviewing the soft vow section
        Then skill instructions and CLAUDE.md should be listed
        """
        assert "Skill instructions" in skill_content
        assert "CLAUDE.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hard_vow_describes_mechanism(self, skill_content: str) -> None:
        """Scenario: Hard vow layer describes its mechanism.

        Given the vow-enforcement skill
        When reviewing the hard vow section
        Then hooks and settings.json should be listed
        """
        assert "PreToolUse" in skill_content or "Hook" in skill_content
        assert "settings.json" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_nen_court_describes_mechanism(self, skill_content: str) -> None:
        """Scenario: Nen Court layer describes its mechanism.

        Given the vow-enforcement skill
        When reviewing the Nen Court section
        Then external validator agents should be described
        """
        assert "validator" in skill_content.lower()
        assert "agent" in skill_content.lower()


class TestVowClassificationProtocol:
    """Feature: Skill defines vow classification protocol.

    As a developer adding a new constraint
    I want a clear classification sequence
    So that I start cheap and graduate when needed
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_classification_protocol(self, skill_content: str) -> None:
        """Scenario: Skill defines vow classification protocol.

        Given the vow-enforcement skill
        When reviewing the classification section
        Then a step-by-step protocol should exist
        """
        assert "Vow Classification Protocol" in skill_content
        assert "Step 1" in skill_content
        assert "Step 2" in skill_content
        assert "Step 3" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_starts_as_soft_vow(self, skill_content: str) -> None:
        """Scenario: Protocol starts with soft vow.

        Given the classification protocol
        When reviewing step 1
        Then the default should be soft vow (cheapest path)
        """
        assert "Start as Soft Vow" in skill_content
        assert "cheapest" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_monitors_violation_rate(self, skill_content: str) -> None:
        """Scenario: Protocol monitors violation rate.

        Given the classification protocol
        When reviewing step 2
        Then violation rate monitoring should be described
        """
        assert "Monitor Violation Rate" in skill_content
        assert "violation" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graduates_based_on_threshold(self, skill_content: str) -> None:
        """Scenario: Protocol graduates based on violation threshold.

        Given the classification protocol
        When reviewing step 3
        Then graduation at 20% violation rate should be defined
        """
        assert "Graduate" in skill_content
        assert "20%" in skill_content


class TestNightMarketVowInventory:
    """Feature: Skill classifies existing Night Market constraints.

    As a developer auditing enforcement gaps
    I want current constraints classified by layer
    So that I know which need graduation
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_inventory_exists(self, skill_content: str) -> None:
        """Scenario: Skill has a vow inventory section.

        Given the vow-enforcement skill
        When looking for the inventory
        Then a Night Market Vow Inventory should exist
        """
        assert "Night Market Vow Inventory" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_inventory_classifies_iron_law(self, skill_content: str) -> None:
        """Scenario: Iron Law is classified with target layer.

        Given the vow inventory
        When checking the Iron Law entry
        Then it should be classified as currently soft, target Nen Court
        """
        assert "Iron Law" in skill_content
        assert "Nen Court" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_inventory_classifies_no_verify(self, skill_content: str) -> None:
        """Scenario: No --no-verify is classified as hard.

        Given the vow inventory
        When checking the no-verify entry
        Then it should be classified as already hard
        """
        assert "--no-verify" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_inventory_classifies_bounded_discovery(self, skill_content: str) -> None:
        """Scenario: Bounded discovery reads are classified.

        Given the vow inventory
        When checking the bounded discovery entry
        Then it should be classified with a target layer
        """
        assert "Bounded discovery" in skill_content


class TestVowGraduationCriteria:
    """Feature: Skill defines when vows graduate between layers.

    As a developer maintaining enforcement quality
    I want clear graduation triggers and process
    So that constraints move to harder enforcement when needed
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_graduation_triggers(self, skill_content: str) -> None:
        """Scenario: Skill defines triggers for vow graduation.

        Given the vow-enforcement skill
        When reviewing graduation criteria
        Then frequency, severity, and user escalation should be listed
        """
        assert "Graduation Criteria" in skill_content
        assert "Frequency" in skill_content or "frequency" in skill_content.lower()
        assert "Severity" in skill_content or "severity" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_frequency_threshold(self, skill_content: str) -> None:
        """Scenario: Skill defines a frequency threshold.

        Given the graduation criteria
        When checking the frequency trigger
        Then 3+ violations in 30 days should be the threshold
        """
        assert "3+" in skill_content or "3 " in skill_content
        assert "30 day" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_graduation_process(self, skill_content: str) -> None:
        """Scenario: Skill defines the graduation process.

        Given the graduation criteria
        When reviewing the process
        Then a step-by-step graduation process should exist
        """
        assert "Graduation Process" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_demotion_path(self, skill_content: str) -> None:
        """Scenario: Skill defines demotion for over-aggressive vows.

        Given the graduation criteria
        When reviewing demotion
        Then false positive rate should trigger demotion
        """
        assert "Demotion" in skill_content
        assert "false positive" in skill_content.lower()


class TestNenCourtProtocol:
    """Feature: Skill defines the Nen Court validator protocol.

    As a developer implementing judgment-based constraints
    I want a clear validator agent protocol
    So that phase-gating works with structured verdicts
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_nen_court_protocol(self, skill_content: str) -> None:
        """Scenario: Skill defines the Nen Court protocol.

        Given the vow-enforcement skill
        When reviewing the Nen Court section
        Then a protocol for validator agents should exist
        """
        assert "Nen Court Protocol" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_phase_boundaries(self, skill_content: str) -> None:
        """Scenario: Nen Court runs at phase boundaries.

        Given the Nen Court protocol
        When checking invocation points
        Then specify, plan, execute, and pr-prep should be listed
        """
        assert "specify" in skill_content.lower()
        assert "plan" in skill_content.lower()
        assert "execute" in skill_content.lower()
        assert "pr-prep" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_validator_contract(self, skill_content: str) -> None:
        """Scenario: Nen Court defines validator agent contract.

        Given the Nen Court protocol
        When reviewing the contract
        Then name, constraint, inputs, checks, and output should be defined
        """
        assert "Validator Agent Contract" in skill_content
        assert "constraint:" in skill_content
        assert "checks:" in skill_content
        assert "verdict:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_three_verdicts(self, skill_content: str) -> None:
        """Scenario: Nen Court defines pass, violation, and inconclusive.

        Given the Nen Court protocol
        When reviewing verdicts
        Then pass, violation, and inconclusive should be defined
        """
        assert "pass" in skill_content
        assert "violation" in skill_content
        assert "inconclusive" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_user_override(self, skill_content: str) -> None:
        """Scenario: Nen Court allows user override.

        Given the Nen Court protocol
        When a verdict blocks progress
        Then user override should be possible
        """
        assert "User Override" in skill_content
        assert "override" in skill_content.lower()


class TestIntegrationPoints:
    """Feature: Skill documents integration with other imbue skills.

    As a developer composing enforcement workflows
    I want clear integration points
    So that vow-enforcement connects to the mission lifecycle
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_scope_guard(self, skill_content: str) -> None:
        """Scenario: Skill integrates with scope-guard.

        Given the vow-enforcement skill
        When reviewing integration points
        Then scope-guard integration should be described
        """
        assert "imbue:scope-guard" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_proof_of_work(self, skill_content: str) -> None:
        """Scenario: Skill integrates with proof-of-work.

        Given the vow-enforcement skill
        When reviewing integration points
        Then proof-of-work integration should be described
        """
        assert "imbue:proof-of-work" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_justify(self, skill_content: str) -> None:
        """Scenario: Skill integrates with justify.

        Given the vow-enforcement skill
        When reviewing integration points
        Then justify integration should be described
        """
        assert "imbue:justify" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_mission_orchestrator(self, skill_content: str) -> None:
        """Scenario: Skill integrates with mission orchestrator.

        Given the vow-enforcement skill
        When reviewing integration points
        Then mission orchestrator phase-routing should be described
        """
        assert "Mission Orchestrator" in skill_content
        assert "phase" in skill_content.lower()


class TestResearchBacking:
    """Feature: Skill cites research backing for enforcement layers.

    As a developer evaluating enforcement approaches
    I want the skill grounded in evidence
    So that the three-layer model is justified
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "vow-enforcement" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_odcv_bench(self, skill_content: str) -> None:
        """Scenario: Skill references ODCV-Bench findings.

        Given the vow-enforcement skill
        When reviewing the problem statement
        Then ODCV-Bench constraint violation rates should be cited
        """
        assert "ODCV-Bench" in skill_content
        assert "30-50%" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_settings_firewall_metaphor(self, skill_content: str) -> None:
        """Scenario: Skill references the firewall vs handbook metaphor.

        Given the vow-enforcement skill
        When reviewing the rationale
        Then the settings.json firewall metaphor should be cited
        """
        assert "firewall" in skill_content.lower()
        assert "handbook" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_150_rule_threshold(self, skill_content: str) -> None:
        """Scenario: Skill references the 150-rule compliance drop.

        Given the vow-enforcement skill
        When reviewing the problem statement
        Then the 150 soft rules threshold should be cited
        """
        assert "150" in skill_content
