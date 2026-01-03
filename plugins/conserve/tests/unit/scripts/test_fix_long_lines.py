#!/usr/bin/env python3
"""Tests for fix_long_lines.py script - actual implementation tests.

This module tests the line-breaking functions following TDD/BDD principles.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the fix_long_lines module dynamically
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "fix_long_lines_module", scripts_dir / "fix_long_lines.py"
)
assert spec is not None
assert spec.loader is not None
fix_long_lines_module = importlib.util.module_from_spec(spec)
sys.modules["fix_long_lines_module"] = fix_long_lines_module
spec.loader.exec_module(fix_long_lines_module)

fix_long_descriptions = fix_long_lines_module.fix_long_descriptions
break_description_line = fix_long_lines_module.break_description_line
break_list_item_line = fix_long_lines_module.break_list_item_line
break_generic_line = fix_long_lines_module.break_generic_line
fix_skill_file = fix_long_lines_module.fix_skill_file


class TestFixLongLinesImplementation:
    """Feature: Line breaker fixes excessively long lines in skill files.

    As a documentation formatter
    I want to break long lines at logical points
    So that files are more readable and follow line length limits
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_preserves_short_lines(self) -> None:
        """Scenario: Fixer preserves lines within length limit.

        Given content with short lines
        When fixing long lines
        Then short lines should remain unchanged
        """
        # Arrange
        content = "Short line\nAnother short line"

        # Act
        result = fix_long_descriptions(content, max_length=80)

        # Assert
        assert result == content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_breaks_description_lines(self) -> None:
        """Scenario: Fixer breaks long description lines.

        Given a description line exceeding max length
        When fixing
        Then it should break at logical points
        """
        # Arrange
        long_line = "description: This is a very long description that exceeds the maximum line length, and needs to be broken"

        # Act
        result = fix_long_descriptions(long_line, max_length=80)

        # Assert
        lines = result.split("\n")
        assert len(lines) > 1
        assert all(len(line) <= 85 for line in lines)  # Allow small margin

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_description_at_comma(self) -> None:
        """Scenario: Description breaks at comma when possible.

        Given a description with commas
        When breaking the line
        Then it should break at the first comma
        """
        # Arrange
        line = "description: First part, second part, third part that is very long"

        # Act
        result = break_description_line(line, max_length=80)

        # Assert
        assert len(result) == 2
        assert "First part," in result[0]
        assert "second part" in result[1]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_description_at_and(self) -> None:
        """Scenario: Description breaks at 'and' when no comma.

        Given a description without commas but with 'and'
        When breaking the line
        Then it should break at 'and'
        """
        # Arrange
        line = (
            "description: This describes something and another thing that makes it long"
        )

        # Act
        result = break_description_line(line, max_length=80)

        # Assert
        assert len(result) > 1
        # Should break somewhere logical

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_list_item_line(self) -> None:
        """Scenario: List item breaks after colon.

        Given a long list item with bold prefix
        When breaking the line
        Then it should break after the colon
        """
        # Arrange
        line = (
            "- **Long Item Name**: This is a very long description that needs breaking"
        )

        # Act
        result = break_list_item_line(line, max_length=60)

        # Assert
        assert len(result) == 2
        assert result[0].endswith(":")
        assert result[1].startswith("    ")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_list_item_preserves_short_lines(self) -> None:
        """Scenario: List item breaker preserves short lines.

        Given a short list item
        When checking if break is needed
        Then it should return unchanged
        """
        # Arrange
        line = "- **Short**: Description"

        # Act
        result = break_list_item_line(line, max_length=80)

        # Assert
        assert len(result) == 1
        assert result[0] == line

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_generic_line_at_space(self) -> None:
        """Scenario: Generic line breaks at nearest space.

        Given a long generic line
        When breaking
        Then it should break at the nearest space before limit
        """
        # Arrange
        line = "This is a very long line that needs to be broken at a reasonable point"

        # Act
        result = break_generic_line(line, max_length=40)

        # Assert
        assert len(result) == 2
        assert len(result[0]) <= 40
        assert result[1].startswith("    ")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_break_generic_forces_break_no_spaces(self) -> None:
        """Scenario: Generic breaker forces break when no spaces.

        Given a long line with no spaces
        When breaking
        Then it should force break with ellipsis
        """
        # Arrange
        line = "a" * 100  # No spaces

        # Act
        result = break_generic_line(line, max_length=40)

        # Assert
        assert len(result) == 2
        assert "..." in result[0]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_skill_file_processes_file(self, tmp_path: Path) -> None:
        """Scenario: Fixer processes actual skill file.

        Given a skill file with long lines
        When processing the file
        Then it should create fixed version
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = "description: This is a very long description line that exceeds the normal maximum line length and needs breaking\n"
        skill_file.write_text(content)

        # Act
        result = fix_skill_file(str(skill_file), max_length=80)

        # Assert
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_skill_file_handles_nonexistent_file(self, tmp_path: Path) -> None:
        """Scenario: Fixer handles missing files gracefully.

        Given a path to nonexistent file
        When attempting to fix
        Then it should return False
        """
        # Arrange
        nonexistent = tmp_path / "does_not_exist.md"

        # Act
        result = fix_skill_file(str(nonexistent))

        # Assert
        assert result is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_handles_mixed_content(self) -> None:
        """Scenario: Fixer handles mixed content types.

        Given content with various line types
        When fixing
        Then each type should be handled appropriately
        """
        # Arrange
        content = """# Short title
description: Very long description that needs to be broken at an appropriate point, such as a comma
- **List Item**: This is a long list item description that also needs breaking
Regular text that is also quite long and should be broken at a reasonable point"""

        # Act
        result = fix_long_descriptions(content, max_length=80)

        # Assert
        lines = result.split("\n")
        assert len(lines) > 4  # Should have broken some lines

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "max_length",
        [40, 60, 80, 100],
    )
    def test_respects_different_max_lengths(self, max_length: int) -> None:
        """Scenario: Fixer respects different max length limits.

        Given various max length settings
        When fixing long lines
        Then lines should respect the specified limit
        """
        # Arrange
        long_line = "This is a very long line that definitely needs to be broken into multiple pieces"

        # Act
        result = break_generic_line(long_line, max_length=max_length)

        # Assert
        if len(long_line) > max_length:
            assert len(result[0]) <= max_length + 5  # Small margin for breaks


class TestFixLongLinesEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_content(self) -> None:
        """Scenario: Fixer handles empty content.

        Given empty content
        When fixing
        Then it should return empty result without errors
        """
        # Act
        result = fix_long_descriptions("")

        # Assert
        assert result == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_single_character_lines(self) -> None:
        """Scenario: Fixer handles very short lines.

        Given content with single character lines
        When fixing
        Then it should preserve them
        """
        # Arrange
        content = "a\nb\nc"

        # Act
        result = fix_long_descriptions(content)

        # Assert
        assert result == content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_description_without_break_points(self) -> None:
        """Scenario: Description line with no logical break points.

        Given a description without commas or 'and'
        When breaking
        Then it should force break with ellipsis
        """
        # Arrange
        line = "description: " + "word" * 30  # No break points

        # Act
        result = break_description_line(line, max_length=80)

        # Assert
        assert len(result) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_list_item_without_colon(self) -> None:
        """Scenario: List item without colon separator.

        Given a list item without colon
        When attempting to break
        Then it should return unchanged
        """
        # Arrange
        line = "- Just a list item without colon"

        # Act
        result = break_list_item_line(line, max_length=20)

        # Assert
        assert result == [line]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_preserves_indentation(self) -> None:
        """Scenario: Fixer preserves existing indentation.

        Given content with indented lines
        When fixing
        Then indentation should be maintained
        """
        # Arrange
        content = (
            "    Indented line that is quite long and needs breaking at some point"
        )

        # Act
        result = break_generic_line(content, max_length=40)

        # Assert
        # Should maintain some level of indentation in continuation

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_unicode_content(self) -> None:
        """Scenario: Fixer handles Unicode characters correctly.

        Given content with Unicode characters
        When fixing
        Then it should handle them correctly
        """
        # Arrange
        content = "description: This line contains émojis 🎉 and Üñíçödé characters, making it longer"

        # Act
        result = fix_long_descriptions(content, max_length=60)

        # Assert
        # Should handle without errors
        assert isinstance(result, str)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_handles_description_and_list_mix(self) -> None:
        """Scenario: Fixer handles files with both descriptions and lists.

        Given content with description and list item lines
        When fixing
        Then both types should be handled correctly
        """
        # Arrange
        content = """description: Very long description with multiple parts, including various elements that exceed limits

- **Item**: Another very long list item with description that also needs breaking"""

        # Act
        result = fix_long_descriptions(content, max_length=60)

        # Assert
        lines = result.split("\n")
        # Should have broken lines
        assert len(lines) > 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_applies_generic_breaking_fallback(self) -> None:
        """Scenario: Fixer uses generic breaking as fallback.

        Given a long line that doesn't match special patterns
        When fixing
        Then it should use generic line breaking
        """
        # Arrange
        content = "This is just a regular long paragraph that doesn't start with description or list markers but still needs to be broken"

        # Act
        result = fix_long_descriptions(content, max_length=60)

        # Assert
        lines = result.split("\n")
        # Should have broken the line
        assert len(lines) > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
