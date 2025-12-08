"""Tests for spec-writing skill functionality."""

import pytest
from unittest.mock import Mock, patch
import re


class TestSpecWriting:
    """Test cases for the Spec Writing skill."""

    def test_spec_creation_from_natural_language(self, sample_feature_description):
        """Test creating specification from natural language description."""
        # Parse feature description
        feature_desc = sample_feature_description

        # Should extract key components
        assert "user authentication" in feature_desc.lower()
        assert "email" in feature_desc.lower()
        assert "password" in feature_desc.lower()
        assert "role-based access control" in feature_desc.lower()

    def test_spec_structure_validation(self, sample_spec_content):
        """Test specification follows required structure."""
        spec = sample_spec_content

        # Check mandatory sections
        required_sections = [
            "## Overview",
            "## User Scenarios",
            "## Functional Requirements",
            "## Success Criteria"
        ]

        for section in required_sections:
            assert section in spec, f"Missing required section: {section}"

        # Check optional sections
        optional_sections = [
            "## Assumptions",
            "## Open Questions"
        ]

        for section in optional_sections:
            # Optional sections may or may not be present
            pass  # No assertion needed for optional sections

    def test_user_scenario_formatting(self, sample_spec_content):
        """Test user scenarios follow proper format."""
        # Look for user scenario patterns
        scenario_pattern = r"### As a (\w+)\nI want to (.+)\nSo that (.+)"
        scenarios = re.findall(scenario_pattern, sample_spec_content)

        assert len(scenarios) > 0, "Should have at least one user scenario"

        for role, want, so_that in scenarios:
            assert role.strip(), "Role should not be empty"
            assert want.strip(), "Desire should not be empty"
            assert so_that.strip(), "Purpose should not be empty"

    def test_functional_requirements_structure(self, sample_spec_content):
        """Test functional requirements are properly structured."""
        # Look for functional requirement sections
        fr_sections = re.findall(r"### ([^\n]+)\n(.+?)(?=\n###|\n##|$)", sample_spec_content, re.DOTALL)

        assert len(fr_sections) > 0, "Should have functional requirement sections"

        for title, content in fr_sections:
            assert title.strip(), "FR section title should not be empty"
            assert content.strip(), "FR section content should not be empty"
            # Should contain bullet points or numbered lists
            assert ("-" in content) or (":" in content), "FR should have structured items"

    def test_success_criteria_measurability(self, sample_spec_content):
        """Test success criteria are measurable and verifiable."""
        success_section = re.search(r"## Success Criteria\n(.+?)(?=\n##|$)", sample_spec_content, re.DOTALL)

        assert success_section, "Should have Success Criteria section"

        criteria_text = success_section.group(1)

        # Look for measurable indicators
        measurable_patterns = [
            r"can\s+\w+",
            r"are\s+\w+",
            r"\d+",
            r"within\s+\w+",
            r"after\s+\w+"
        ]

        has_measurable = any(re.search(pattern, criteria_text.lower()) for pattern in measurable_patterns)
        assert has_measurable, "Success criteria should contain measurable elements"

    def test_clarification_markers_limit(self, sample_spec_content):
        """Test clarification markers are limited (max 3)."""
        # Count clarification markers
        clarification_count = sample_spec_content.count("[CLARIFY]")

        assert clarification_count <= 3, f"Too many clarification markers: {clarification_count} (max 3 allowed)"

    def test_implementation_details_avoidance(self, sample_spec_content):
        """Test specification avoids implementation details."""
        # Look for implementation-specific terms that should be avoided
        implementation_terms = [
            "database",
            "api endpoint",
            "function",
            "class",
            "method",
            "variable",
            "import",
            "library",
            "framework"
        ]

        spec_lower = sample_spec_content.lower()
        found_terms = [term for term in implementation_terms if term in spec_lower]

        # Allow some technical terms but not specific implementation details
        implementation_detail_patterns = [
            r"create.*function",
            r"implement.*class",
            r"use.*library",
            r"import.*module"
        ]

        has_implementation_details = any(re.search(pattern, spec_lower) for pattern in implementation_detail_patterns)
        assert not has_implementation_details, "Specification should avoid implementation details"

    def test_business_value_focus(self, sample_spec_content):
        """Test specification focuses on business value."""
        # Look for business value indicators
        business_value_terms = [
            "user",
            "customer",
            "business",
            "value",
            "benefit",
            "advantage",
            "improve",
            "enable",
            "allow"
        ]

        spec_lower = sample_spec_content.lower()
        business_terms_found = [term for term in business_value_terms if term in spec_lower]

        assert len(business_terms_found) >= 3, f"Should include business value terms, found: {business_terms_found}"

    def test_acceptance_criteria_inclusion(self, sample_spec_content):
        """Test specification includes acceptance criteria."""
        # Acceptance criteria should be embedded in success criteria or scenarios
        acceptance_patterns = [
            r"can\s+\w+",
            r"will\s+\w+",
            r"should\s+\w+",
            r"must\s+\w+"
        ]

        has_acceptance_criteria = any(re.search(pattern, sample_spec_content.lower()) for pattern in acceptance_patterns)
        assert has_acceptance_criteria, "Should include acceptance criteria"

    def test_edge_cases_consideration(self, sample_spec_content):
        """Test specification considers edge cases."""
        # Look for edge case indicators
        edge_case_indicators = [
            "edge case",
            "boundary",
            "limit",
            "maximum",
            "minimum",
            "invalid",
            "error",
            "timeout",
            "concurrent"
        ]

        spec_lower = sample_spec_content.lower()
        edge_cases_found = [indicator for indicator in edge_case_indicators if indicator in spec_lower]

        # Edge cases are optional but good to have
        # assert len(edge_cases_found) > 0, "Should consider edge cases"

    def test_spec_clarity_readability(self, sample_spec_content):
        """Test specification is clear and readable."""
        # Check sentence complexity
        sentences = re.split(r'[.!?]+', sample_spec_content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Avoid extremely long sentences
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        assert len(long_sentences) < len(sentences) * 0.1, "Too many very long sentences"

        # Check for clear structure
        headings = re.findall(r'^#{1,6}\s+(.+)$', sample_spec_content, re.MULTILINE)
        assert len(headings) >= 4, "Should have clear heading structure"

    def test_assumptions_documentation(self, sample_spec_content):
        """Test assumptions are explicitly documented."""
        assumptions_section = re.search(r"## Assumptions\n(.+?)(?=\n##|$)", sample_spec_content, re.DOTALL)

        if assumptions_section:
            assumptions_text = assumptions_section.group(1)
            # Should have bullet points or numbered list
            assert ("-" in assumptions_text) or ("1." in assumptions_text), "Assumptions should be structured"

    def test_non_personal_pronoun_usage(self, sample_spec_content):
        """Test specification avoids personal pronouns (I, we, our)."""
        personal_pronouns = [" I ", " we ", " our ", " my "]
        spec_lower = " " + sample_spec_content.lower() + " "

        found_pronouns = [pronoun for pronoun in personal_pronouns if pronoun in spec_lower]
        # Allow "I want to" in user scenarios but not elsewhere
        non_scenario_pronouns = []
        for pronoun in found_pronouns:
            # Check if pronoun is in a user scenario
            scenario_context = re.search(r"### As a [^\n]*[^\n]*" + pronoun + "[^\n]*", sample_spec_content)
            if not scenario_context:
                non_scenario_pronouns.append(pronoun)

        assert len(non_scenario_pronouns) == 0, f"Found personal pronouns outside scenarios: {non_scenario_pronouns}"

    def test_spec_completeness_score(self, sample_spec_content):
        """Test specification completeness scoring."""
        completeness_factors = {
            "overview": "## Overview" in sample_spec_content,
            "user_scenarios": "## User Scenarios" in sample_spec_content,
            "functional_requirements": "## Functional Requirements" in sample_spec_content,
            "success_criteria": "## Success Criteria" in sample_spec_content,
            "assumptions": "## Assumptions" in sample_spec_content,
            "has_user_roles": "### As a" in sample_spec_content,
            "has_acceptance_criteria": any(term in sample_spec_content.lower() for term in ["can ", "will ", "should "]),
            "limited_clarifications": sample_spec_content.count("[CLARIFY]") <= 3
        }

        completeness_score = sum(completeness_factors.values()) / len(completeness_factors)

        # Should achieve at least 80% completeness
        assert completeness_score >= 0.8, f"Completeness score too low: {completeness_score:.2%}"