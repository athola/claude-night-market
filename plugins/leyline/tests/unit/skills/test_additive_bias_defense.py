"""BDD tests for leyline additive-bias-defense skill structure.

Feature: Additive Bias Defense Skill Validation
  As a plugin developer
  I want the additive-bias-defense skill to follow ecosystem conventions
  So that review-oriented skills can correctly consult the contract
  and enforce burden-of-proof scrutiny on code additions
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "additive-bias-defense"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"

REQUIRED_SCRUTINY_KEYWORDS = [
    "priority",
    "criticality",
    "simplicity",
    "evidence",
    "consequence",
]

REQUIRED_ANTI_PATTERNS = [
    "wheel reinvention",
    "hallucinated",
    "test manipulation",
    "complexity creep",
    "priority deviation",
    "gold plating",
]

EXPECTED_CONSUMING_SKILLS = [
    "attune:war-room",
    "sanctum:pr-review",
    "pensive:code-refinement",
    "conserve:unbloat",
    "attune:mission-orchestrator",
    "imbue:justify",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestAdditiveBiasDefenseSkillFile:
    """Feature: Skill file existence and readability.

    As a plugin validator
    I want the additive-bias-defense SKILL.md to exist and be readable
    So that the skill can be discovered and loaded by the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the leyline plugin
        When checking for additive-bias-defense skill
        Then SKILL.md should exist on disk.
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_skill_file_is_readable(self) -> None:
        """Scenario: Skill file readable
        Given the additive-bias-defense SKILL.md exists
        When reading the file
        Then it should return non-empty content.
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"
        content = SKILL_FILE.read_text()
        assert len(content) > 0, "SKILL.md is empty"


class TestAdditiveBiasDefenseFrontmatter:
    """Feature: YAML frontmatter validity.

    As a plugin validator
    I want the additive-bias-defense frontmatter to contain required fields
    So that the skill is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_name(self) -> None:
        """Scenario: Name field present
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then the name field should equal 'additive-bias-defense'.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "additive-bias-defense", (
            f"Expected name='additive-bias-defense', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present and non-trivial
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then the description field should be present with meaningful content.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description' field"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"

    @pytest.mark.bdd
    def test_frontmatter_has_version(self) -> None:
        """Scenario: Version field present
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then a 'version' field should be present.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "version" in fm, "Frontmatter missing 'version' field"

    @pytest.mark.bdd
    def test_frontmatter_category_is_quality_contract(self) -> None:
        """Scenario: Category reflects quality-contract purpose
        Given the additive-bias-defense SKILL.md
        When parsing the category field
        Then it should be 'quality-contract'.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"
        assert fm["category"] == "quality-contract", (
            f"Expected category='quality-contract', got {fm['category']!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_tags(self) -> None:
        """Scenario: Tags field is present and includes relevant keywords
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then tags should include 'additive-bias' and 'burden-of-proof'.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "tags" in fm, "Frontmatter missing 'tags' field"
        assert isinstance(fm["tags"], list), "tags must be a list"
        assert "additive-bias" in fm["tags"], "tags must include 'additive-bias'"
        assert "burden-of-proof" in fm["tags"], "tags must include 'burden-of-proof'"

    @pytest.mark.bdd
    def test_frontmatter_declares_provides_contract(self) -> None:
        """Scenario: Provides contract declarations present
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then provides.contract should include scrutiny and verdict entries.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "provides" in fm, "Frontmatter missing 'provides' field"
        contract = fm["provides"].get("contract", [])
        assert "additive-bias-scrutiny" in contract, (
            "provides.contract must include 'additive-bias-scrutiny'"
        )
        assert "burden-of-proof-verdict" in contract, (
            "provides.contract must include 'burden-of-proof-verdict'"
        )

    @pytest.mark.bdd
    def test_frontmatter_complexity_is_foundational(self) -> None:
        """Scenario: Complexity set to foundational
        Given the additive-bias-defense SKILL.md
        When parsing frontmatter
        Then complexity should be 'foundational'.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("complexity") == "foundational", (
            f"Expected complexity='foundational', got {fm.get('complexity')!r}"
        )


class TestAdditiveBiasDefenseSections:
    """Feature: Required documentation sections.

    As a skill consumer
    I want additive-bias-defense to contain standard required sections
    So that I can understand when and how to invoke the contract
    """

    @pytest.mark.bdd
    def test_has_the_problem_section(self) -> None:
        """Scenario: Problem section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then a 'The Problem' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## The Problem" in content, "Missing required '## The Problem' section"

    @pytest.mark.bdd
    def test_has_scrutiny_questions_section(self) -> None:
        """Scenario: Scrutiny questions section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then a 'The Scrutiny Questions' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## The Scrutiny Questions" in content, (
            "Missing required '## The Scrutiny Questions' section"
        )

    @pytest.mark.bdd
    def test_has_anti_pattern_detection_section(self) -> None:
        """Scenario: Anti-pattern detection section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then an 'Anti-Pattern Detection' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## Anti-Pattern Detection" in content, (
            "Missing required '## Anti-Pattern Detection' section"
        )

    @pytest.mark.bdd
    def test_has_burden_of_proof_verdict_section(self) -> None:
        """Scenario: Burden of Proof Verdict section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then a 'Burden of Proof Verdict' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## Burden of Proof Verdict" in content, (
            "Missing required '## Burden of Proof Verdict' section"
        )

    @pytest.mark.bdd
    def test_has_integration_contract_section(self) -> None:
        """Scenario: Integration contract section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then an 'Integration Contract' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## Integration Contract" in content, (
            "Missing required '## Integration Contract' section"
        )

    @pytest.mark.bdd
    def test_has_subtraction_principle_section(self) -> None:
        """Scenario: Subtraction principle section present
        Given the additive-bias-defense SKILL.md
        When scanning for section headings
        Then 'The Subtraction Principle' section should exist.
        """
        content = SKILL_FILE.read_text()
        assert "## The Subtraction Principle" in content, (
            "Missing required '## The Subtraction Principle' section"
        )


class TestAdditiveBiasDefenseScrutinyQuestions:
    """Feature: Five scrutiny questions are documented.

    As a review-oriented skill
    I want all five scrutiny questions to be present
    So that I can apply the complete burden-of-proof protocol
    """

    @pytest.mark.bdd
    def test_all_five_scrutiny_keywords_present(self) -> None:
        """Scenario: All scrutiny question topics covered
        Given the additive-bias-defense SKILL.md
        When scanning for scrutiny question keywords
        Then priority, criticality, simplicity, evidence, and consequence
        must all appear in the document.
        """
        content = SKILL_FILE.read_text().lower()
        for keyword in REQUIRED_SCRUTINY_KEYWORDS:
            assert keyword in content, (
                f"Scrutiny keyword '{keyword}' not found in SKILL.md"
            )

    @pytest.mark.bdd
    def test_evidence_and_consequence_are_gatekeepers(self) -> None:
        """Scenario: Evidence and consequence questions are the hard gates
        Given the additive-bias-defense SKILL.md
        When reading the scrutiny questions section
        Then questions 4 (evidence) and 5 (consequence) should be explicitly
        identified as the gatekeepers for unjustified additions.
        """
        content = SKILL_FILE.read_text()
        assert "4" in content and "5" in content, (
            "Questions 4 and 5 must be explicitly numbered in the scrutiny list"
        )
        content_lower = content.lower()
        assert "unjustified" in content_lower, (
            "SKILL.md must use the term 'unjustified' to describe additions "
            "that fail the evidence/consequence gate"
        )


class TestAdditiveBiasDefenseAntiPatterns:
    """Feature: Six anti-patterns are documented in a detection table.

    As a review-oriented skill
    I want all six anti-patterns tabulated with signals and challenges
    So that I can apply systematic detection during reviews
    """

    @pytest.mark.bdd
    def test_all_six_anti_patterns_present(self) -> None:
        """Scenario: All anti-pattern labels present in the document
        Given the additive-bias-defense SKILL.md
        When scanning for anti-pattern keywords
        Then all six anti-patterns should be documented.
        """
        content = SKILL_FILE.read_text().lower()
        for pattern in REQUIRED_ANTI_PATTERNS:
            assert pattern in content, f"Anti-pattern '{pattern}' not found in SKILL.md"


class TestAdditiveBiasDefenseBurdenOfProofVerdicts:
    """Feature: Three verdict states are documented.

    As a review-oriented skill
    I want the three verdict states to be present with clear meanings
    So that I can produce machine-readable verdicts in my output
    """

    @pytest.mark.bdd
    def test_justified_verdict_present(self) -> None:
        """Scenario: justified verdict documented
        Given the additive-bias-defense SKILL.md
        When scanning for verdict states
        Then 'justified' should appear as a verdict option.
        """
        content = SKILL_FILE.read_text()
        assert "`justified`" in content, (
            "Verdict state '`justified`' not found in SKILL.md"
        )

    @pytest.mark.bdd
    def test_needs_evidence_verdict_present(self) -> None:
        """Scenario: needs_evidence verdict documented
        Given the additive-bias-defense SKILL.md
        When scanning for verdict states
        Then 'needs_evidence' should appear as a verdict option.
        """
        content = SKILL_FILE.read_text()
        assert "`needs_evidence`" in content, (
            "Verdict state '`needs_evidence`' not found in SKILL.md"
        )

    @pytest.mark.bdd
    def test_unjustified_verdict_present(self) -> None:
        """Scenario: unjustified verdict documented
        Given the additive-bias-defense SKILL.md
        When scanning for verdict states
        Then 'unjustified' should appear as a verdict option.
        """
        content = SKILL_FILE.read_text()
        assert "`unjustified`" in content, (
            "Verdict state '`unjustified`' not found in SKILL.md"
        )


class TestAdditiveBiasDefenseConsumingSkills:
    """Feature: Consuming skills are listed in the integration contract.

    As a plugin ecosystem maintainer
    I want the consuming skills to be explicitly named
    So that downstream integrations can be audited
    """

    @pytest.mark.bdd
    def test_all_consuming_skills_referenced(self) -> None:
        """Scenario: Expected consuming skills are listed
        Given the additive-bias-defense SKILL.md
        When scanning the Integration Contract section
        Then attune:war-room, sanctum:pr-review, pensive:code-refinement,
        and conserve:unbloat should all be referenced.
        """
        content = SKILL_FILE.read_text()
        for skill_ref in EXPECTED_CONSUMING_SKILLS:
            assert skill_ref in content, (
                f"Consuming skill '{skill_ref}' not referenced in SKILL.md"
            )


class TestAdditiveBiasDefensePluginRegistration:
    """Feature: Plugin registry integration.

    As the plugin system
    I want additive-bias-defense registered in plugin.json
    So that it is discoverable by consumers
    """

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """Scenario: plugin.json includes additive-bias-defense
        Given the leyline plugin.json
        When checking the skills array
        Then additive-bias-defense should be registered.
        """
        plugin_json = (
            Path(__file__).resolve().parent.parent.parent.parent
            / ".claude-plugin"
            / "plugin.json"
        )
        assert plugin_json.exists(), f"plugin.json not found at {plugin_json}"
        config = json.loads(plugin_json.read_text())
        skill_paths = config.get("skills", [])
        assert any("additive-bias-defense" in s for s in skill_paths), (
            "additive-bias-defense not registered in plugin.json skills array"
        )
