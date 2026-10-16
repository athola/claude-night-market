"""Severity categorization utilities for review skills."""

from __future__ import annotations

import re
from typing import Any

# Common severity mappings across review types
SEVERITY_MAP: dict[str, str] = {
    # Critical issues
    "sql_injection": "critical",
    "timing_attack": "critical",
    "security": "critical",
    "command_injection": "critical",
    "privilege_escalation": "critical",
    "buffer_overflow": "critical",
    "data_race": "critical",
    # High severity issues
    "null_pointer": "high",
    "race_condition": "high",
    "memory_leak": "high",
    "unsafe_code": "high",
    "authorization": "high",
    "deprecated_dependency": "high",
    # Medium severity issues
    "resource_leak": "medium",
    "off_by_one": "medium",
    "logical_error": "medium",
    "integer_overflow": "medium",
    "unwrap_usage": "medium",
    "missing_docs": "medium",
    "layering_violation": "medium",
    # Low severity issues
    "type_confusion": "low",
    "performance": "low",
    "style": "low",
}


# Matched on word boundaries. A plain substring test escalated
# "this highlights a minor slowdown", "the highest-traffic path" and
# "higher memory use" to high severity, because each contains "high".
_HIGH_SEVERITY_WORDS = re.compile(r"\b(?:high|dangerous)\b")
# The lookbehind keeps "non-critical" and "insecurity" from matching.
_CRITICAL_SEVERITY_WORDS = re.compile(
    r"(?<![\w-])(?:sql injection|security|critical)\b"
)


def categorize(
    issues: list[dict[str, Any]],
    custom_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Categorize issues by severity.

    Args:
        issues: List of issue dictionaries with 'type' key
        custom_map: Optional custom severity mapping

    Returns:
        List of issues with 'severity' field added
    """
    severity_map = SEVERITY_MAP.copy()
    if custom_map:
        severity_map.update(custom_map)

    categorized = []
    for issue in issues:
        issue_copy = issue.copy()
        issue_type = issue.get("type", "").lower()
        issue_copy["severity"] = severity_map.get(issue_type, "low")

        # Description keywords only escalate; a "high" keyword on a
        # type already mapped critical must not lower it.
        issue_desc = issue.get("issue", "").lower()
        if _CRITICAL_SEVERITY_WORDS.search(issue_desc):
            issue_copy["severity"] = "critical"
        elif (
            _HIGH_SEVERITY_WORDS.search(issue_desc)
            and issue_copy["severity"] != "critical"
        ):
            issue_copy["severity"] = "high"

        categorized.append(issue_copy)

    return categorized


def get_severity_weight(severity: str) -> float:
    """Convert severity level to numeric weight."""
    weights = {
        "low": 1.0,
        "medium": 2.5,
        "high": 5.0,
        "critical": 10.0,
    }
    return weights.get(severity.lower(), 1.0)


# harden emits ADVISORY for uncited findings, and the structured-output
# format defines INFO. Neither has its own column in a summary.
_LOW_ALIASES = frozenset({"advisory", "info"})
_LEVELS = ("critical", "high", "medium", "low")


def normalize_severity(raw: Any) -> str:
    """Return the summary column for ``raw``, or raise ``ValueError``.

    Folding an undefined level into low would hide a producer emitting a
    level nothing defines.
    """
    severity = raw.strip().lower() if isinstance(raw, str) else None
    if severity in _LOW_ALIASES:
        return "low"
    if severity not in _LEVELS:
        raise ValueError(f"unknown severity {raw!r}")
    return severity


def count_by_severity(issues: list[dict[str, Any]]) -> dict[str, int]:
    """Count issues by severity level.

    An issue with no ``severity`` key counts as low. Other levels go
    through ``normalize_severity``, which raises on an undefined one.
    """
    counts = dict.fromkeys(_LEVELS, 0)
    for issue in issues:
        counts[normalize_severity(issue.get("severity", "low"))] += 1
    return counts
