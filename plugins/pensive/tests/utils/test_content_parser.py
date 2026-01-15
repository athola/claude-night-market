"""Unit tests for the content parser utility.

Tests line number finding, code snippet extraction,
and content manipulation helpers.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from pensive.utils.content_parser import ContentParser


class TestContentParser:
    """Test suite for ContentParser utility class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.parser = ContentParser()
        self.sample_content = """def hello():
    print("Hello, World!")
    return True

def goodbye():
    print("Goodbye!")
    return False

class MyClass:
    def __init__(self):
        self.value = 42
"""

    # ========================================================================
    # find_line_number tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_line_number_at_start(self) -> None:
        """Given position at file start, returns line 1."""
        # Act
        line = ContentParser.find_line_number(self.sample_content, 0)

        # Assert
        assert line == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_line_number_after_newlines(self) -> None:
        """Given position after newlines, returns correct line number."""
        # Arrange
        # First newline is after "def hello():" (index ~12)
        # Second newline is after the print statement

        # Act - position at start of "def goodbye():" (line 5)
        position = self.sample_content.index("def goodbye")
        line = ContentParser.find_line_number(self.sample_content, position)

        # Assert
        assert line == 5

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_line_number_middle_of_file(self) -> None:
        """Given position in middle, returns accurate line number."""
        # Arrange - find "class MyClass"
        position = self.sample_content.index("class MyClass")

        # Act
        line = ContentParser.find_line_number(self.sample_content, position)

        # Assert
        assert line == 9

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_line_number_at_end(self) -> None:
        """Given position at end of file, returns correct line number."""
        # Arrange - position at the last newline character
        position = len(self.sample_content) - 1

        # Act
        line = ContentParser.find_line_number(self.sample_content, position)

        # Assert - the last newline is at the end of line 11 (before empty line 12)
        # find_line_number counts newlines BEFORE the position
        assert line == 11

    # ========================================================================
    # extract_code_snippet tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_single_line_no_context(self) -> None:
        """Given line number with no context, returns just that line."""
        # Act
        snippet = ContentParser.extract_code_snippet(
            self.sample_content, 2, context_lines=0
        )

        # Assert
        assert snippet == 'print("Hello, World!")'

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_with_context_lines(self) -> None:
        """Given line with context, returns surrounding lines."""
        # Act
        snippet = ContentParser.extract_code_snippet(
            self.sample_content, 2, context_lines=1
        )

        # Assert
        assert "def hello():" in snippet
        assert 'print("Hello, World!")' in snippet
        assert "return True" in snippet

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_at_file_start(self) -> None:
        """Given first line with context, handles boundary correctly."""
        # Act
        snippet = ContentParser.extract_code_snippet(
            self.sample_content, 1, context_lines=2
        )

        # Assert
        assert "def hello():" in snippet
        # Should not crash or include negative indices

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_at_file_end(self) -> None:
        """Given last line with context, handles boundary correctly."""
        # Arrange
        lines = self.sample_content.split("\n")
        last_line = len(lines)

        # Act
        snippet = ContentParser.extract_code_snippet(
            self.sample_content, last_line, context_lines=2
        )

        # Assert - should contain last few lines without error
        assert "self.value = 42" in snippet

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_invalid_line_number(self) -> None:
        """Given invalid line number, returns empty string."""
        # Act
        snippet_zero = ContentParser.extract_code_snippet(self.sample_content, 0)
        snippet_negative = ContentParser.extract_code_snippet(self.sample_content, -1)
        snippet_too_large = ContentParser.extract_code_snippet(
            self.sample_content, 1000
        )

        # Assert
        assert snippet_zero == ""
        assert snippet_negative == ""
        assert snippet_too_large == ""

    # ========================================================================
    # get_file_content tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_file_content_from_context(self) -> None:
        """Given context with get_file_content method, extracts content."""
        # Arrange
        mock_context = Mock()
        mock_context.get_file_content.return_value = "file content here"

        # Act
        content = ContentParser.get_file_content(mock_context)

        # Assert
        assert content == "file content here"
        mock_context.get_file_content.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_file_content_with_filename(self) -> None:
        """Given filename, calls context with specific file."""
        # Arrange
        mock_context = Mock()
        mock_context.get_file_content.return_value = "specific file content"

        # Act
        content = ContentParser.get_file_content(mock_context, "myfile.py")

        # Assert
        assert content == "specific file content"
        mock_context.get_file_content.assert_called_once_with("myfile.py")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_file_content_missing_method(self) -> None:
        """Given context without method, returns empty string."""
        # Arrange
        mock_context = Mock(spec=[])  # No methods

        # Act
        content = ContentParser.get_file_content(mock_context)

        # Assert
        assert content == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_file_content_non_string_return(self) -> None:
        """Given context returning non-string, returns empty string."""
        # Arrange
        mock_context = Mock()
        mock_context.get_file_content.return_value = None

        # Act
        content = ContentParser.get_file_content(mock_context)

        # Assert
        assert content == ""

    # ========================================================================
    # extract_lines_range tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_lines_range_middle(self) -> None:
        """Given valid range, extracts lines inclusively."""
        # Act
        extracted = ContentParser.extract_lines_range(self.sample_content, 5, 7)

        # Assert
        assert len(extracted.split("\n")) == 3  # 3 lines extracted
        assert "def goodbye():" in extracted
        assert 'print("Goodbye!")' in extracted
        assert "return False" in extracted

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_lines_range_single_line(self) -> None:
        """Given same start and end, extracts single line."""
        # Act
        extracted = ContentParser.extract_lines_range(self.sample_content, 1, 1)

        # Assert
        assert extracted == "def hello():"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_lines_range_handles_boundaries(self) -> None:
        """Given out-of-bounds range, clips to valid lines."""
        # Act
        extracted = ContentParser.extract_lines_range(self.sample_content, 0, 1000)

        # Assert - should contain all content
        assert "def hello():" in extracted
        assert "self.value = 42" in extracted

    # ========================================================================
    # count_lines tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_count_lines_normal_content(self) -> None:
        """Given multi-line content, counts correctly."""
        # Act
        count = ContentParser.count_lines(self.sample_content)

        # Assert
        assert count == 12

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_count_lines_single_line(self) -> None:
        """Given single line content, returns 1."""
        # Act
        count = ContentParser.count_lines("single line no newline")

        # Assert
        assert count == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_count_lines_empty_string(self) -> None:
        """Given empty string, returns 1 (empty line)."""
        # Act
        count = ContentParser.count_lines("")

        # Assert
        assert count == 1

    # ========================================================================
    # strip_comments tests
    # ========================================================================

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strip_comments_python_style(self) -> None:
        """Given Python comments, strips them correctly."""
        # Arrange
        code = """x = 1  # inline comment
# full line comment
y = 2
"""

        # Act
        stripped = ContentParser.strip_comments(code)

        # Assert
        assert "# inline comment" not in stripped
        assert "# full line comment" not in stripped
        assert "x = 1" in stripped
        assert "y = 2" in stripped

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strip_comments_custom_char(self) -> None:
        """Given custom comment char, uses it for stripping."""
        # Arrange
        code = """value = 10 ; this is a comment
; another comment
result = 20
"""

        # Act
        stripped = ContentParser.strip_comments(code, comment_char=";")

        # Assert
        assert "this is a comment" not in stripped
        assert "value = 10" in stripped
        assert "result = 20" in stripped

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strip_comments_preserves_non_comment_lines(self) -> None:
        """Given code without comments, preserves all code lines."""
        # Arrange
        code = """def foo():
    return bar
"""

        # Act
        stripped = ContentParser.strip_comments(code)

        # Assert
        assert "def foo():" in stripped
        assert "return bar" in stripped
