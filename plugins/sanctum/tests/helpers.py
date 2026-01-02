# ruff: noqa: D101,D102,D103
"""Test helper utilities for Sanctum agent tests.

This module contains shared helper functions used across test files,
following the principle that test classes should not contain
implementation logic.
"""

from __future__ import annotations

# Constants
MAX_COMMIT_MESSAGE_LENGTH = 80

# Git Status and Diff Parsing Helpers


def parse_git_status(status: str) -> dict[str, list[str]]:
    """Parse git status porcelain output into categorized changes.

    Args:
        status: Git status output in porcelain format

    Returns:
        Dictionary with keys: modified, added, deleted, untracked

    """
    changes = {"modified": [], "added": [], "deleted": [], "untracked": []}
    for line in status.splitlines():
        if line.startswith("M "):
            changes["modified"].append(line.split()[1])
        elif line.startswith("A "):
            changes["added"].append(line.split()[1])
        elif line.startswith("D "):
            changes["deleted"].append(line.split()[1])
        elif line.startswith("?? "):
            changes["untracked"].append(line.split()[1])
    return changes


def parse_git_stats(stats: str) -> dict[str, int]:
    """Parse git diff stats into addition/deletion counts.

    Args:
        stats: Git diff stats output

    Returns:
        Dictionary with total_additions and total_deletions

    """
    lines = [line for line in stats.splitlines() if line.strip()]
    additions = int(lines[0]) if lines and lines[0].isdigit() else 0
    deletions = sum(int(line) for line in lines[1:] if line.isdigit())
    return {
        "total_additions": additions,
        "total_deletions": deletions,
    }


# Todo Creation Helpers


def create_analysis_todos(analysis: dict) -> list[dict]:
    """Create todo items from repository analysis results.

    Args:
        analysis: Analysis results dictionary

    Returns:
        List of todo items with content and status

    """
    return [
        {"content": "Verify repository status", "status": "completed"},
        {"content": "Check staged changes", "status": "completed"},
        {"content": "Summarize change summary", "status": "completed"},
    ]


# Error Handling Helpers


def handle_git_error(error: str) -> list[str]:
    """Generate recovery suggestions for common Git errors.

    Args:
        error: Git error message

    Returns:
        List of suggested recovery actions

    """
    if "not a git repository" in error:
        return ["git init", "git clone <repo>"]
    if "couldn't find remote ref" in error:
        return ["git branch -m main", "git push origin main"]
    if "permission denied" in error.lower():
        return ["Check file permissions", "Run as appropriate user"]
    return ["Check Git status for details"]


# Workflow Recommendation Helpers


def generate_workflow_recommendations(context: dict) -> list[str]:
    """Generate workflow recommendations based on repository context.

    Args:
        context: Repository state context dictionary

    Returns:
        List of recommended next steps

    """
    recs = []
    if context.get("has_staged_changes"):
        recs.append("Commit staged changes using commit-messages skill")
    if context.get("has_unstaged_changes"):
        recs.append("Stage pending changes with git add")
    if context.get("is_clean"):
        recs.append("Workspace clean - push or open PR")
    return recs


# Commit Message Helpers


def validate_commit_message(message: str) -> bool:
    """Validate commit message follows conventional commits format.

    Args:
        message: Commit message to validate

    Returns:
        True if message is valid, False otherwise

    """
    if not message or ":" not in message:
        return False
    type_part, _, description = message.partition(":")
    if not type_part or not description.strip():
        return False
    return len(message) <= MAX_COMMIT_MESSAGE_LENGTH


def generate_complex_commit_message(context: dict) -> str:
    """Generate a commit message for complex multi-file changes.

    Args:
        context: Change context with staged files and breaking changes

    Returns:
        Formatted commit message

    """
    # Determine primary change type from staged files
    # Priority: feature > fix > other types
    types = [f.get("type", "feat") for f in context.get("staged_files", [])]

    # Prefer "feat" or "feature" type for primary commits
    if "feature" in types or "feat" in types:
        primary_type = "feat"
    else:
        primary_type = max(set(types), key=types.count) if types else "feat"

    # Add breaking change indicator
    if context.get("breaking_changes"):
        type_prefix = f"{primary_type}!"
    else:
        type_prefix = primary_type

    # Generate description
    has_tests = any(f.get("type") == "test" for f in context.get("staged_files", []))
    has_docs = any(f.get("type") == "docs" for f in context.get("staged_files", []))

    description = "Add API changes"
    details = []
    if has_tests:
        details.append("tests")
    if has_docs:
        details.append("update documentation")

    # Construct message
    return f"{type_prefix}: {description}"


# Pull Request Helpers


def generate_pr_description(context: dict) -> str:
    """Generate a detailed PR description.

    Args:
        context: PR context with title, description, and changes

    Returns:
        Formatted PR description with all required sections

    """
    sections = [
        "## Summary",
        "## Changes Made",
        "## Test Plan",
        "## Breaking Changes",
        "## Checklist",
    ]
    return "\n\n".join(sections)


def check_quality_gates(gates: dict[str, bool]) -> dict[str, str]:
    """Check PR quality gates and return status.

    Args:
        gates: Dictionary of gate names to boolean pass/fail

    Returns:
        Dictionary mapping gate names to status strings

    """
    status = {}
    for gate, passed in gates.items():
        if gate == "has_description":
            status["description_check"] = "passed" if passed else "failed"
        elif gate == "has_tests":
            status["test_check"] = "passed" if passed else "failed"
        elif gate == "has_documentation":
            status["documentation_check"] = "passed" if passed else "failed"
        elif gate == "passes_ci":
            status["ci_check"] = "passed" if passed else "failed"
        elif gate == "has_breaking_changes":
            status["breaking_changes_check"] = "passed" if passed else "failed"

    # Determine overall status
    if any(v == "failed" for v in status.values()):
        status["overall_status"] = "failed"
    else:
        status["overall_status"] = "passed"

    return status


def suggest_reviewers(
    context: dict,
    reviewer_map: dict[str, list[str]],
) -> list[str]:
    """Suggest reviewers based on changed files and reviewer mapping.

    Args:
        context: PR context with changed_files list
        reviewer_map: Mapping of file prefixes to reviewer teams

    Returns:
        Sorted list of suggested reviewers

    """
    reviewers: set[str] = set()
    for file_change in context.get("changed_files", []):
        for prefix, teams in reviewer_map.items():
            if file_change.startswith(prefix):
                reviewers.update(teams)
    return sorted(reviewers)
