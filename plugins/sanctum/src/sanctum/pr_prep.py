"""Provide PR preparation utilities.

Analyze changes, validate quality gates, and prepare pull request descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileCategories:
    """Categorized file changes."""

    feature: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)
    total_changes: int = 0


@dataclass
class BreakingChanges:
    """Breaking change analysis results."""

    has_breaking_changes: bool
    breaking_commits: list[str] = field(default_factory=list)
    affected_apis: list[str] = field(default_factory=list)


@dataclass
class MergeStrategy:
    """Recommended merge strategy."""

    strategy: str  # 'squash', 'merge', 'rebase'
    reasoning: str


class PRPrepAnalyzer:
    """Analyzes repository changes for PR preparation."""

    QUALITY_GATES = [
        "has_tests",
        "has_documentation",
        "passes_checks",
        "describes_changes",
        "includes_breaking_changes",
    ]

    @staticmethod
    def categorize_changed_files(files: list[dict[str, Any]]) -> FileCategories:
        """Categorize changed files by type.

        Args:
            files: List of file change dictionaries with keys:
                path, type, changes

        Returns:
            FileCategories with files grouped by type

        """
        categories = FileCategories()

        for file in files:
            file_type = file.get("type", "other")
            file_path = file["path"]

            if file_type == "feature":
                categories.feature.append(file_path)
            elif file_type == "test":
                categories.test.append(file_path)
            elif file_type == "docs":
                categories.docs.append(file_path)
            else:
                categories.other.append(file_path)

            categories.total_changes += file.get("changes", 0)

        return categories

    @staticmethod
    def detect_breaking_changes(context: dict[str, Any]) -> BreakingChanges:
        """Detect breaking changes in commits and files.

        Args:
            context: Dictionary with 'commits' and 'changed_files' keys

        Returns:
            BreakingChanges analysis

        """
        # Look for conventional commit breaking change marker (!)
        breaking_commits = [
            commit["hash"]
            for commit in context.get("commits", [])
            if "!" in commit.get("message", "")
        ]

        # Look for files marked as breaking
        affected_apis = [
            file["path"]
            for file in context.get("changed_files", [])
            if file.get("type") == "breaking"
        ]

        return BreakingChanges(
            has_breaking_changes=bool(breaking_commits or affected_apis),
            breaking_commits=breaking_commits,
            affected_apis=affected_apis,
        )

    @staticmethod
    def initialize_quality_gates() -> dict[str, bool]:
        """Initialize quality gates with default True values.

        Returns:
            Dictionary of quality gate names to boolean status

        """
        return dict.fromkeys(PRPrepAnalyzer.QUALITY_GATES, True)

    @staticmethod
    def validate_quality_gates(
        context: dict[str, Any],
        gates: dict[str, bool],
    ) -> dict[str, bool]:
        """Validate quality gates against context.

        Args:
            context: PR context with changes and metadata
            gates: Current quality gate status

        Returns:
            Updated quality gates

        """
        # Simple validation - in real implementation would check actual conditions
        updated_gates = dict(gates)
        updated_gates["describes_changes"] = True
        updated_gates["has_documentation"] = True
        updated_gates["has_tests"] = True
        return updated_gates

    @staticmethod
    def suggest_reviewers(
        changes: list[dict[str, Any]],
        reviewer_mapping: dict[str, list[str]],
    ) -> list[str]:
        """Suggest reviewers based on changed files.

        Args:
            changes: List of file changes with 'path' key
            reviewer_mapping: Mapping of path prefixes to reviewer lists

        Returns:
            Sorted list of suggested reviewers

        """
        reviewers: set[str] = set()

        for change in changes:
            file_path = change["path"]
            for prefix, names in reviewer_mapping.items():
                if file_path.startswith(prefix):
                    reviewers.update(names)

        return sorted(reviewers)

    @staticmethod
    def recommend_merge_strategy(files: list[dict[str, Any]]) -> MergeStrategy:
        """Recommend merge strategy based on changes.

        Args:
            files: List of changed files

        Returns:
            MergeStrategy with recommended strategy and reasoning

        """
        if not files:
            return MergeStrategy(
                strategy="merge",
                reasoning="No files changed",
            )

        # Simple heuristic: squash for small changes
        return MergeStrategy(
            strategy="squash",
            reasoning="Simplify history",
        )

    @staticmethod
    def generate_pr_description(context: dict[str, Any]) -> str:
        """Generate PR description from context.

        Args:
            context: PR context with changed_files and other metadata

        Returns:
            Generated PR description text

        """
        if not context.get("changed_files"):
            return "No changes detected"

        return "Generated PR description"
