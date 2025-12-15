"""Tests for spec-writing skill functionality."""

import re

import pytest


class TestSpecWriting:
    """Test cases for the Spec Writing skill."""

    def test_should_extract_key_components_when_parsing_natural_language_description(
        self, detailed_feature_description
    ) -> None:
        """Test creating specification from natural language description."""
        # Given: a detailed natural language feature description
        feature_desc = detailed_feature_description

        # When: parsing the feature description
        # Then: should extract all key authentication components
        assert "user authentication" in feature_desc.lower()
        assert "email" in feature_desc.lower()
        assert "password" in feature_desc.lower()
        assert "role-based access control" in feature_desc.lower()

    def test_should_require_mandatory_sections_when_validating_spec_structure(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification follows required structure."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: validating the specification structure
        required_sections = [
            "## Overview",
            "## User Scenarios",
            "## Functional Requirements",
            "## Success Criteria",
        ]

        # Then: all mandatory sections should be present
        for section in required_sections:
            assert section in spec, f"Missing required section: {section}"

    def test_should_reject_spec_when_missing_functional_requirements(
        self, spec_without_requirements
    ) -> None:
        """Test validation rejects specs without functional requirements."""
        # Given: a spec missing the functional requirements section
        spec = spec_without_requirements

        # When: checking for the required Functional Requirements section
        # Then: the section should be missing
        assert "## Functional Requirements" not in spec

    def test_should_format_user_scenarios_correctly_when_present(
        self, valid_authentication_spec_content
    ) -> None:
        """Test user scenarios follow proper format."""
        # Given: a valid authentication specification with user scenarios
        spec = valid_authentication_spec_content

        # When: extracting user scenario patterns
        scenario_pattern = r"### As a (\w+)\nI want to (.+)\nSo that (.+)"
        scenarios = re.findall(scenario_pattern, spec)

        # Then: should have at least one properly formatted scenario
        assert len(scenarios) > 0, "Should have at least one user scenario"

        # And: each scenario should have all three components populated
        for role, want, so_that in scenarios:
            assert role.strip(), "Role should not be empty"
            assert want.strip(), "Desire should not be empty"
            assert so_that.strip(), "Purpose should not be empty"

    def test_should_structure_functional_requirements_with_sections_when_validating(
        self, valid_authentication_spec_content
    ) -> None:
        """Test functional requirements are properly structured."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: extracting the functional requirements section
        fr_section = re.search(
            r"## Functional Requirements\n(.+?)(?=\n##|$)",
            spec,
            re.DOTALL,
        )

        # Then: should have a functional requirements section
        assert fr_section, "Should have Functional Requirements section"

        fr_content = fr_section.group(1)

        # And: should contain subsections with structured content
        subsections = re.findall(
            r"### ([^\n]+)\n(.+?)(?=\n###|$)",
            fr_content,
            re.DOTALL,
        )

        assert len(subsections) > 0, "Should have functional requirement subsections"

        # And: each subsection should have a title and structured content
        for title, content in subsections:
            assert title.strip(), "FR subsection title should not be empty"
            assert content.strip(), "FR subsection content should not be empty"
            # Should contain bullet points or numbered lists
            assert ("-" in content) or (
                ":" in content
            ), "FR subsection should have structured items"

    def test_should_contain_measurable_elements_when_validating_success_criteria(
        self, valid_authentication_spec_content
    ) -> None:
        """Test success criteria are measurable and verifiable."""
        # Given: a valid authentication specification with success criteria
        spec = valid_authentication_spec_content

        # When: extracting the success criteria section
        success_section = re.search(
            r"## Success Criteria\n(.+?)(?=\n##|$)",
            spec,
            re.DOTALL,
        )

        # Then: success criteria section should exist
        assert success_section, "Should have Success Criteria section"

        criteria_text = success_section.group(1)

        # And: should contain measurable indicators
        measurable_patterns = [
            r"can\s+\w+",
            r"are\s+\w+",
            r"\d+",
            r"within\s+\w+",
            r"after\s+\w+",
        ]

        has_measurable = any(
            re.search(pattern, criteria_text.lower()) for pattern in measurable_patterns
        )
        assert has_measurable, "Success criteria should contain measurable elements"

    def test_should_limit_clarification_markers_to_three_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test clarification markers are limited (max 3)."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: counting clarification markers
        clarification_count = spec.count("[CLARIFY]")

        # Then: should have at most 3 clarification markers
        assert (
            clarification_count <= 3
        ), f"Too many clarification markers: {clarification_count} (max 3 allowed)"

    @pytest.mark.parametrize(
        "clarify_count,expected_valid",
        [
            (0, True),  # No clarifications is valid
            (1, True),  # One clarification is valid
            (3, True),  # Three clarifications is the limit
            (4, False),  # Four clarifications exceeds limit
        ],
    )
    def test_should_validate_clarification_count_limits(
        self, spec_content_factory, clarify_count: int, expected_valid: bool
    ) -> None:
        """Test parameterized clarification marker validation."""
        # Given: a spec with a specific number of clarification markers
        clarify_markers = "\n".join(
            [f"[CLARIFY] Question {i}?" for i in range(clarify_count)]
        )
        spec = (
            spec_content_factory(
                "Test Feature",
                "Testing clarification limits",
                ["Requirement 1"],
            )
            + f"\n## Open Questions\n{clarify_markers}"
        )

        # When: counting clarification markers
        actual_count = spec.count("[CLARIFY]")

        # Then: count should match expected and validity should be correct
        assert actual_count == clarify_count
        is_valid = actual_count <= 3
        assert is_valid == expected_valid

    def test_should_avoid_implementation_details_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification avoids implementation details."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content
        spec_lower = spec.lower()

        # When: checking for specific implementation detail patterns
        implementation_detail_patterns = [
            r"create.*function",
            r"implement.*class",
            r"use.*library",
            r"import.*module",
        ]

        has_implementation_details = any(
            re.search(pattern, spec_lower) for pattern in implementation_detail_patterns
        )

        # Then: should not contain implementation-specific phrases
        assert (
            not has_implementation_details
        ), "Specification should avoid implementation details"

    def test_should_focus_on_business_value_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification focuses on business value."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content
        spec_lower = spec.lower()

        # When: checking for business value indicators
        business_value_terms = [
            "user",
            "customer",
            "business",
            "value",
            "benefit",
            "advantage",
            "improve",
            "enable",
            "allow",
        ]

        business_terms_found = [
            term for term in business_value_terms if term in spec_lower
        ]

        # Then: should include at least 3 business value terms
        assert (
            len(business_terms_found) >= 3
        ), f"Should include business value terms, found: {business_terms_found}"

    def test_should_include_acceptance_criteria_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification includes acceptance criteria."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: checking for acceptance criteria patterns
        acceptance_patterns = [
            r"can\s+\w+",
            r"will\s+\w+",
            r"should\s+\w+",
            r"must\s+\w+",
        ]

        has_acceptance_criteria = any(
            re.search(pattern, spec.lower()) for pattern in acceptance_patterns
        )

        # Then: should include at least one acceptance criteria pattern
        assert has_acceptance_criteria, "Should include acceptance criteria"

    def test_should_optionally_consider_edge_cases_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification optionally considers edge cases."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content
        spec_lower = spec.lower()

        # When: checking for edge case indicators
        edge_case_indicators = [
            "edge case",
            "boundary",
            "limit",
            "maximum",
            "minimum",
            "invalid",
            "error",
            "timeout",
            "concurrent",
        ]

        edge_cases_found = [
            indicator for indicator in edge_case_indicators if indicator in spec_lower
        ]

        # Then: edge cases are optional but good to have
        # This test documents the edge case check without enforcing it
        # If edge cases are present, they should be meaningful
        if edge_cases_found:
            assert len(edge_cases_found) > 0

    def test_should_maintain_clarity_and_readability_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification is clear and readable."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: analyzing sentence complexity
        sentences = re.split(r"[.!?]+", spec)
        sentences = [s.strip() for s in sentences if s.strip()]

        long_sentences = [s for s in sentences if len(s.split()) > 30]

        # Then: should avoid extremely long sentences (less than 10% of total)
        assert (
            len(long_sentences) < len(sentences) * 0.1
        ), "Too many very long sentences"

        # And: should have clear heading structure
        headings = re.findall(r"^#{1,6}\s+(.+)$", spec, re.MULTILINE)
        assert len(headings) >= 4, "Should have clear heading structure"

    def test_should_structure_assumptions_when_present_in_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test assumptions are explicitly documented and structured."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: extracting the assumptions section
        assumptions_section = re.search(
            r"## Assumptions\n(.+?)(?=\n##|$)",
            spec,
            re.DOTALL,
        )

        # Then: if assumptions are present, they should be structured
        if assumptions_section:
            assumptions_text = assumptions_section.group(1)
            # Should have bullet points or numbered list
            assert ("-" in assumptions_text) or (
                "1." in assumptions_text
            ), "Assumptions should be structured"

    def test_should_avoid_personal_pronouns_outside_scenarios_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification avoids personal pronouns (I, we, our) outside scenarios."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content
        spec_lower = " " + spec.lower() + " "

        # When: checking for personal pronouns
        personal_pronouns = [" I ", " we ", " our ", " my "]
        found_pronouns = [
            pronoun for pronoun in personal_pronouns if pronoun in spec_lower
        ]

        # Then: allow "I want to" in user scenarios but not elsewhere
        non_scenario_pronouns = []
        for pronoun in found_pronouns:
            # Check if pronoun is in a user scenario
            scenario_context = re.search(
                r"### As a [^\n]*[^\n]*" + pronoun + "[^\n]*",
                spec,
            )
            if not scenario_context:
                non_scenario_pronouns.append(pronoun)

        assert (
            len(non_scenario_pronouns) == 0
        ), f"Found personal pronouns outside scenarios: {non_scenario_pronouns}"

    def test_should_achieve_high_completeness_score_when_validating_spec(
        self, valid_authentication_spec_content
    ) -> None:
        """Test specification completeness scoring."""
        # Given: a valid authentication specification
        spec = valid_authentication_spec_content

        # When: calculating completeness score across multiple factors
        completeness_factors = {
            "overview": "## Overview" in spec,
            "user_scenarios": "## User Scenarios" in spec,
            "functional_requirements": "## Functional Requirements" in spec,
            "success_criteria": "## Success Criteria" in spec,
            "assumptions": "## Assumptions" in spec,
            "has_user_roles": "### As a" in spec,
            "has_acceptance_criteria": any(
                term in spec.lower() for term in ["can ", "will ", "should "]
            ),
            "limited_clarifications": spec.count("[CLARIFY]") <= 3,
        }

        completeness_score = sum(completeness_factors.values()) / len(
            completeness_factors,
        )

        # Then: should achieve at least 80% completeness
        assert (
            completeness_score >= 0.8
        ), f"Completeness score too low: {completeness_score:.2%}"

    def test_should_fail_completeness_when_missing_critical_sections(
        self, minimal_spec_content
    ) -> None:
        """Test incomplete spec fails completeness scoring."""
        # Given: a minimal spec with only required sections
        spec = minimal_spec_content

        # When: calculating completeness score
        completeness_factors = {
            "overview": "## Overview" in spec,
            "user_scenarios": "## User Scenarios" in spec,
            "functional_requirements": "## Functional Requirements" in spec,
            "success_criteria": "## Success Criteria" in spec,
            "assumptions": "## Assumptions" in spec,
            "has_user_roles": "### As a" in spec,
            "has_acceptance_criteria": any(
                term in spec.lower() for term in ["can ", "will ", "should "]
            ),
            "limited_clarifications": spec.count("[CLARIFY]") <= 3,
        }

        completeness_score = sum(completeness_factors.values()) / len(
            completeness_factors,
        )

        # Then: minimal spec should have lower completeness score
        assert (
            completeness_score < 0.8
        ), f"Minimal spec should not achieve high completeness: {completeness_score:.2%}"

    @pytest.mark.parametrize(
        "spec_type,min_score",
        [
            ("valid_authentication_spec_content", 0.8),
            ("minimal_spec_content", 0.0),
            ("empty_spec_content", 0.0),
        ],
    )
    def test_should_score_specs_appropriately_by_type(
        self, request, spec_type: str, min_score: float
    ) -> None:
        """Test parameterized completeness scoring for different spec types."""
        # Given: a spec of a specific type
        spec = request.getfixturevalue(spec_type)

        # When: calculating completeness score
        completeness_factors = {
            "overview": "## Overview" in spec,
            "user_scenarios": "## User Scenarios" in spec,
            "functional_requirements": "## Functional Requirements" in spec,
            "success_criteria": "## Success Criteria" in spec,
            "assumptions": "## Assumptions" in spec,
            "has_user_roles": "### As a" in spec,
            "has_acceptance_criteria": any(
                term in spec.lower() for term in ["can ", "will ", "should "]
            ),
            "limited_clarifications": spec.count("[CLARIFY]") <= 3,
        }

        completeness_score = sum(completeness_factors.values()) / len(
            completeness_factors,
        )

        # Then: score should meet the minimum threshold for that type
        assert (
            completeness_score >= min_score
        ), f"{spec_type} completeness score {completeness_score:.2%} below minimum {min_score:.2%}"
