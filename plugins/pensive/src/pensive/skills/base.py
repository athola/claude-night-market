"""Base classes for pensive review skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    """Base class for all review skills."""

    skill_name: str = "base"
    supported_languages: list[str] = []

    def __init__(self) -> None:
        """Initialize the skill."""
        self.findings: list[ReviewFinding] = []

    def analyze(self, context: Any, file_path: str) -> AnalysisResult:
        """Analyze a file and return findings."""
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
