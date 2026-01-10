"""Markdown report generation utilities for review skills."""

from __future__ import annotations

from typing import Any


class MarkdownReportGenerator:
    """Generate markdown-formatted reports from analysis data."""

    @staticmethod
    def create_section(title: str, level: int = 2) -> str:
        """Create a markdown section header.

        Args:
            title: Section title
            level: Header level (1-6)

        Returns:
            Markdown header string
        """
        return f"{'#' * level} {title}\n"

    @staticmethod
    def create_list_item(content: str, indent: int = 0) -> str:
        """Create a markdown list item.

        Args:
            content: List item content
            indent: Indentation level

        Returns:
            Markdown list item string
        """
        prefix = "  " * indent
        return f"{prefix}- {content}\n"

    @staticmethod
    def create_code_block(content: str, language: str = "") -> str:
        """Create a markdown code block.

        Args:
            content: Code content
            language: Syntax highlighting language

        Returns:
            Markdown code block string
        """
        return f"```{language}\n{content}\n```\n"

    @staticmethod
    def create_score_line(label: str, score: float, max_score: float = 10.0) -> str:
        """Create a score display line.

        Args:
            label: Score label
            score: Actual score
            max_score: Maximum possible score

        Returns:
            Formatted score string
        """
        return f"**{label}**: {score}/{max_score}\n"

    @staticmethod
    def create_table_header(columns: list[str]) -> str:
        """Create a markdown table header.

        Args:
            columns: Column names

        Returns:
            Markdown table header
        """
        header = "| " + " | ".join(columns) + " |\n"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |\n"
        return header + separator

    @staticmethod
    def create_table_row(values: list[str]) -> str:
        """Create a markdown table row.

        Args:
            values: Row values

        Returns:
            Markdown table row
        """
        return "| " + " | ".join(values) + " |\n"

    @classmethod
    def create_report(
        cls,
        title: str,
        sections: list[dict[str, Any]],
    ) -> str:
        """Create a complete markdown report.

        Args:
            title: Report title
            sections: List of section dicts with 'title', 'content', 'type' keys

        Returns:
            Complete markdown report
        """
        lines = [cls.create_section(title, level=1), ""]

        for section in sections:
            section_title = section.get("title", "")
            section_content = section.get("content", [])
            section_type = section.get("type", "text")

            if section_title:
                lines.append(cls.create_section(section_title, level=2))
                lines.append("")

            if section_type == "list":
                for item in section_content:
                    lines.append(cls.create_list_item(str(item)))
            elif section_type == "table":
                headers = section.get("headers", [])
                if headers:
                    lines.append(cls.create_table_header(headers))
                    for row in section_content:
                        lines.append(cls.create_table_row(row))
            elif section_type == "score":
                score = section.get("score", 0.0)
                max_score = section.get("max_score", 10.0)
                lines.append(cls.create_score_line(section_title, score, max_score))
            else:  # text
                lines.append(str(section_content))

            lines.append("")

        return "\n".join(lines)
