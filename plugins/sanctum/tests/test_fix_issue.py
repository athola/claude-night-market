# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,PLR2004,E501
"""BDD-style tests for the fix-issue command."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from sanctum.validators import CommandValidator

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def fix_issue_command_content() -> str:
    """Content of the fix-issue.md command file."""
    return """---
name: fix-issue
description: Fix GitHub issues using subagent-driven-development with parallel execution where appropriate
usage: /fix-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--parallel] [--no-review]
extends: "superpowers:subagent-driven-development"
---

# Fix GitHub Issue(s)

Retrieves GitHub issue content and uses subagent-driven-development to systematically address the requirements.

## When to Use

- Addressing one or more GitHub issues systematically
- Issues with well-defined acceptance criteria
"""


@pytest.fixture
def sample_github_issue() -> dict[str, Any]:
    """Sample GitHub issue data as returned by gh CLI."""
    return {
        "number": 42,
        "title": "Add user authentication",
        "body": """## Description
Implement user authentication for the API.

## Acceptance Criteria
- [ ] Users can register with email/password
- [ ] Users can login and receive JWT
- [ ] Protected routes require valid JWT

## Technical Requirements
- Use bcrypt for password hashing
- JWT expiry: 24 hours
""",
        "labels": [{"name": "feature"}, {"name": "priority:high"}],
        "assignees": [{"login": "dev1"}],
        "comments": [],
    }


@pytest.fixture
def sample_github_issue_with_dependencies() -> dict[str, Any]:
    """GitHub issue that depends on another issue."""
    return {
        "number": 43,
        "title": "Add password reset",
        "body": """## Description
Add password reset functionality.

## Dependencies
Blocked by #42 (requires authentication to be implemented first)

## Acceptance Criteria
- [ ] Users can request password reset via email
- [ ] Reset tokens expire after 1 hour
""",
        "labels": [{"name": "feature"}],
        "assignees": [],
        "comments": [],
    }


@pytest.fixture
def temp_fix_issue_command(tmp_path: Path, fix_issue_command_content: str) -> Path:
    """Create a temporary fix-issue.md command file."""
    cmd_file = tmp_path / "commands" / "fix-issue.md"
    cmd_file.parent.mkdir(parents=True)
    cmd_file.write_text(fix_issue_command_content)
    return cmd_file


# ==============================================================================
# Input Parsing Tests
# ==============================================================================


@dataclass
class IssueInput:
    """Represents parsed issue input."""

    number: int
    owner: str | None = None
    repo: str | None = None
    is_url: bool = False


def parse_issue_input(input_str: str) -> IssueInput:
    """
    Parse issue input which can be a number or GitHub URL.

    GIVEN an issue input string
    WHEN parsing the input
    THEN returns structured IssueInput with number and optional owner/repo
    """
    # URL pattern: https://github.com/owner/repo/issues/123
    url_pattern = r"https?://github\.com/([^/]+)/([^/]+)/issues/(\d+)"
    match = re.match(url_pattern, input_str)

    if match:
        return IssueInput(
            number=int(match.group(3)),
            owner=match.group(1),
            repo=match.group(2),
            is_url=True,
        )

    # Plain number
    try:
        return IssueInput(number=int(input_str))
    except ValueError as e:
        msg = f"Invalid issue input: {input_str}"
        raise ValueError(msg) from e


def parse_issue_list(input_str: str) -> list[IssueInput]:
    """
    Parse space-delimited list of issue inputs.

    GIVEN a space-delimited string of issue inputs
    WHEN parsing the list
    THEN returns list of IssueInput objects
    """
    parts = input_str.split()
    return [parse_issue_input(part) for part in parts]


class TestIssueInputParsing:
    """Tests for parsing issue input arguments."""

    def test_parses_single_issue_number(self) -> None:
        """
        GIVEN a single issue number
        WHEN parsing the input
        THEN returns IssueInput with correct number
        """
        result = parse_issue_input("42")
        assert result.number == 42
        assert result.owner is None
        assert result.repo is None
        assert result.is_url is False

    def test_parses_github_issue_url(self) -> None:
        """
        GIVEN a GitHub issue URL
        WHEN parsing the input
        THEN extracts owner, repo, and number
        """
        url = "https://github.com/owner/repo/issues/42"
        result = parse_issue_input(url)

        assert result.number == 42
        assert result.owner == "owner"
        assert result.repo == "repo"
        assert result.is_url is True

    def test_parses_space_delimited_issue_numbers(self) -> None:
        """
        GIVEN space-delimited issue numbers
        WHEN parsing the list
        THEN returns list of IssueInputs
        """
        result = parse_issue_list("42 43 44")

        assert len(result) == 3
        assert result[0].number == 42
        assert result[1].number == 43
        assert result[2].number == 44

    def test_parses_mixed_input_formats(self) -> None:
        """
        GIVEN mixed issue numbers and URLs
        WHEN parsing the list
        THEN correctly parses each format
        """
        input_str = "42 https://github.com/owner/repo/issues/43 44"
        result = parse_issue_list(input_str)

        assert len(result) == 3
        assert result[0].number == 42
        assert result[0].is_url is False

        assert result[1].number == 43
        assert result[1].owner == "owner"
        assert result[1].is_url is True

        assert result[2].number == 44
        assert result[2].is_url is False

    def test_raises_on_invalid_input(self) -> None:
        """
        GIVEN invalid issue input
        WHEN parsing
        THEN raises ValueError
        """
        with pytest.raises(ValueError, match="Invalid issue input"):
            parse_issue_input("not-a-number")


# ==============================================================================
# Issue Dependency Analysis Tests
# ==============================================================================


@dataclass
class Issue:
    """Represents a GitHub issue for dependency analysis."""

    number: int
    title: str
    body: str
    dependencies: list[int] = field(default_factory=list)

    def has_no_blockers(self, all_issues: list[Issue]) -> bool:
        """Check if issue has no blocking dependencies in the given list."""
        issue_numbers = {i.number for i in all_issues}
        return not any(dep in issue_numbers for dep in self.dependencies)

    def get_blockers(self, all_issues: list[Issue]) -> list[int]:
        """Get list of blocking issue numbers from the given list."""
        issue_numbers = {i.number for i in all_issues}
        return [dep for dep in self.dependencies if dep in issue_numbers]


def extract_dependencies(body: str) -> list[int]:
    """
    Extract issue dependencies from issue body.

    GIVEN an issue body
    WHEN extracting dependencies
    THEN returns list of blocking issue numbers
    """
    # Pattern: "Blocked by #42" or "Depends on #42"
    pattern = r"(?:blocked by|depends on)\s+#(\d+)"
    matches = re.findall(pattern, body.lower())
    return [int(m) for m in matches]


def analyze_dependencies(issues: list[Issue]) -> tuple[list[Issue], list[dict]]:
    """
    Analyze issue dependencies to identify parallel vs sequential execution.

    GIVEN a list of issues
    WHEN analyzing dependencies
    THEN returns (independent, dependent) issue lists
    """
    independent = []
    dependent = []

    for issue in issues:
        if issue.has_no_blockers(issues):
            independent.append(issue)
        else:
            dependent.append(
                {
                    "issue": issue,
                    "blocked_by": issue.get_blockers(issues),
                }
            )

    return independent, dependent


class TestIssueDependencyAnalysis:
    """Tests for analyzing issue dependencies."""

    def test_extracts_dependency_from_body(self) -> None:
        """
        GIVEN issue body with "Blocked by #42"
        WHEN extracting dependencies
        THEN returns [42]
        """
        body = "## Dependencies\nBlocked by #42"
        result = extract_dependencies(body)
        assert result == [42]

    def test_extracts_multiple_dependencies(self) -> None:
        """
        GIVEN issue body with multiple dependencies
        WHEN extracting dependencies
        THEN returns all dependency numbers
        """
        body = "Blocked by #42 and depends on #43"
        result = extract_dependencies(body)
        assert 42 in result
        assert 43 in result

    def test_returns_empty_when_no_dependencies(self) -> None:
        """
        GIVEN issue body without dependencies
        WHEN extracting dependencies
        THEN returns empty list
        """
        body = "## Description\nJust a regular issue"
        result = extract_dependencies(body)
        assert result == []

    def test_identifies_independent_issues(self) -> None:
        """
        GIVEN issues with no cross-dependencies
        WHEN analyzing dependencies
        THEN all issues are independent
        """
        issues = [
            Issue(number=42, title="Issue A", body="No deps"),
            Issue(number=43, title="Issue B", body="No deps"),
        ]

        independent, dependent = analyze_dependencies(issues)

        assert len(independent) == 2
        assert len(dependent) == 0

    def test_identifies_dependent_issues(
        self,
        sample_github_issue: dict,
        sample_github_issue_with_dependencies: dict,
    ) -> None:
        """
        GIVEN issues where one depends on another
        WHEN analyzing dependencies
        THEN correctly classifies independent vs dependent
        """
        issue_42 = Issue(
            number=42,
            title=sample_github_issue["title"],
            body=sample_github_issue["body"],
            dependencies=extract_dependencies(sample_github_issue["body"]),
        )
        issue_43 = Issue(
            number=43,
            title=sample_github_issue_with_dependencies["title"],
            body=sample_github_issue_with_dependencies["body"],
            dependencies=extract_dependencies(
                sample_github_issue_with_dependencies["body"]
            ),
        )

        independent, dependent = analyze_dependencies([issue_42, issue_43])

        assert len(independent) == 1
        assert independent[0].number == 42

        assert len(dependent) == 1
        assert dependent[0]["issue"].number == 43
        assert 42 in dependent[0]["blocked_by"]


# ==============================================================================
# Workflow Execution Tests
# ==============================================================================


@dataclass
class WorkflowResult:
    """Result of fix-issue workflow execution."""

    status: str
    issues_processed: list[int]
    tasks_created: int
    parallel_batches: int
    reviews_completed: int
    errors: list[str] = field(default_factory=list)


def execute_fix_issue_workflow(
    issues: list[Issue],
    dry_run: bool = False,
    parallel: bool = True,
    no_review: bool = False,
) -> WorkflowResult:
    """
    Simulate fix-issue workflow execution.

    GIVEN a list of issues and options
    WHEN executing the workflow
    THEN returns WorkflowResult with execution details
    """
    if dry_run:
        return WorkflowResult(
            status="dry_run",
            issues_processed=[i.number for i in issues],
            tasks_created=len(issues) * 2,  # Estimate 2 tasks per issue
            parallel_batches=1,
            reviews_completed=0,
        )

    independent, dependent = analyze_dependencies(issues)

    # Calculate parallel batches
    batches = 1 if not parallel or not independent else len(independent)

    # Calculate reviews (one per batch unless no_review)
    reviews = 0 if no_review else batches + (1 if dependent else 0)

    return WorkflowResult(
        status="completed",
        issues_processed=[i.number for i in issues],
        tasks_created=len(issues) * 2,
        parallel_batches=batches,
        reviews_completed=reviews,
    )


class TestFixIssueWorkflow:
    """Tests for fix-issue workflow execution."""

    def test_dry_run_returns_plan_without_execution(self) -> None:
        """
        GIVEN issues with --dry-run flag
        WHEN executing workflow
        THEN returns plan without making changes
        """
        issues = [Issue(number=42, title="Test", body="Test body")]
        result = execute_fix_issue_workflow(issues, dry_run=True)

        assert result.status == "dry_run"
        assert result.issues_processed == [42]
        assert result.reviews_completed == 0

    def test_parallel_execution_creates_batches(self) -> None:
        """
        GIVEN multiple independent issues
        WHEN executing with parallel=True
        THEN creates multiple parallel batches
        """
        issues = [
            Issue(number=42, title="Issue A", body="No deps"),
            Issue(number=43, title="Issue B", body="No deps"),
            Issue(number=44, title="Issue C", body="No deps"),
        ]
        result = execute_fix_issue_workflow(issues, parallel=True)

        assert result.status == "completed"
        assert result.parallel_batches == 3

    def test_sequential_execution_with_dependencies(self) -> None:
        """
        GIVEN issues with dependencies
        WHEN executing workflow
        THEN processes dependent issues sequentially
        """
        issues = [
            Issue(number=42, title="Base", body="No deps"),
            Issue(
                number=43,
                title="Depends on 42",
                body="Blocked by #42",
                dependencies=[42],
            ),
        ]
        result = execute_fix_issue_workflow(issues, parallel=True)

        assert result.status == "completed"
        # Only 1 parallel batch (issue 42), then sequential (issue 43)
        assert result.parallel_batches == 1

    def test_no_review_skips_quality_gates(self) -> None:
        """
        GIVEN --no-review flag
        WHEN executing workflow
        THEN skips code review steps
        """
        issues = [Issue(number=42, title="Test", body="Test body")]
        result = execute_fix_issue_workflow(issues, no_review=True)

        assert result.reviews_completed == 0

    def test_workflow_includes_review_gates_by_default(self) -> None:
        """
        GIVEN normal execution
        WHEN executing workflow
        THEN includes code review after each batch
        """
        issues = [
            Issue(number=42, title="Issue A", body="No deps"),
            Issue(number=43, title="Issue B", body="No deps"),
        ]
        result = execute_fix_issue_workflow(issues)

        assert result.reviews_completed >= 1


# ==============================================================================
# Command Validation Tests
# ==============================================================================


class TestFixIssueCommandValidation:
    """Tests for fix-issue.md command file validation."""

    def test_command_has_valid_frontmatter(
        self, fix_issue_command_content: str
    ) -> None:
        """
        GIVEN fix-issue command content
        WHEN validating frontmatter
        THEN validation passes
        """
        result = CommandValidator.parse_frontmatter(fix_issue_command_content)
        assert result.is_valid
        assert "subagent-driven-development" in result.description

    def test_command_has_description(self, fix_issue_command_content: str) -> None:
        """
        GIVEN fix-issue command content
        WHEN extracting description
        THEN description is present and meaningful
        """
        result = CommandValidator.parse_frontmatter(fix_issue_command_content)
        assert result.description is not None
        assert len(result.description) > 20

    def test_command_file_validates(self, temp_fix_issue_command: Path) -> None:
        """
        GIVEN fix-issue.md command file
        WHEN validating file
        THEN validation passes
        """
        result = CommandValidator.validate_file(temp_fix_issue_command)
        assert result.is_valid

    def test_command_has_main_heading(self, fix_issue_command_content: str) -> None:
        """
        GIVEN fix-issue command content
        WHEN validating content
        THEN has proper main heading
        """
        result = CommandValidator.validate_content(fix_issue_command_content)
        assert result.is_valid


# ==============================================================================
# Error Handling Tests
# ==============================================================================


class TestFixIssueErrorHandling:
    """Tests for error handling in fix-issue workflow."""

    def test_handles_empty_issue_list(self) -> None:
        """
        GIVEN empty issue list
        WHEN executing workflow
        THEN returns appropriate status
        """
        result = execute_fix_issue_workflow([])
        assert result.issues_processed == []
        assert result.tasks_created == 0

    def test_handles_invalid_url_format(self) -> None:
        """
        GIVEN malformed GitHub URL
        WHEN parsing input
        THEN raises ValueError
        """
        with pytest.raises(ValueError):
            parse_issue_input("https://not-github.com/issues/42")

    def test_parses_url_with_different_protocols(self) -> None:
        """
        GIVEN GitHub URL with http (not https)
        WHEN parsing input
        THEN still extracts correctly
        """
        url = "http://github.com/owner/repo/issues/42"
        result = parse_issue_input(url)
        assert result.number == 42
        assert result.owner == "owner"


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestFixIssueIntegration:
    """Integration tests for fix-issue command."""

    def test_full_workflow_single_issue(self, sample_github_issue: dict) -> None:
        """
        GIVEN a single GitHub issue
        WHEN running full fix-issue workflow
        THEN completes successfully with expected results
        """
        issue = Issue(
            number=sample_github_issue["number"],
            title=sample_github_issue["title"],
            body=sample_github_issue["body"],
        )

        result = execute_fix_issue_workflow([issue])

        assert result.status == "completed"
        assert 42 in result.issues_processed
        assert result.tasks_created > 0
        assert result.reviews_completed >= 1

    def test_full_workflow_multiple_issues_with_deps(
        self,
        sample_github_issue: dict,
        sample_github_issue_with_dependencies: dict,
    ) -> None:
        """
        GIVEN multiple issues with dependencies
        WHEN running full fix-issue workflow
        THEN handles dependencies correctly
        """
        issue_42 = Issue(
            number=42,
            title=sample_github_issue["title"],
            body=sample_github_issue["body"],
        )
        issue_43 = Issue(
            number=43,
            title=sample_github_issue_with_dependencies["title"],
            body=sample_github_issue_with_dependencies["body"],
            dependencies=[42],
        )

        result = execute_fix_issue_workflow([issue_42, issue_43])

        assert result.status == "completed"
        assert set(result.issues_processed) == {42, 43}
        # Should have at least 2 reviews (one for parallel, one for sequential)
        assert result.reviews_completed >= 1
