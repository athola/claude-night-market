"""Provide PR preparation utilities.

Analyze changes, validate quality gates, and prepare pull request descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _is_test_path(path: str) -> bool:
    """Say whether *path* is a test, by path segment rather than substring.

    A substring match calls ``plugins/latest/x.py`` a test.
    """
    segments = path.split("/")
    name = segments[-1]
    return (
        "tests" in segments
        or "test" in segments
        or "__tests__" in segments
        or name.startswith("test_")
        or name.endswith(
            (
                "_test.py",
                "_test.rs",
                "_test.go",
                ".test.ts",
                ".test.js",
                ".spec.ts",
                ".spec.js",
                "_spec.rb",
            )
        )
    )


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
    """Analyze repository changes for pull request preparation."""

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
            context: Dictionary containing 'commits' and 'changed_files'.

        Returns:
            BreakingChanges analysis results.

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
    def initialize_quality_gates() -> dict[str, bool | None]:
        """Initialize every quality gate as not yet evaluated.

        ``None`` means no check has run. A gate seeded ``True`` is a gate
        that cannot fail, and the only consumer of these values renders
        them for a human, so an unevaluated gate must be distinguishable
        from a passing one.

        Returns:
            Dictionary of quality gate names to None

        """
        return dict.fromkeys(PRPrepAnalyzer.QUALITY_GATES, None)

    @staticmethod
    def validate_quality_gates(
        context: dict[str, Any],
        gates: dict[str, bool | None],
    ) -> dict[str, bool | None]:
        """Validate the gates that the changed-file list can decide.

        ``passes_checks`` and ``includes_breaking_changes`` need a test,
        lint or type run and a release decision respectively, neither of
        which this context carries, so they are left untouched.

        Args:
            context: PR context with changes and metadata
            gates: Current quality gate status

        Returns:
            Updated quality gates

        """
        updated_gates = dict(gates)
        changed_files = context.get("changed_files", [])
        paths = [
            f.get("path", "") if isinstance(f, dict) else str(f) for f in changed_files
        ]

        updated_gates["has_tests"] = any(_is_test_path(p) for p in paths)
        updated_gates["has_documentation"] = any(p.endswith(".md") for p in paths)
        updated_gates["describes_changes"] = bool(changed_files)
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
            context: PR context containing changed_files and metadata.

        Returns:
            Generated PR description text.

        """
        changed_files = context.get("changed_files", [])
        if not changed_files:
            return "No changes detected"

        paths = [
            f.get("path", "") if isinstance(f, dict) else str(f) for f in changed_files
        ]
        lines = [f"## Changes ({len(paths)} files)", ""]
        for p in paths:
            lines.append(f"- {p}")
        return "\n".join(lines)
