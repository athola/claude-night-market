"""BDD tests for attune mission-orchestrator adaptive-constraints module.

Feature: Adaptive Constraints Module Validation
  As a plugin developer
  I want the adaptive-constraints module to follow ecosystem conventions
  So that constraint profiles scale governance to task complexity
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
MODULE_FILE = MODULE_DIR / "adaptive-constraints.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestAdaptiveConstraintsFileExistence:
    """
    Feature: Module file existence and readability

    As a plugin validator
    I want the adaptive-constraints module to exist and be readable
    So that the orchestrator can load it on demand
    """

    @pytest.mark.bdd
    def test_module_file_exists(self) -> None:
        """Scenario: Module file present
        Given the mission-orchestrator skill
        When checking for adaptive-constraints module
        Then adaptive-constraints.md should exist on disk
        """
        assert MODULE_FILE.exists(), (
            f"adaptive-constraints.md not found at {MODULE_FILE}"
        )

    @pytest.mark.bdd
    def test_module_file_is_readable(self) -> None:
        """Scenario: Module file readable
        Given the adaptive-constraints.md exists
        When reading the file
        Then it should return non-empty content
        """
        content = MODULE_FILE.read_text()
        assert len(content) > 0, "adaptive-constraints.md is empty"


class TestAdaptiveConstraintsFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the adaptive-constraints frontmatter to contain required fields
    So that the module is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_correct_name(self) -> None:
        """Scenario: Name field matches module identity
        Given the adaptive-constraints.md module
        When parsing frontmatter
        Then the name field should equal 'adaptive-constraints'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "adaptive-constraints", (
            f"Expected name='adaptive-constraints', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_parent_skill(self) -> None:
        """Scenario: Parent skill declared
        Given the adaptive-constraints.md module
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
        Given the adaptive-constraints.md module
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
        Given the adaptive-constraints.md module
        When parsing frontmatter
        Then a description field should exist with meaningful content
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description'"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"


class TestAdaptiveConstraintsRequiredSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the adaptive-constraints to contain all required sections
    So that profiles and safety floors are documented
    """

    @pytest.mark.bdd
    def test_has_constraint_profiles_section(self) -> None:
        """Scenario: Constraint Profiles section present
        Given the adaptive-constraints.md module
        When scanning for section headings
        Then a Constraint Profiles section should exist
        """
        content = MODULE_FILE.read_text()
        assert (
            "Constraint Profiles" in content
            or "## Three Constraint Profiles" in content
        ), "Missing Constraint Profiles section"

    @pytest.mark.bdd
    def test_has_profile_selection_section(self) -> None:
        """Scenario: Profile Selection section present
        Given the adaptive-constraints.md module
        When scanning for section headings
        Then a Profile Selection section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Profile Selection" in content, (
            "Missing '## Profile Selection' section"
        )

    @pytest.mark.bdd
    def test_has_safety_floor_section(self) -> None:
        """Scenario: Safety Floor section present
        Given the adaptive-constraints.md module
        When scanning for section headings
        Then a Safety Floor section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Safety Floor" in content, "Missing '## Safety Floor' section"


class TestAdaptiveConstraintsContent:
    """
    Feature: Adaptive constraints content validation

    As a plugin developer
    I want the module to define all three profiles and safety floor
    So that governance scales correctly with task complexity
    """

    @pytest.mark.bdd
    def test_defines_minimal_profile(self) -> None:
        """Scenario: Minimal profile defined
        Given the adaptive-constraints.md module
        When scanning content
        Then the Minimal constraint profile should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Minimal" in content, (
            "adaptive-constraints.md must define the Minimal profile"
        )

    @pytest.mark.bdd
    def test_defines_standard_profile(self) -> None:
        """Scenario: Standard profile defined
        Given the adaptive-constraints.md module
        When scanning content
        Then the Standard constraint profile should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Standard" in content, (
            "adaptive-constraints.md must define the Standard profile"
        )

    @pytest.mark.bdd
    def test_defines_full_profile(self) -> None:
        """Scenario: Full profile defined
        Given the adaptive-constraints.md module
        When scanning content
        Then the Full constraint profile should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Full" in content, "adaptive-constraints.md must define the Full profile"

    @pytest.mark.bdd
    def test_safety_floor_prevents_no_verify(self) -> None:
        """Scenario: Safety floor prevents --no-verify bypass
        Given the adaptive-constraints.md module
        When scanning the Safety Floor section
        Then pre-commit hooks should be listed as never-stripped
        """
        content = MODULE_FILE.read_text()
        lower = content.lower()
        assert "pre-commit" in lower, "Safety floor must include pre-commit hooks"
        assert "--no-verify" in content, (
            "Safety floor must explicitly mention --no-verify protection"
        )

    @pytest.mark.bdd
    def test_safety_floor_requires_proof_of_work(self) -> None:
        """Scenario: Safety floor requires proof-of-work
        Given the adaptive-constraints.md module
        When scanning the Safety Floor section
        Then proof-of-work evidence should be listed as never-stripped
        """
        content = MODULE_FILE.read_text()
        assert "proof-of-work" in content, (
            "Safety floor must include proof-of-work evidence"
        )

    @pytest.mark.bdd
    def test_safety_floor_blocks_destructive_operations(self) -> None:
        """Scenario: Safety floor blocks destructive operations
        Given the adaptive-constraints.md module
        When scanning the Safety Floor section
        Then destructive operation confirmation should be required
        """
        content = MODULE_FILE.read_text()
        lower = content.lower()
        assert "destructive" in lower, (
            "Safety floor must address destructive operations"
        )

    @pytest.mark.bdd
    def test_references_risk_classification(self) -> None:
        """Scenario: Risk classification integration for upgrades
        Given the adaptive-constraints.md module
        When scanning content
        Then it should reference risk-classification for profile upgrades
        """
        content = MODULE_FILE.read_text()
        assert "risk-classification" in content, (
            "adaptive-constraints.md must reference "
            "leyline:risk-classification for upgrades"
        )

    @pytest.mark.bdd
    def test_risk_upgrade_never_downgrades(self) -> None:
        """Scenario: Risk classification only upgrades, never downgrades
        Given the adaptive-constraints.md module
        When scanning the risk upgrade rules
        Then it should state that risk can upgrade but never downgrade
        """
        content = MODULE_FILE.read_text()
        lower = content.lower()
        assert "never" in lower and "downgrade" in lower, (
            "adaptive-constraints.md must state risk can never downgrade"
        )


class TestAdaptiveConstraintsLineWrapping:
    """
    Feature: Markdown prose line wrapping

    As a documentation maintainer
    I want prose lines to wrap at 80 characters
    So that git diffs stay clean and reviewable
    """

    @pytest.mark.bdd
    def test_prose_lines_wrap_at_80_chars(self) -> None:
        """Scenario: Prose lines respect 80-char wrap limit
        Given the adaptive-constraints.md module
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
