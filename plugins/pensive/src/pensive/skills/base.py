"""
Base classes for pensive review skills."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, ClassVar


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


@dataclass
class PatternSearch:
    """Configuration for a pattern detection scan."""

    patterns: list[tuple[str, str]]
    bug_type: str = ""
    re_flags: int = 0


class BaseReviewSkill:
    """Base class for all review skills with shared utilities."""

    skill_name: ClassVar[str] = "base"
    supported_languages: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the skill."""
        self.findings: list[ReviewFinding] = []

    def analyze(self, _context: Any, _file_path: str) -> AnalysisResult:
        """Analyze a file and return findings.

        Subclasses should override this method to implement specific analysis.
        """
        return AnalysisResult()

    def _detect_patterns(
        self,
        context: Any,
        filename: str,
        patterns: list[tuple[str, str]],
        content_parser: Any,
        *,
        search: PatternSearch | None = None,
    ) -> list[dict[str, str]]:
        """Detect regex patterns in file content and return findings.

        Args:
            context: Skill context with file access methods.
            filename: File to scan.
            patterns: List of (regex_pattern, issue_description) tuples.
            content_parser: Module or object with get_file_content and
                find_line_number helpers.
            search: Optional PatternSearch with bug_type and re_flags.
                When omitted, bug_type defaults to "" and re_flags to 0.

        Returns:
            List of finding dicts with keys: type, location, issue, code.
        """
        bug_type = search.bug_type if search else ""
        re_flags = search.re_flags if search else 0
        code = content_parser.get_file_content(context, filename)
        if not code:
            return []
        findings: list[dict[str, str]] = []
        for pattern, issue_desc in patterns:
            for match in re.finditer(pattern, code, re_flags):
                line_num = content_parser.find_line_number(code, match.start())
                findings.append(
                    {
                        "type": bug_type,
                        "location": f"{filename}:{line_num}",
                        "issue": issue_desc,
                        "code": content_parser.extract_code_snippet(code, line_num),
                    }
                )
        return findings

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
