"""Content parsing utilities for review skills."""

from __future__ import annotations

from typing import Any


class ContentParser:
    """Parse and extract information from file content."""

    @staticmethod
    def find_line_number(content: str, match_start: int) -> int:
        """Find line number for a match position in content.

        Args:
            content: Full file content
            match_start: Character position of match

        Returns:
            Line number (1-indexed)
        """
        return content[:match_start].count("\n") + 1

    @staticmethod
    def extract_code_snippet(
        content: str,
        line_num: int,
        context_lines: int = 0,
    ) -> str:
        """Extract code snippet around a specific line.

        Args:
            content: Full file content
            line_num: Target line number (1-indexed)
            context_lines: Number of context lines before/after

        Returns:
            Code snippet as string
        """
        lines = content.split("\n")
        if line_num < 1 or line_num > len(lines):
            return ""

        if context_lines == 0:
            return lines[line_num - 1].strip()

        start = max(0, line_num - 1 - context_lines)
        end = min(len(lines), line_num + context_lines)
        return "\n".join(lines[start:end])

    @staticmethod
    def get_file_content(context: Any, filename: str = "") -> str:
        """Get file content from context if available.

        Args:
            context: Skill context with file access methods
            filename: Optional filename to retrieve

        Returns:
            File content as string, or empty string if context lacks
            get_file_content method or returns non-string value
        """
        if hasattr(context, "get_file_content"):
            if filename:
                content = context.get_file_content(filename)
            else:
                content = context.get_file_content()
            return content if isinstance(content, str) else ""
        return ""

    @staticmethod
    def extract_lines_range(
        content: str,
        start_line: int,
        end_line: int,
    ) -> str:
        """Extract a range of lines from content.

        Args:
            content: Full file content
            start_line: Starting line number (1-indexed, inclusive)
            end_line: Ending line number (1-indexed, inclusive)

        Returns:
            Lines as string
        """
        lines = content.split("\n")
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        return "\n".join(lines[start_idx:end_idx])

    @staticmethod
    def count_lines(content: str) -> int:
        """Count number of lines in content.

        Args:
            content: File content

        Returns:
            Number of lines
        """
        return len(content.split("\n"))

    @staticmethod
    def strip_comments(content: str, comment_char: str = "#") -> str:
        """Strip comments from content.

        Args:
            content: File content
            comment_char: Comment character (default: #)

        Returns:
            Content with comments removed
        """
        lines = content.split("\n")
        stripped_lines = []
        for original_line in lines:
            # Remove inline comments
            line = original_line
            if comment_char in line:
                line = line[: line.index(comment_char)]
            if line.strip():  # Keep non-empty lines
                stripped_lines.append(line)
        return "\n".join(stripped_lines)
