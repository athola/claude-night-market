"""Shared report formatting for plugin validators.

Provides a common report structure used by imbue_validator,
abstract_validator, and other plugin validation scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def format_validator_report(  # noqa: PLR0913 - report formatting needs all fields
    title: str,
    plugin_root: Path,
    skill_file_count: int,
    metadata: list[tuple[str, Any]],
    issues: list[str],
    success_message: str = "All validations passed successfully!",
) -> str:
    """Format a standard plugin validation report.

    Args:
        title: Report title (e.g., "Imbue Plugin Review Workflow Report").
        plugin_root: Root directory of the plugin being validated.
        skill_file_count: Number of skill files found.
        metadata: List of (label, value) pairs for domain-specific
            summary lines shown between the header and issues section.
        issues: List of issue descriptions to enumerate.
        success_message: Message shown when no issues are found.
            Defaults to "All validations passed successfully!".

    Returns:
        Formatted report string.

    """
    report = [title, "=" * 50]
    report.append(f"\nPlugin Root: {plugin_root}")
    report.append(f"Skill Files: {skill_file_count}")

    for label, value in metadata:
        report.append(f"\n{label}: {value}")

    if issues:
        report.append(f"\nIssues Found ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            report.append(f"  {i}. {issue}")
    else:
        report.append(f"\n{success_message}")

    return "\n".join(report)
