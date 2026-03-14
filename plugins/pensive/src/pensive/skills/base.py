"""
Base classes for pensive review skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from ..utils.content_parser import ContentParser
from ..utils.severity_mapper import SeverityMapper


@dataclass
class ReviewFinding:
    """A finding from a code review."""

    file: str
    line: int
    severity: str
    category: str
    message: str
    suggestion: str = ""
    code_snippet: str = ""


@dataclass
class ApiExport:
    """Represents an exported API element."""

    name: str
    export_type: str  # function, class, interface, const, etc.
    visibility: str = "public"
    documentation: str = ""
    line: int = 0


@dataclass
class AnalysisResult:
    """Result of an analysis operation."""

    issues: list[ReviewFinding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)


class BaseReviewSkill:
    """Base class for all review skills with shared utilities."""

    skill_name: ClassVar[str] = "base"
    supported_languages: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the skill."""
        self.findings: list[ReviewFinding] = []
        self._parser = ContentParser()
        self._severity = SeverityMapper()

    def analyze(self, _context: Any, _file_path: str) -> AnalysisResult:
        """Analyze a file and return findings.

        Subclasses should override this method to implement specific analysis.
        """
        return AnalysisResult()

    def generate_report(self, findings: list[ReviewFinding]) -> str:
        """Generate a summary report from findings."""
        if not findings:
            return "No issues found."

        lines = [f"Found {len(findings)} issue(s):", ""]
        for finding in findings:
            lines.append(f"- [{finding.severity}] {finding.file}:{finding.line}")
            lines.append(f"  {finding.message}")
            if finding.suggestion:
                lines.append(f"  Suggestion: {finding.suggestion}")
            lines.append("")

        return "\n".join(lines)

    # ========================================================================
    # Shared utility methods
    # ========================================================================

    def _get_code_content(self, context: Any, filename: str = "") -> str:
        """Get file content from context.

        Args:
            context: Skill context with file access
            filename: Optional filename

        Returns:
            File content as string
        """
        return self._parser.get_file_content(context, filename)

    def _find_line_number(self, content: str, position: int) -> int:
        """Find line number for a character position.

        Args:
            content: Full content
            position: Character position

        Returns:
            Line number (1-indexed)
        """
        return self._parser.find_line_number(content, position)

    def _extract_code_snippet(self, content: str, line: int, context: int = 0) -> str:
        """Extract code snippet around a line.

        Args:
            content: Full content
            line: Line number
            context: Context lines before/after

        Returns:
            Code snippet
        """
        return self._parser.extract_code_snippet(content, line, context)

    def _categorize_severity(
        self,
        issues: list[dict[str, Any]],
        custom_map: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Categorize issues by severity.

        Args:
            issues: List of issue dicts
            custom_map: Optional custom severity mapping

        Returns:
            Categorized issues
        """
        return self._severity.categorize(issues, custom_map)
