"""PR review knowledge capture entry point (AR-05)."""

from __future__ import annotations

from typing import Any

from .entry import ReviewEntry
from .manager import ProjectPalaceManager
from .rooms import ReviewSubroom


def capture_pr_review_knowledge(  # noqa: PLR0913 - PR capture requires all review context fields
    repo_name: str,
    pr_number: int,
    pr_title: str,
    findings: list[dict[str, Any]],
    participants: list[str],
    config_path: str | None = None,
) -> list[str]:
    """Capture knowledge from PR review findings.

    This is the main integration point for sanctum:pr-review.
    It evaluates findings and creates appropriate review entries.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        pr_number: PR number
        pr_title: PR title
        findings: List of review findings with severity and content
        participants: List of PR participants
        config_path: Optional path to configuration file

    Returns:
        List of created entry IDs

    """
    manager = ProjectPalaceManager(config_path)
    palace = manager.get_or_create_project_palace(repo_name)

    created_ids = []
    source_pr = f"#{pr_number} - {pr_title}"

    for finding in findings:
        # Classify finding into room type
        room_type = _classify_finding(finding)
        if not room_type:
            continue

        # Create review entry
        entry = ReviewEntry(
            source_pr=source_pr,
            title=finding.get("title", "Untitled Finding"),
            room_type=room_type,
            content={
                "decision": finding.get("description", ""),
                "context": finding.get("context", []),
                "captured_knowledge": {
                    "severity": finding.get("severity", "SUGGESTION"),
                    "category": finding.get("category", "general"),
                    "file": finding.get("file", ""),
                    "line": finding.get("line", ""),
                },
                "connected_concepts": finding.get("related", []),
            },
            participants=participants,
            tags=finding.get("tags", []),
        )

        if manager.add_review_entry(palace["id"], entry):
            created_ids.append(entry.id)

    return created_ids


def _classify_finding(finding: dict[str, Any]) -> str | None:
    """Classify a finding into a review chamber room type.

    Args:
        finding: Finding dictionary with severity and content

    Returns:
        Room type string or None if not worth capturing

    """
    severity = finding.get("severity", "").upper()
    category = finding.get("category", "").lower()

    # Architectural decisions (BLOCKING with architectural context)
    if severity == "BLOCKING" and any(
        kw in category for kw in ["architecture", "design", "pattern", "security"]
    ):
        return ReviewSubroom.DECISIONS

    # Recurring patterns (IN-SCOPE issues that represent patterns)
    if severity in ["BLOCKING", "IN-SCOPE"] and any(
        kw in category for kw in ["pattern", "recurring", "common", "best-practice"]
    ):
        return ReviewSubroom.PATTERNS

    # Quality standards (code quality findings)
    if severity in ["BLOCKING", "IN-SCOPE"] and any(
        kw in category for kw in ["quality", "style", "convention", "standard"]
    ):
        return ReviewSubroom.STANDARDS

    # Lessons learned (post-mortems, retrospective insights)
    if any(kw in category for kw in ["lesson", "learning", "retrospective", "insight"]):
        return ReviewSubroom.LESSONS

    # High-severity findings are worth capturing as patterns
    if severity == "BLOCKING":
        return ReviewSubroom.PATTERNS

    return None


__all__ = ["_classify_finding", "capture_pr_review_knowledge"]
