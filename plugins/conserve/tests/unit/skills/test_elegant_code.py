"""Tests for the elegant-code skill: decision ladder and negligence floor.

Note: elegant-code is a markdown-only methodology skill with no Python
source modules. The tests below validate:
  1. Skill file structure (SKILL.md exists, frontmatter, Exit Criteria).
  2. Methodology concepts (the 5-rung ordered ladder, the never-cut
     negligence floor, new-dependency-is-last-resort) using inline logic
     that mirrors the rules documented in the skill markdown.
Structural and conceptual tests are the appropriate test type for skills
that contain no executable Python code. See GitHub issue #320.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def skill_dir() -> Path:
    """Return the elegant-code skill directory path."""
    return Path(__file__).parents[3] / "skills" / "elegant-code"


@pytest.fixture
def skill_text(skill_dir: Path) -> str:
    """Return the SKILL.md contents."""
    return (skill_dir / "SKILL.md").read_text()


class TestLeastCodeStructure:
    """Feature: Skill file structure is valid and discoverable.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md exists.

        Given the elegant-code skill directory
        When checking for SKILL.md
        Then the file should exist
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_required_frontmatter(self, skill_text: str) -> None:
        """Scenario: SKILL.md has valid YAML frontmatter.

        Given the SKILL.md file
        When parsing the frontmatter
        Then required fields are present and name is 'elegant-code'
        """
        assert skill_text.startswith("---"), "should start with frontmatter"
        assert skill_text.count("---") >= 2, "should close frontmatter"
        frontmatter = skill_text[3 : skill_text.index("---", 3)]
        assert "name: elegant-code" in frontmatter, "name must be elegant-code"
        assert "description:" in frontmatter, "missing description"
        assert "category:" in frontmatter, "missing category"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_exit_criteria_section(self, skill_text: str) -> None:
        """Scenario: skill declares Exit Criteria.

        Given the project rule skill-exit-criteria
        When reading the skill
        Then an Exit Criteria section with checkboxes is present
        """
        assert "## Exit Criteria" in skill_text, "missing Exit Criteria section"
        assert "- [ ]" in skill_text, "Exit Criteria needs checkbox items"


class TestDecisionLadderContent:
    """Feature: the documented ladder has five ordered rungs.

    As a developer applying the skill
    I want the ladder rungs documented in order
    So that I stop at the first rung that holds
    """

    RUNGS = (
        "Need-to-exist",
        "Builtin / stdlib",
        "Native platform",
        "Installed dependency",
        "A few lines",
    )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_five_rungs_present_in_order(self, skill_text: str) -> None:
        """Scenario: rungs appear in the documented order.

        Given the decision ladder table
        When scanning the rung labels
        Then all five appear, each after the previous
        """
        positions = [skill_text.find(rung) for rung in self.RUNGS]
        assert all(p != -1 for p in positions), f"missing rung: {positions}"
        assert positions == sorted(positions), "rungs must be in ladder order"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_new_dependency_is_last_resort(self, skill_text: str) -> None:
        """Scenario: a new dependency is below rung 5, not rung 4.

        Given the rung-4 reuse rule
        When reading the ladder
        Then the skill states a new dependency is the last resort
        And points at dependency-verification before adding one
        """
        assert "last resort" in skill_text, "new dep must be last resort"
        assert "imbue:dependency-verification" in skill_text, (
            "must gate new deps on dependency-verification"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_honest_rationale_disclaims_unsupported_claim(
        self, skill_text: str
    ) -> None:
        """Scenario: the skill does not assert fewer-lines-means-fewer-bugs.

        Given the research that the complexity-defect law is unsettled
        When reading the rationale
        Then the skill argues from attack surface and review cost
        And explicitly disclaims the unsupported law
        """
        # Collapse wrapped prose to single spaces so multi-word phrases
        # match regardless of line breaks.
        normalized = " ".join(skill_text.split()).lower()
        assert "attack surface" in normalized, "must argue from attack surface"
        assert "review cost" in normalized, "must argue from review cost"
        assert "not empirically settled" in normalized or "not a clean" in normalized, (
            "must disclaim the fewer-lines-means-fewer-bugs law"
        )


class TestNegligenceFloor:
    """Feature: minimalism never trades away the safety floor.

    As a reviewer
    I want a documented never-cut list
    So that brevity never deletes a guard
    """

    FLOOR_ITEMS = (
        "validation",
        "Authorization",
        "Data-loss",
        "Error handling",
        "Accessibility",
    )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_floor_items_documented(self, skill_text: str) -> None:
        """Scenario: all floor items are listed.

        Given the negligence floor section
        When scanning for the never-cut categories
        Then each category is present
        """
        lowered = skill_text.lower()
        floor = skill_text[lowered.index("negligence floor") :]
        for item in self.FLOOR_ITEMS:
            assert item in floor, f"floor missing: {item}"


class TestMinimalElegantComplete:
    """Feature: minimal means elegant and complete, not fewest lines.

    As a developer applying the skill
    I want minimalism bounded by performance, edge, and negative cases
    So that brevity never omits an essential path
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_minimal_is_defined_as_no_incidental_complexity(
        self, skill_text: str
    ) -> None:
        """Scenario: minimal is reframed away from raw line count.

        Given the reframed thesis
        When reading the skill
        Then minimal is defined as no incidental complexity, not fewest lines
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "incidental complexity" in normalized, (
            "minimal must be defined as removing incidental complexity"
        )
        assert "not fewest lines" in normalized or "not mean fewest lines" in (
            normalized
        ), "skill must disclaim 'minimal = fewest lines'"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_performance_without_speculative_optimization(
        self, skill_text: str
    ) -> None:
        """Scenario: performance is in scope, micro-optimization is not.

        Given the completeness requirements
        When reading the performance guidance
        Then performance is addressed and speculative optimization is warned
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "performance" in normalized, "must address performance"
        assert "micro-optimi" in normalized or "speculative" in normalized, (
            "must warn against speculative micro-optimization"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_edge_and_negative_cases(self, skill_text: str) -> None:
        """Scenario: edge and negative cases are essential, never cut.

        Given the completeness requirements
        When reading the skill
        Then edge cases and negative/failure cases are required coverage
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "edge case" in normalized, "must require edge-case coverage"
        assert "negative" in normalized or "failure case" in normalized, (
            "must require negative/failure-case coverage"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_elegance_is_distinguished_from_terseness(self, skill_text: str) -> None:
        """Scenario: elegance is clarity, not cleverness or brevity.

        Given the research that terse/clever code raises defects
        When reading the elegance guidance
        Then elegance is distinguished from terseness/cleverness
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "elegan" in normalized, "must address elegance"
        assert "terse" in normalized or "clever" in normalized, (
            "elegance must be distinguished from terseness or cleverness"
        )


class TestLadderProcedure:
    """Feature: SKILL.md documents the stop-at-first-rung procedure.

    These assert the shipped skill markdown, not a function defined in
    this test file. Reverting or corrupting the documented ladder must
    fail at least one of them (the revert test); a tautology over a
    test-local helper could not (PR #577 finding I2).
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_five_rungs_documented_in_order(self, skill_text: str) -> None:
        """Scenario: the five rungs appear in their documented order.

        Given the elegant-code SKILL.md
        When scanning for the rung names
        Then need-to-exist, stdlib, native, installed dependency, and a
        few lines appear in that order.
        """
        low = skill_text.lower()
        rungs = [
            "need-to-exist",
            "builtin / stdlib",
            "native platform",
            "installed dependency",
            "a few lines",
        ]
        positions = [low.find(r) for r in rungs]
        missing = [r for r, p in zip(rungs, positions) if p == -1]
        assert not missing, f"missing rung(s): {missing}"
        assert positions == sorted(positions), "rungs are out of documented order"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stop_at_first_rung_rule_documented(self, skill_text: str) -> None:
        """Scenario: the stop-at-first-rung rule is stated.

        Given the SKILL.md
        When reading the decision-ladder procedure
        Then it instructs stopping at the first rung that solves the problem.
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "stop at the first rung" in normalized

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_new_dependency_is_last_resort_documented(self, skill_text: str) -> None:
        """Scenario: a new dependency is documented as the last resort.

        Given the SKILL.md
        When reading the guidance below the ladder
        Then a new dependency is named the last resort.
        """
        normalized = " ".join(skill_text.split()).lower()
        assert "new" in normalized and "dependency is the last resort" in normalized
