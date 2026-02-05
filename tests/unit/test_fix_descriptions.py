#!/usr/bin/env python3
"""
Feature: Extract structured content from skill descriptions

As a plugin developer
I want to extract triggers and usage patterns from descriptions
So that UI displays concise descriptions while preserving metadata
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from fix_descriptions import extract_structured_content


class TestExtractStructuredContent:
    """Test extraction of triggers, use_when, and do_not_use_when from descriptions."""

    @pytest.mark.unit
    def test_extracts_triggers_from_first_line(self):
        """
        Scenario: Description starts with Triggers line
        Given a description with "Triggers:" on the first line
        When I extract structured content
        Then triggers field contains the keywords
        And description field contains the actual description
        """
        # Arrange
        description = """
Triggers: refine, code quality, clean code, refactor

Analyze and improve living code quality across multiple dimensions.

Use when: improving code quality, reducing duplication
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert result["triggers"] == "refine, code quality, clean code, refactor"
        assert "Analyze and improve living code quality" in result["description"]
        assert "Triggers:" not in result["description"]

    @pytest.mark.unit
    def test_extracts_use_when_from_description(self):
        """
        Scenario: Description contains Use when section
        Given a description with "Use when:" guidance
        When I extract structured content
        Then use_when field contains the guidance
        And description does not contain "Use when:"
        """
        # Arrange
        description = """
Analyze code quality and improve it.

Use when: improving code quality, reducing duplication, refactoring for clarity

DO NOT use when: removing dead code
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert "improving code quality" in result["use_when"]
        assert "reducing duplication" in result["use_when"]
        assert "Use when:" not in result["description"]

    @pytest.mark.unit
    def test_extracts_do_not_use_when_from_description(self):
        """
        Scenario: Description contains DO NOT use when section
        Given a description with "DO NOT use when:" guidance
        When I extract structured content
        Then do_not_use_when field contains the anti-patterns
        And description does not contain "DO NOT use when:"
        """
        # Arrange
        description = """
Analyze and improve code quality.

DO NOT use when: removing dead code (use conserve:bloat-detector)
DO NOT use when: reviewing for bugs (use pensive:bug-review)
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert "removing dead code" in result["do_not_use_when"]
        assert "conserve:bloat-detector" in result["do_not_use_when"]
        assert "DO NOT use when:" not in result["description"]

    @pytest.mark.unit
    def test_handles_multiline_triggers(self):
        """
        Scenario: Triggers span multiple lines
        Given triggers that continue on multiple lines
        When I extract structured content
        Then all trigger keywords are concatenated
        """
        # Arrange
        description = """
Triggers: refine, code quality, clean code, refactor, duplication, algorithm efficiency,
complexity reduction, code smell, anti-slop, craft

Analyze and improve living code quality.
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert "refine" in result["triggers"]
        assert "complexity reduction" in result["triggers"]
        assert "craft" in result["triggers"]
        assert result["triggers"].count("Triggers:") == 0

    @pytest.mark.unit
    def test_preserves_description_without_triggers(self):
        """
        Scenario: Description has no triggers or usage patterns
        Given a plain description without metadata
        When I extract structured content
        Then description is preserved as-is
        And metadata fields are empty
        """
        # Arrange
        description = (
            "Analyze and improve living code quality across multiple dimensions."
        )

        # Act
        result = extract_structured_content(description)

        # Assert
        assert result["description"] == description.strip()
        assert result["triggers"] == ""
        assert result["use_when"] == ""
        assert result["do_not_use_when"] == ""

    @pytest.mark.unit
    def test_real_world_example_code_refinement(self):
        """
        Scenario: Process actual code-refinement skill description
        Given the actual problematic description from code-refinement
        When I extract structured content
        Then description is concise and UI-friendly
        And triggers are extracted to separate field
        """
        # Arrange
        description = """
Triggers: refine, code quality, clean code, refactor, duplication, algorithm efficiency,
complexity reduction, code smell, anti-slop, craft

Analyze and improve living code quality: duplication, algorithmic efficiency, clean code
principles, architectural fit, anti-slop patterns, and error handling robustness.

Use when: improving code quality, reducing AI slop, refactoring for clarity,
optimizing algorithms, applying clean code principles

DO NOT use when: removing dead/unused code (use conserve:bloat-detector).
DO NOT use when: reviewing for bugs (use pensive:bug-review).
DO NOT use when: selecting architecture paradigms (use archetypes skills).

This skill actively improves living code, complementing bloat detection (dead code removal)
with quality refinement (living code improvement).
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        # Description should be concise and not start with "Triggers:"
        assert not result["description"].startswith("Triggers:")
        assert "Analyze and improve living code quality" in result["description"]

        # Triggers should be extracted
        assert "refine" in result["triggers"]
        assert "code quality" in result["triggers"]
        assert "anti-slop" in result["triggers"]

        # Use when should be extracted
        assert "improving code quality" in result["use_when"]
        assert "reducing AI slop" in result["use_when"]

        # DO NOT use when should be extracted
        assert "removing dead/unused code" in result["do_not_use_when"]
        assert "conserve:bloat-detector" in result["do_not_use_when"]

    @pytest.mark.unit
    def test_handles_multiline_use_when(self):
        """
        Scenario: Use when guidance spans multiple lines
        Given use_when that continues across lines
        When I extract structured content
        Then all lines are concatenated with spaces
        """
        # Arrange
        description = """
Analyze code quality.

Use when: improving code quality, reducing AI slop, refactoring for clarity,
optimizing algorithms, applying clean code principles
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert "improving code quality" in result["use_when"]
        assert "optimizing algorithms" in result["use_when"]
        assert "applying clean code principles" in result["use_when"]
        # Should be one continuous string
        assert "\n" not in result["use_when"]

    @pytest.mark.unit
    def test_handles_multiple_do_not_use_when_lines(self):
        """
        Scenario: Multiple DO NOT use when entries
        Given multiple "DO NOT use when:" lines
        When I extract structured content
        Then all anti-patterns are captured together
        """
        # Arrange
        description = """
Analyze code quality.

DO NOT use when: removing dead/unused code (use conserve:bloat-detector).
DO NOT use when: reviewing for bugs (use pensive:bug-review).
DO NOT use when: selecting architecture paradigms (use archetypes skills).
"""

        # Act
        result = extract_structured_content(description)

        # Assert
        assert "removing dead/unused code" in result["do_not_use_when"]
        assert "reviewing for bugs" in result["do_not_use_when"]
        assert "selecting architecture paradigms" in result["do_not_use_when"]
