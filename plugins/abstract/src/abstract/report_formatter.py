"""Shared report formatting for plugin validators.

Provides a common report structure used by imbue_validator,
abstract_validator, and other plugin validation scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidatorReport:
    """Inputs for a standard plugin validation report.

    Args:
        title: Report title (e.g., "Imbue Plugin Review Workflow Report").
        plugin_root: Root directory of the plugin being validated.
        skill_file_count: Number of skill files found.
        metadata: List of (label, value) pairs for domain-specific
            summary lines shown between the header and issues section.
        issues: List of issue descriptions to enumerate.
        success_message: Message shown when no issues are found.

    """

    title: str
    plugin_root: Path
    skill_file_count: int
    metadata: list[tuple[str, Any]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    success_message: str = "All validations passed successfully!"


def format_validator_report(report: ValidatorReport) -> str:
    """Format a standard plugin validation report.

    Returns:
        Formatted report string.

    """
    lines = [report.title, "=" * 50]
    lines.append(f"\nPlugin Root: {report.plugin_root}")
    lines.append(f"Skill Files: {report.skill_file_count}")

    for label, value in report.metadata:
        lines.append(f"\n{label}: {value}")

    if report.issues:
        lines.append(f"\nIssues Found ({len(report.issues)}):")
        for i, issue in enumerate(report.issues, 1):
            lines.append(f"  {i}. {issue}")
    else:
        lines.append(f"\n{report.success_message}")

    return "\n".join(lines)
