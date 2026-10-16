"""Contract tests for the spec-writing skill and the command that applies it.

Each test pins a rule that ``skills/spec-writing`` or
``commands/speckit-specify.md`` states, so deleting or contradicting the
rule fails the test. These replace tests that compared conftest fixture
strings with themselves and could not fail.
"""

from __future__ import annotations

import re

import pytest

from tests._contract import headings, read, section

SKILL = "skills/spec-writing/SKILL.md"
STRUCTURE = "skills/spec-writing/modules/specification-structure.md"
CRITERIA = "skills/spec-writing/modules/success-criteria-patterns.md"
CHECKLISTS = "skills/spec-writing/modules/checklist-dimensions.md"
SPECIFY = "commands/speckit-specify.md"
CLARIFY = "commands/speckit-clarify.md"

MANDATORY = [
    "Overview/Context",
    "User Scenarios",
    "Functional Requirements",
    "Success Criteria",
]


@pytest.fixture(scope="module")
def skill() -> str:
    return read(SKILL)


@pytest.fixture(scope="module")
def structure() -> str:
    return read(STRUCTURE)


@pytest.fixture(scope="module")
def specify() -> str:
    return read(SPECIFY)


class TestSpecWriting:
    """The rules a specification is written and validated against."""

    def test_should_extract_key_components_when_parsing_natural_language_description(
        self, specify: str
    ) -> None:
        """speckit-specify extracts actors, actions, data and constraints."""
        assert 'If empty: ERROR "No feature description provided"' in specify
        assert "Identify: actors, actions, data, constraints" in specify

    def test_should_require_mandatory_sections_when_validating_spec_structure(
        self, skill: str, structure: str
    ) -> None:
        """The skill and its structure module name the same four sections."""
        listed = re.findall(
            r"^\d\. \*\*(.+?)\*\*", section(skill, "Mandatory Sections"), re.MULTILINE
        )
        assert listed == MANDATORY
        numbered = [
            h.split(". ", 1)[1]
            for h in headings(structure, 3)
            if h[:2] in {"1.", "2.", "3.", "4."}
        ]
        assert numbered == MANDATORY

    def test_should_reject_spec_when_missing_functional_requirements(
        self, skill: str, structure: str
    ) -> None:
        """A spec without Functional Requirements is not complete."""
        assert (
            "Every specification must include these four sections to be "
            "considered complete." in structure
        )
        exit_criteria = section(skill, "Exit Criteria")
        assert "Functional Requirements" in exit_criteria

    def test_should_format_user_scenarios_correctly_when_present(
        self, structure: str
    ) -> None:
        """Scenarios are headed by user type and goal, in template and example."""
        assert "### Scenario 1: [User Type] - [Goal]" in structure
        assert (
            "### Scenario 1: First-Time Buyer - Review Order Before Purchase"
            in structure
        )

    def test_should_structure_functional_requirements_with_sections_when_validating(
        self, structure: str
    ) -> None:
        """Functional requirements split into capabilities, validation, business rules."""
        requirements = structure.split("### 3. Functional Requirements", 1)[1]
        requirements = requirements.split("### 4. Success Criteria", 1)[0]
        for subsection in (
            "### Core Capabilities",
            "### Validation Rules",
            "### Business Rules",
        ):
            assert subsection in requirements, subsection
        assert "Define what the system must do, without specifying how." in requirements

    def test_should_contain_measurable_elements_when_validating_success_criteria(
        self,
    ) -> None:
        """Good success criteria have four named properties."""
        criteria = read(CRITERIA)
        assert headings(criteria, 2)[0] == "What Makes Good Success Criteria"
        assert headings(criteria, 3)[:4] == [
            "Measurable",
            "Technology-Agnostic",
            "User-Focused",
            "Verifiable",
        ]

    def test_should_limit_clarification_markers_to_three_when_validating_spec(
        self, specify: str
    ) -> None:
        """The marker cap is stated where the spec is drafted and in the guidelines."""
        assert "**LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**" in specify
        assert (
            "**Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers"
            in specify
        )
        assert "(Q1, Q2, Q3 - max 3 total)" in specify

    def test_should_validate_clarification_count_limits(self) -> None:
        """speckit-clarify caps queued questions at 5 and a session at 10."""
        clarify = read(CLARIFY)
        assert (
            "prioritized queue of candidate clarification questions (maximum 5)"
            in clarify
        )
        assert "Maximum of 10 total questions across the whole session." in clarify

    def test_should_avoid_implementation_details_when_validating_spec(
        self, skill: str, specify: str
    ) -> None:
        """Both the skill checklist and the generated checklist forbid implementation detail."""
        assert "- [ ] No implementation details present" in section(
            skill, "Quality Checklist"
        )
        assert (
            "- [ ] No implementation details (languages, frameworks, APIs)" in specify
        )
        assert (
            "Avoid HOW to implement (no tech stack, APIs, code structure)." in specify
        )

    def test_should_focus_on_business_value_when_validating_spec(
        self, skill: str, specify: str
    ) -> None:
        """User value and business needs lead the skill and the checklist."""
        assert "Focus on user value and business needs" in section(
            skill, "Core Principles"
        )
        assert "- [ ] Focused on user value and business needs" in specify

    def test_should_include_acceptance_criteria_when_validating_spec(
        self, skill: str, specify: str
    ) -> None:
        """Every functional requirement carries a testable acceptance criterion."""
        assert "testable acceptance" in section(skill, "Exit Criteria").replace(
            "\n      ", " "
        )
        assert (
            "- [ ] All functional requirements have clear acceptance criteria"
            in specify
        )

    def test_should_optionally_consider_edge_cases_when_validating_spec(
        self, skill: str, structure: str
    ) -> None:
        """Edge Cases is optional, with a stated condition for including it."""
        assert "- Edge Cases (when special handling needed)" in section(
            skill, "Optional Sections"
        )
        assert "**Include Edge Cases when**:" in structure

    def test_should_write_for_business_stakeholders(self, specify: str) -> None:
        """Specs are written for business stakeholders, not developers."""
        assert "- Written for business stakeholders, not developers." in specify
        assert "- [ ] Written for non-technical stakeholders" in specify

    def test_should_structure_assumptions_when_present_in_spec(
        self, skill: str, specify: str, structure: str
    ) -> None:
        """Defaults chosen for gaps are recorded in an Assumptions section."""
        assert "- Assumptions (when decisions made with incomplete info)" in skill
        assert "document assumptions in Assumptions section" in specify
        assert "**Include Assumptions when**:" in structure

    def test_should_convert_each_bad_success_criterion_to_a_user_facing_one(
        self, skill: str
    ) -> None:
        """Every implementation-focused example carries a user-facing rewrite."""
        bad = section(skill, "Bad (Implementation-focused, Internal metrics)")
        examples = [line for line in bad.splitlines() if line.startswith("- ")]
        assert len(examples) == 3
        for line in examples:
            assert '-> Use: "' in line, line

    def test_should_rerun_validation_up_to_three_times(self, specify: str) -> None:
        """Validation reruns until every checklist item passes, at most 3 times."""
        assert "Re-run validation until all items pass (max 3 iterations)" in specify
        assert "`FEATURE_DIR/checklists/requirements.md`" in specify

    def test_should_error_when_no_user_flow_can_be_determined(
        self, specify: str
    ) -> None:
        """Missing user scenarios is an error, and mandatory sections are required."""
        assert (
            'If no clear user flow: ERROR "Cannot determine user scenarios"' in specify
        )
        assert "- [ ] All mandatory sections completed" in specify

    def test_should_describe_requirement_checklists_as_tests_of_the_writing(
        self,
    ) -> None:
        """Requirement checklists test the writing, not the implementation."""
        checklists = read(CHECKLISTS)
        assert "Checklists are **unit tests for requirements writing**" in checklists
        assert "NOT implementation correctness" in checklists
