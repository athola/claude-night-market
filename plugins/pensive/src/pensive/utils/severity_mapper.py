"""Severity categorization utilities for review skills."""

from __future__ import annotations

from typing import Any, ClassVar


class SeverityMapper:
    """Map issue types to severity levels."""

    # Common severity mappings across review types
    SEVERITY_MAP: ClassVar[dict[str, str]] = {
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

    @classmethod
    def categorize(
        cls,
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
        severity_map = cls.SEVERITY_MAP.copy()
        if custom_map:
            severity_map.update(custom_map)

        categorized = []
        for issue in issues:
            issue_copy = issue.copy()
            issue_type = issue.get("type", "").lower()
            issue_copy["severity"] = severity_map.get(issue_type, "low")

            # Override with issue description keywords
            issue_desc = issue.get("issue", "").lower()
            if any(
                keyword in issue_desc
                for keyword in ["sql injection", "security", "critical"]
            ):
                issue_copy["severity"] = "critical"
            elif any(keyword in issue_desc for keyword in ["high", "dangerous"]):
                issue_copy["severity"] = "high"

            categorized.append(issue_copy)

        return categorized

    @staticmethod
    def get_severity_weight(severity: str) -> float:
        """Convert severity level to numeric weight.

        Args:
            severity: Severity level (low, medium, high, critical)

        Returns:
            Numeric weight for the severity
        """
        weights = {
            "low": 1.0,
            "medium": 2.5,
            "high": 5.0,
            "critical": 10.0,
        }
        return weights.get(severity.lower(), 1.0)

    @staticmethod
    def count_by_severity(issues: list[dict[str, Any]]) -> dict[str, int]:
        """Count issues by severity level.

        Args:
            issues: List of categorized issues

        Returns:
            Dictionary mapping severity to count
        """
        counts: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for issue in issues:
            severity = issue.get("severity", "low").lower()
            if severity in counts:
                counts[severity] += 1

        return counts
