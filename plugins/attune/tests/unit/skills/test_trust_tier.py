"""BDD tests for attune mission-orchestrator trust-tier module.

Feature: Trust Tier Module Validation
  As a plugin developer
  I want the trust-tier module to follow ecosystem conventions
  So that progressive autonomy integrates correctly
  with the mission-orchestrator checkpoint system
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

MODULE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "mission-orchestrator"
    / "modules"
)
MODULE_FILE = MODULE_DIR / "trust-tier.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestTrustTierFileExistence:
    """
    Feature: Module file existence and readability

    As a plugin validator
    I want the trust-tier module to exist and be readable
    So that the orchestrator can load it on demand
    """

    @pytest.mark.bdd
    def test_module_file_exists(self) -> None:
        """Scenario: Module file present
        Given the mission-orchestrator skill
        When checking for trust-tier module
        Then trust-tier.md should exist on disk
        """
        assert MODULE_FILE.exists(), f"trust-tier.md not found at {MODULE_FILE}"

    @pytest.mark.bdd
    def test_module_file_is_readable(self) -> None:
        """Scenario: Module file readable
        Given the trust-tier.md exists
        When reading the file
        Then it should return non-empty content
        """
        content = MODULE_FILE.read_text()
        assert len(content) > 0, "trust-tier.md is empty"


class TestTrustTierFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the trust-tier frontmatter to contain required fields
    So that the module is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_correct_name(self) -> None:
        """Scenario: Name field matches module identity
        Given the trust-tier.md module
        When parsing frontmatter
        Then the name field should equal 'trust-tier'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "trust-tier", (
            f"Expected name='trust-tier', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_parent_skill(self) -> None:
        """Scenario: Parent skill declared
        Given the trust-tier.md module
        When parsing frontmatter
        Then parent_skill should be 'attune:mission-orchestrator'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("parent_skill") == "attune:mission-orchestrator", (
            f"Expected parent_skill='attune:mission-orchestrator', "
            f"got {fm.get('parent_skill')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_estimated_tokens(self) -> None:
        """Scenario: Token estimate present
        Given the trust-tier.md module
        When parsing frontmatter
        Then the estimated_tokens field should be a positive integer
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "estimated_tokens" in fm, "Frontmatter missing 'estimated_tokens' field"
        assert isinstance(fm["estimated_tokens"], int), (
            "estimated_tokens must be an integer"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present
        Given the trust-tier.md module
        When parsing frontmatter
        Then a description field should exist with meaningful content
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description'"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"


class TestTrustTierRequiredSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the trust-tier to contain all required sections
    So that the tier system and transitions are documented
    """

    @pytest.mark.bdd
    def test_has_three_trust_tiers_section(self) -> None:
        """Scenario: Three Trust Tiers section present
        Given the trust-tier.md module
        When scanning for section headings
        Then a Three Trust Tiers section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Three Trust Tiers" in content, (
            "Missing required '## Three Trust Tiers' section"
        )

    @pytest.mark.bdd
    def test_has_trust_score_tracking_section(self) -> None:
        """Scenario: Trust Score Tracking section present
        Given the trust-tier.md module
        When scanning for section headings
        Then a Trust Score Tracking section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Trust Score Tracking" in content, (
            "Missing '## Trust Score Tracking' section"
        )

    @pytest.mark.bdd
    def test_has_tier_transitions_section(self) -> None:
        """Scenario: Tier Transitions section present
        Given the trust-tier.md module
        When scanning for section headings
        Then a Tier Transitions section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Tier Transitions" in content, "Missing '## Tier Transitions' section"

    @pytest.mark.bdd
    def test_has_checkpoint_reduction_section(self) -> None:
        """Scenario: Checkpoint Reduction section present
        Given the trust-tier.md module
        When scanning for section headings
        Then a Checkpoint Reduction section should exist
        """
        content = MODULE_FILE.read_text()
        assert "Checkpoint Reduction" in content, "Missing Checkpoint Reduction section"

    @pytest.mark.bdd
    def test_has_strategic_interruption_section(self) -> None:
        """Scenario: Strategic Interruption section present
        Given the trust-tier.md module
        When scanning for section headings
        Then a Strategic Interruption section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Strategic Interruption" in content, (
            "Missing '## Strategic Interruption' section"
        )


class TestTrustTierContent:
    """
    Feature: Trust tier content validation

    As a plugin developer
    I want the trust-tier module to document all three tiers
    So that checkpoint behavior is predictable
    """

    @pytest.mark.bdd
    def test_defines_t1_tier(self) -> None:
        """Scenario: T1 Supervised tier defined
        Given the trust-tier.md module
        When scanning content
        Then T1 (Supervised) tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "T1" in content, "trust-tier.md must define T1 tier"
        assert "Supervised" in content, "trust-tier.md must label T1 as Supervised"

    @pytest.mark.bdd
    def test_defines_t2_tier(self) -> None:
        """Scenario: T2 Guided tier defined
        Given the trust-tier.md module
        When scanning content
        Then T2 (Guided) tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "T2" in content, "trust-tier.md must define T2 tier"
        assert "Guided" in content, "trust-tier.md must label T2 as Guided"

    @pytest.mark.bdd
    def test_defines_t3_tier(self) -> None:
        """Scenario: T3 Autonomous tier defined
        Given the trust-tier.md module
        When scanning content
        Then T3 (Autonomous) tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "T3" in content, "trust-tier.md must define T3 tier"
        assert "Autonomous" in content, "trust-tier.md must label T3 as Autonomous"

    @pytest.mark.bdd
    def test_references_trust_scores_json(self) -> None:
        """Scenario: Trust scores storage location documented
        Given the trust-tier.md module
        When scanning content
        Then it should reference .attune/trust-scores.json
        """
        content = MODULE_FILE.read_text()
        assert ".attune/trust-scores.json" in content, (
            "trust-tier.md must reference .attune/trust-scores.json storage"
        )

    @pytest.mark.bdd
    def test_contains_asymmetric_rule(self) -> None:
        """Scenario: Asymmetric promotion/demotion rule documented
        Given the trust-tier.md module
        When scanning content
        Then it should state 5 successes promote and 1 failure demotes
        """
        content = MODULE_FILE.read_text()
        assert "5" in content and "successes" in content.lower(), (
            "trust-tier.md must document the 5-success promotion threshold"
        )
        assert "1" in content and "failure" in content.lower(), (
            "trust-tier.md must document the 1-failure demotion rule"
        )
        # Verify the asymmetric principle is stated
        lower = content.lower()
        assert "earned slowly" in lower or "lost quickly" in lower, (
            "trust-tier.md must state the asymmetric trust principle"
        )


class TestTrustTierLineWrapping:
    """
    Feature: Markdown prose line wrapping

    As a documentation maintainer
    I want prose lines to wrap at 80 characters
    So that git diffs stay clean and reviewable
    """

    @pytest.mark.bdd
    def test_prose_lines_wrap_at_80_chars(self) -> None:
        """Scenario: Prose lines respect 80-char wrap limit
        Given the trust-tier.md module
        When checking line lengths of prose lines
        Then no prose line should exceed 80 characters
        """
        content = MODULE_FILE.read_text()
        in_code_block = False
        in_frontmatter = False
        violations = []

        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            # Skip headings, tables, links, empty lines
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith("|")
                or stripped.startswith("[")
                or stripped.startswith("![")
                or stripped == ""
                or re.match(r"^https?://", stripped)
            ):
                continue
            if len(line) > 80:
                violations.append(f"  Line {i} ({len(line)} chars): {line[:60]}...")

        assert not violations, "Prose lines exceeding 80 chars:\n" + "\n".join(
            violations
        )
