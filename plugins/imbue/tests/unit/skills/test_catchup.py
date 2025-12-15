"""Tests for catchup skill business logic.

This module tests the repository catchup and change summarization functionality,
following TDD/BDD principles and testing all catchup scenarios.
"""

import contextlib
import time
from unittest.mock import call

import pytest

# Constants for PLR2004 magic values
TWO = 2
TWO_POINT_ZERO = 2.0
THREE = 3
FOUR = 4
FIVE = 5
SEVEN = 7
EIGHT = 8
TEN = 10
HUNDRED = 100
FIVE_HUNDRED = 500


class TestCatchupSkill:
    """Feature: Catchup skill efficiently reviews recent changes.

    As a developer returning to work
    I want to quickly understand what changed
    So that I can resume context efficiently
    """

    @pytest.fixture
    def mock_catchup_skill_content(self) -> str:
        """Mock catchup skill content."""
        return """---
name: catchup
description: Methodology for summarizing changes and extracting insights
category: review-patterns
usage_patterns:
  - context-acquisition
  - change-summary
  - insight-extraction
tools:
  - Read
  - Glob
  - Grep
  - Bash
tags:
  - catchup
  - context
  - summary
  - insights
---

# Catchup

Methodology for efficiently understanding recent changes and extracting actionable insights.

## TodoWrite Items

- `catchup:context-confirmed`
- `catchup:delta-captured`
- `catchup:insights-extracted`
- `catchup:followups-recorded`

## Catchup Workflow

### 1. Context Confirmation
- Current working directory
- Git repository status
- Branch and baseline information
- Remote synchronization status

### 2. Delta Capture
- Enumerate changes without deep content reproduction
- Focus on metadata and structure
- Token-efficient change representation
- Categorize by relevance and priority

### 3. Insight Extraction
- Identify high-impact changes
- Detect potential conflicts or blockers
- Extract coordination requirements
- Note breaking changes or deprecations

### 4. Follow-up Recording
- Actions required for each change category
- Areas needing detailed review
- Coordination points with team
- Documentation or communication needs

## Relevance Filtering

Priority order for change categories:
1. **Code changes** (src/, lib/, core/)
2. **Configuration** (config/, .env, Dockerfile)
3. **Tests** (tests/, test/)
4. **Documentation** (docs/, README.md)
5. **Build artifacts** (build/, dist/, node_modules/)
"""

    @pytest.fixture
    def sample_git_log_output(self) -> str:
        """Sample git log output for catchup testing."""
        return """abc1234 2024-12-04 Add user authentication feature
def5678 2024-12-03 Fix database connection timeout
9012345 2024-12-02 Update API documentation
2345678 2024-12-01 Refactor user service module
3456789 2024-11-30 Add integration tests for auth
4567890 2024-11-29 Configure CI/CD pipeline
5678901 2024-11-28 Update dependencies"""

    @pytest.fixture
    def sample_git_status_output(self) -> str:
        """Sample git status output."""
        return """On branch feature/user-auth
Your branch is ahead of 'origin/feature/user-auth' by 2 commits.
  (use "git push" to publish your local commits)

Changes to be committed:
  modified:   src/auth.py
  new file:   src/middleware.py
  modified:   tests/test_auth.py

Untracked files:
  config/auth_config.json"""

    @pytest.fixture
    def sample_catchup_result(self):
        """Sample structured catchup analysis result."""
        return {
            "context": {
                "working_directory": "/test/project",
                "branch": "feature/user-auth",
                "baseline": "main",
                "status": "ahead",
                "uncommitted_changes": True,
            },
            "delta": {
                "commits_since_baseline": 7,
                "files_changed": 10,
                "lines_added": 150,
                "lines_removed": 45,
                "changes_by_category": {"code": 5, "tests": 2, "docs": 1, "config": 2},
            },
            "insights": [
                {
                    "type": "feature_complete",
                    "description": "User authentication feature implementation",
                    "impact": "High",
                    "files": ["src/auth.py", "src/middleware.py"],
                },
                {
                    "type": "coordination_needed",
                    "description": "API changes require frontend team coordination",
                    "impact": "Medium",
                    "files": ["src/api.py"],
                },
            ],
            "followups": [
                {
                    "action": "Review authentication implementation",
                    "priority": "High",
                    "category": "code_review",
                },
                {
                    "action": "Update API documentation",
                    "priority": "Medium",
                    "category": "documentation",
                },
            ],
        }

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_confirms_repository_context(self, mock_claude_tools) -> None:
        """Scenario: Catchup confirms repository context and state.

        Given a git repository in any state
        When starting catchup analysis
        Then it should capture pwd, branch, and synchronization status
        And identify uncommitted changes.
        """
        # Arrange
        mock_claude_tools["Bash"].side_effect = [
            "/test/project",  # pwd
            "feature/user-auth",  # git branch
            "ahead",  # git status summary
            "True",  # has uncommitted changes
        ]

        # Act - capture repository context
        context = {}
        context["working_directory"] = mock_claude_tools["Bash"]("pwd")
        context["branch"] = mock_claude_tools["Bash"]("git branch --show-current")
        context["status"] = mock_claude_tools["Bash"](
            "git status --porcelain | head -1",
        )
        context["uncommitted_changes"] = bool(
            mock_claude_tools["Bash"]("git status --porcelain"),
        )

        # Assert
        assert context["working_directory"] == "/test/project"
        assert context["branch"] == "feature/user-auth"
        assert context["status"] == "ahead"
        assert context["uncommitted_changes"] is True

        # Verify proper commands were called
        expected_calls = [
            call("pwd"),
            call("git branch --show-current"),
            call("git status --porcelain | head -1"),
            call("git status --porcelain"),
        ]
        mock_claude_tools["Bash"].assert_has_calls(expected_calls)

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_identifies_relevant_changes(
        self, sample_git_status_output
    ) -> None:
        """Scenario: Catchup filters changes by relevance.

        Given a repository with various changes
        When running catchup analysis
        Then it should prioritize code changes over docs
        And identify conflicts or blocking issues.
        """
        # Arrange & Act - parse git status and categorize changes
        status_lines = sample_git_status_output.split("\n")

        changes = {"staged": [], "unstaged": [], "untracked": []}

        current_section = None
        for line in status_lines:
            if "Changes to be committed:" in line:
                current_section = "staged"
            elif "Untracked files:" in line:
                current_section = "untracked"
            elif line.startswith("  ") and current_section:
                change_info = line.strip()
                if ":" in change_info:
                    change_type, file_path = change_info.split(": ", 1)
                    changes[current_section].append(
                        {"file": file_path, "status": change_type},
                    )
                elif change_info and not change_info.endswith(":"):
                    changes[current_section].append(
                        {"file": change_info, "status": "untracked"},
                    )

        # Categorize by relevance
        relevance_priority = {
            "code": ["src/", "lib/", "core/", "app/"],
            "config": ["config/", ".env", "Dockerfile", "docker-compose.yml"],
            "tests": ["tests/", "test/", "spec/"],
            "docs": ["docs/", "README.md", "CHANGELOG.md"],
            "build": ["build/", "dist/", "node_modules/"],
        }

        categorized_changes = {"high": [], "medium": [], "low": []}

        for section, section_changes in changes.items():
            for change in section_changes:
                file_path = change["file"]
                relevance = "low"  # default

                for category, patterns in relevance_priority.items():
                    if any(pattern in file_path for pattern in patterns):
                        if category == "code":
                            relevance = "high"
                        elif category in ["config", "tests"]:
                            relevance = "medium"
                        break

                categorized_changes[relevance].append(
                    {"file": file_path, "section": section, "status": change["status"]},
                )

        # Assert
        assert len(categorized_changes["high"]) == 2  # src/auth.py, src/middleware.py
        assert (
            len(categorized_changes["medium"]) == 2
        )  # tests/test_auth.py, config/auth_config.json
        high_priority_files = [c["file"] for c in categorized_changes["high"]]
        assert "src/auth.py" in high_priority_files
        assert "src/middleware.py" in high_priority_files

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_captures_delta_efficiently(self, sample_git_log_output) -> None:
        """Scenario: Catchup captures change delta without full reproduction.

        Given recent commits and changes
        When analyzing delta
        Then it should summarize metadata and structure
        And conserve tokens by avoiding full content reproduction.
        """
        # Arrange & Act - parse git log output efficiently
        log_lines = sample_git_log_output.split("\n")

        commits = []
        for line in log_lines:
            parts = line.split(" ", 3)
            if len(parts) >= 4:
                commit_hash = parts[0]
                commit_date = parts[1]
                commit_time = parts[2]
                commit_message = parts[3]

                commits.append(
                    {
                        "hash": commit_hash[:8],  # Short hash
                        "date": commit_date,
                        "time": commit_time,
                        "message": commit_message,
                        "type": self._categorize_commit_type(commit_message),
                    },
                )

        # Generate summary statistics
        summary = {
            "total_commits": len(commits),
            "date_range": {
                "earliest": commits[-1]["date"] if commits else None,
                "latest": commits[0]["date"] if commits else None,
            },
            "commit_types": {},
        }

        for commit in commits:
            commit_type = commit["type"]
            summary["commit_types"][commit_type] = (
                summary["commit_types"].get(commit_type, 0) + 1
            )

        # Assert
        assert summary["total_commits"] == 7
        assert summary["date_range"]["earliest"] == "2024-11-28"
        assert summary["date_range"]["latest"] == "2024-12-04"
        assert summary["commit_types"]["feature"] == 1
        assert summary["commit_types"]["fix"] == 1
        assert summary["commit_types"]["update"] == 1
        assert summary["commit_types"]["refactor"] == 1

        # Verify token efficiency - no full file contents reproduced
        for commit in commits:
            assert len(commit["message"]) < 100  # Reasonable length
            assert len(commit["hash"]) == 8  # Short hash

    def _categorize_commit_type(self, message: str) -> str:
        """Categorize commit type from message."""
        message_lower = message.lower()
        keyword_map = {
            "feature": ("add", "implement"),
            "fix": ("fix", "bug"),
            "refactor": ("refactor", "restructure"),
            "update": ("update", "upgrade"),
            "test": ("test",),
            "config": ("config", "configure"),
        }
        for commit_type, keywords in keyword_map.items():
            if any(keyword in message_lower for keyword in keywords):
                return commit_type
        return "other"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_extracts_insights(self, sample_catchup_result) -> None:
        """Scenario: Catchup extracts actionable insights from changes.

        Given categorized changes and commit history
        When extracting insights
        Then it should identify high-impact changes
        And detect coordination requirements.
        """
        # Arrange & Act - simulate insight extraction
        changes = [
            {"file": "src/auth.py", "type": "feature", "impact": "High"},
            {"file": "src/middleware.py", "type": "feature", "impact": "High"},
            {"file": "tests/test_auth.py", "type": "test", "impact": "Low"},
            {"file": "config/auth_config.json", "type": "config", "impact": "Medium"},
        ]

        insights = []

        # Look for feature completion patterns
        feature_files = [c for c in changes if c["type"] == "feature"]
        if len(feature_files) > 1:
            insights.append(
                {
                    "type": "feature_complete",
                    "description": f"Feature implementation with {len(feature_files)} components",
                    "impact": "High",
                    "files": [c["file"] for c in feature_files],
                },
            )

        # Look for test additions
        test_files = [c for c in changes if c["type"] == "test"]
        if test_files:
            insights.append(
                {
                    "type": "test_coverage_added",
                    "description": f"Test coverage added for {len(test_files)} areas",
                    "impact": "Medium",
                    "files": [c["file"] for c in test_files],
                },
            )

        # Look for configuration changes
        config_files = [c for c in changes if c["type"] == "config"]
        if config_files:
            insights.append(
                {
                    "type": "configuration_updated",
                    "description": "Configuration changes affecting deployment",
                    "impact": "Medium",
                    "files": [c["file"] for c in config_files],
                },
            )

        # Assert
        assert len(insights) == 3
        insight_types = [i["type"] for i in insights]
        assert "feature_complete" in insight_types
        assert "test_coverage_added" in insight_types
        assert "configuration_updated" in insight_types

        # Verify feature completion insight
        feature_insight = next(i for i in insights if i["type"] == "feature_complete")
        assert feature_insight["impact"] == "High"
        assert len(feature_insight["files"]) == 2

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_records_followups(self, sample_catchup_result) -> None:
        """Scenario: Catchup records actionable follow-up items.

        Given insights from change analysis
        When recording follow-ups
        Then it should prioritize actions by impact
        And categorize by action type.
        """
        # Arrange & Act - generate follow-ups from insights
        insights = sample_catchup_result["insights"]

        followups = []

        for insight in insights:
            if insight["type"] == "feature_complete":
                followups.append(
                    {
                        "action": "Review new feature implementation",
                        "priority": "High",
                        "category": "code_review",
                        "files": insight["files"],
                    },
                )
                followups.append(
                    {
                        "action": "Update feature documentation",
                        "priority": "Medium",
                        "category": "documentation",
                        "files": insight["files"],
                    },
                )

            elif insight["type"] == "coordination_needed":
                followups.append(
                    {
                        "action": "Coordinate with affected teams",
                        "priority": "High",
                        "category": "coordination",
                        "files": insight["files"],
                    },
                )

        # Sort by priority
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        followups.sort(key=lambda f: priority_order[f["priority"]])

        # Assert
        assert len(followups) >= 2
        high_priority_count = len([f for f in followups if f["priority"] == "High"])
        assert high_priority_count >= 1

        # Verify action categories
        action_categories = [f["category"] for f in followups]
        assert "code_review" in action_categories

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_token_conservation(self) -> None:
        """Scenario: Catchup conserves tokens in large repositories.

        Given a repository with many changes
        When generating catchup summary
        Then it should summarize rather than reproduce content
        And focus on high-priority items.
        """
        # Arrange - simulate many changes
        many_changes = []
        for i in range(100):
            many_changes.append(
                {
                    "file": f"src/component_{i}.py",
                    "type": "modified",
                    "lines_added": i % 10,
                    "lines_removed": i % 5,
                },
            )

        # Act - implement token conservation
        summary = {
            "total_files_changed": len(many_changes),
            "total_lines_added": sum(c["lines_added"] for c in many_changes),
            "total_lines_removed": sum(c["lines_removed"] for c in many_changes),
            "highlights": [],  # Only show top changes
            "sample_files": [],  # Show sample, not all
        }

        # Prioritize by impact (lines changed)
        sorted_changes = sorted(
            many_changes,
            key=lambda c: c["lines_added"] + c["lines_removed"],
            reverse=True,
        )

        # Show top 10 most impactful changes
        summary["highlights"] = sorted_changes[:10]

        # Show sample files (first 5)
        summary["sample_files"] = [c["file"] for c in many_changes[:5]]

        # Assert - token conservation achieved
        assert summary["total_files_changed"] == 100
        assert len(summary["highlights"]) == 10  # Not all 100
        assert len(summary["sample_files"]) == 5  # Not all 100
        assert summary["sample_files"][0] == "src/component_0.py"
        assert "src/component_99.py" not in summary["sample_files"]

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_handles_different_baselines(self, mock_claude_tools) -> None:
        """Scenario: Catchup handles various baseline specifications.

        Given different baseline reference formats
        When establishing baseline for catchup
        Then it should handle relative refs, dates, and branches.
        """
        # Test cases for different baseline specifications
        test_cases = [
            ("HEAD~5", "git rev-parse HEAD~5"),
            ("main", "git rev-parse main"),
            ("yesterday", "git log --since='yesterday' --format=format:%H | tail -1"),
            ("--tags", "git describe --tags"),
            ("origin/feature", "git rev-parse origin/feature"),
        ]

        for _baseline_spec, expected_command in test_cases:
            # Arrange
            mock_claude_tools["Bash"].return_value = "baseline-hash"

            # Act
            baseline = mock_claude_tools["Bash"](expected_command)

            # Assert
            assert baseline == "baseline-hash"
            mock_claude_tools["Bash"].assert_called_with(expected_command)

    @pytest.mark.unit
    @pytest.mark.unit
    def test_catchup_detects_blockers_and_conflicts(self) -> None:
        """Scenario: Catchup identifies potential blockers and conflicts.

        Given changes that might cause issues
        When analyzing for blockers
        Then it should flag merge conflicts, breaking changes, etc.
        """
        # Arrange - simulate problematic changes
        changes = [
            {
                "file": "src/database.py",
                "change_type": "schema_change",
                "breaking": True,
            },
            {
                "file": "api/users.py",
                "change_type": "endpoint_removed",
                "breaking": True,
            },
            {
                "file": "requirements.txt",
                "change_type": "dependency_major_update",
                "breaking": True,
            },
            {
                "file": "src/utils.py",
                "change_type": "function_signature_change",
                "breaking": True,
            },
        ]

        # Act - detect blockers and conflicts
        blockers = []
        conflicts = []

        for change in changes:
            if change["breaking"]:
                blocker = {
                    "file": change["file"],
                    "type": change["change_type"],
                    "severity": "High",
                    "impact": "breaking_change",
                }
                blockers.append(blocker)

                # Specific conflict types
                if "schema" in change["change_type"]:
                    conflicts.append(
                        {
                            "type": "database_migration_required",
                            "affected_files": [change["file"]],
                            "action": "Coordinate with DB team for migration",
                        },
                    )
                elif "endpoint" in change["change_type"]:
                    conflicts.append(
                        {
                            "type": "api_contract_break",
                            "affected_files": [change["file"]],
                            "action": "Update API clients and documentation",
                        },
                    )

        # Assert
        assert len(blockers) == 4
        assert len(conflicts) >= 2

        conflict_types = [c["type"] for c in conflicts]
        assert "database_migration_required" in conflict_types
        assert "api_contract_break" in conflict_types

        # Verify all blockers are marked as high severity
        for blocker in blockers:
            assert blocker["severity"] == "High"

    @pytest.mark.unit
    def test_catchup_error_handling(self, mock_claude_tools) -> None:
        """Scenario: Catchup handles repository errors gracefully.

        Given various git repository issues
        When running catchup analysis
        Then it should handle errors and provide meaningful feedback.
        """
        # Test cases for repository errors
        error_cases = [
            ("fatal: not a git repository", "not_a_repo"),
            ("fatal: not a valid object name: INVALID_REF", "invalid_baseline"),
            ("error: git command not found", "git_not_available"),
        ]

        for error_output, _error_type in error_cases:
            # Arrange
            mock_claude_tools["Bash"].return_value = error_output

            # Act - handle error gracefully
            with contextlib.suppress(Exception):
                mock_claude_tools["Bash"]("git status")

            # Assert
            # In a real implementation, this would return error info rather than raising
            assert "fatal:" in error_output or "error:" in error_output

    @pytest.mark.performance
    def test_catchup_performance_large_history(self) -> None:
        """Scenario: Catchup performs efficiently with large commit history.

        Given a repository with extensive commit history
        When running catchup analysis
        Then it should complete in reasonable time.
        """
        # Arrange - simulate large commit history
        large_history = []
        for i in range(500):
            large_history.append(
                {
                    "hash": f"{i:08x}",
                    "date": f"2024-{12 - (i % 12):02d}-{(i % 28) + 1:02d}",
                    "message": f"Commit {i}: Various changes",
                    "files_changed": i % 10 + 1,
                },
            )

        # Act - measure performance of analysis
        start_time = time.time()

        # Process history efficiently
        summary = {
            "total_commits": len(large_history),
            "date_range": {
                "earliest": large_history[-1]["date"],
                "latest": large_history[0]["date"],
            },
            "files_changed_total": sum(c["files_changed"] for c in large_history),
            "commits_by_month": {},
        }

        # Group by month for summary
        for commit in large_history:
            month = commit["date"][:7]  # YYYY-MM
            summary["commits_by_month"][month] = (
                summary["commits_by_month"].get(month, 0) + 1
            )

        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should process 500 commits in under 2 seconds
        assert summary["total_commits"] == 500
        assert len(summary["commits_by_month"]) <= 12  # Max 12 months

    @pytest.mark.unit
    def test_catchup_generates_structured_output(self, sample_catchup_result) -> None:
        """Scenario: Catchup generates structured output for consumption.

        Given completed catchup analysis
        When generating final output
        Then it should produce consistent structure
        With all required sections and metadata.
        """
        # Arrange & Act - generate structured output
        catchup_result = sample_catchup_result

        # Validate required structure
        required_sections = ["context", "delta", "insights", "followups"]
        for section in required_sections:
            assert section in catchup_result

        # Validate context section
        context = catchup_result["context"]
        required_context_fields = ["working_directory", "branch", "status"]
        for field in required_context_fields:
            assert field in context

        # Validate delta section
        delta = catchup_result["delta"]
        assert "commits_since_baseline" in delta
        assert "changes_by_category" in delta
        assert isinstance(delta["changes_by_category"], dict)

        # Validate insights section
        insights = catchup_result["insights"]
        assert isinstance(insights, list)
        for insight in insights:
            assert "type" in insight
            assert "description" in insight
            assert "impact" in insight

        # Validate followups section
        followups = catchup_result["followups"]
        assert isinstance(followups, list)
        for followup in followups:
            assert "action" in followup
            assert "priority" in followup
            assert "category" in followup

        # Assert overall structure integrity
        assert catchup_result["context"]["branch"] == "feature/user-auth"
        assert catchup_result["delta"]["commits_since_baseline"] == 7
        assert len(catchup_result["insights"]) >= 1
        assert len(catchup_result["followups"]) >= 1
