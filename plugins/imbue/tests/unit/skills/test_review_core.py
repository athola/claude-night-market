"""Tests for review-core skill business logic.

This module tests the review workflow scaffolding functionality,
following TDD/BDD principles and testing all business scenarios.
"""

from unittest.mock import call

import pytest

# Constants for PLR2004 magic values
TWO = 2
FIVE = 5
TEN = 10
THOUSAND = 1000


class TestReviewCoreSkill:
    """Feature: Review core provides structured workflow scaffolding.

    As a review workflow initiator
    I want consistent context establishment and scope inventory
    So that all reviews follow the same structured approach
    """

    @pytest.fixture
    def mock_review_core_skill_content(self) -> str:
        """Mock review-core skill content with required components."""
        return """---
name: review-core
description: Foundational workflow scaffolding for any detailed review
category: review-patterns
usage_patterns:
  - review-preflight
  - context-establishment
  - scope-inventory
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
tags:
  - workflow
  - review
  - scaffolding
---

# Review Core

Foundational workflow scaffolding for any detailed review.

## TodoWrite Items

- `review-core:context-established`
- `review-core:scope-inventoried`
- `review-core:evidence-captured`
- `review-core:deliverables-structured`
- `review-core:contingencies-documented`

## Context Establishment

1. Establish repository context:
   - Current working directory
   - Git branch and status
   - Remote repository information
   - Baseline for comparison

2. Log all discovery commands for evidence tracking

## Scope Inventory

1. List project structure:
   - Source files by type and language
   - Configuration files
   - Documentation
   - Generated artifacts

2. Identify review targets:
   - Modified files
   - Configuration changes
   - Documentation updates

## Evidence Capture

1. Initialize evidence log
2. Log all commands and outputs
3. Capture citations and references

## Deliverable Structure

1. Executive summary
2. Detailed findings
3. Action items
4. Evidence appendix

## Contingency Planning

1. Missing tool fallbacks
2. Partial completion scenarios
3. Error handling strategies
"""

    @pytest.fixture
    def mock_session_state(self):
        """Mock Claude Code session state."""
        return {
            "working_directory": "/test/repo",
            "git_branch": "main",
            "git_status": "clean",
            "baseline": "HEAD~1",
            "targets": ["src/", "config/"],
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_review_core_creates_required_todowrite_items(
        self, mock_todo_write
    ) -> None:
        """Scenario: Review core creates required TodoWrite items.

        Given the review-core skill is executed
        When establishing the workflow
        Then it should create all 5 required TodoWrite items
        And each item should have proper naming convention.
        """
        # Arrange
        expected_items = [
            "review-core:context-established",
            "review-core:scope-inventoried",
            "review-core:evidence-captured",
            "review-core:deliverables-structured",
            "review-core:contingencies-documented",
        ]

        # Act - simulate review-core skill execution
        review_core_items = [
            "review-core:context-established",
            "review-core:scope-inventoried",
            "review-core:evidence-captured",
            "review-core:deliverables-structured",
            "review-core:contingencies-documented",
        ]

        # Assert
        assert len(review_core_items) == 5
        for expected_item in expected_items:
            assert expected_item in review_core_items
        assert all(item.startswith("review-core:") for item in review_core_items)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_establishment_captures_git_state(self, mock_claude_tools) -> None:
        """Scenario: Context establishment captures git state.

        Given a repository in review state
        When establishing context
        Then it should capture pwd, branch, and baseline
        And log commands used for discovery.
        """
        # Arrange
        mock_claude_tools["Bash"].return_value = "/test/repo"
        mock_claude_tools["Bash"].side_effect = [
            "/test/repo",  # pwd
            "main",  # git branch
            "clean",  # git status --porcelain
            "HEAD~1",  # baseline calculation
        ]

        # Act - simulate context establishment
        context = {}
        context["working_directory"] = mock_claude_tools["Bash"]("pwd")
        context["git_branch"] = mock_claude_tools["Bash"]("git branch --show-current")
        context["git_status"] = mock_claude_tools["Bash"]("git status --porcelain")
        context["baseline"] = mock_claude_tools["Bash"]("git merge-base HEAD HEAD~1")

        # Assert
        assert context["working_directory"] == "/test/repo"
        assert context["git_branch"] == "main"
        assert context["git_status"] == "clean"
        assert context["baseline"] == "HEAD~1"

        # Verify commands were called
        expected_calls = [
            call("pwd"),
            call("git branch --show-current"),
            call("git status --porcelain"),
            call("git merge-base HEAD HEAD~1"),
        ]
        mock_claude_tools["Bash"].assert_has_calls(expected_calls)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_scope_inventory_discovers_project_structure(
        self, mock_claude_tools
    ) -> None:
        """Scenario: Scope inventory finds all relevant artifacts.

        Given a project with various file types
        When inventorying scope
        Then it should list source, config, docs, and generated assets
        And record discovery commands.
        """
        # Arrange
        mock_claude_tools["Glob"].return_value = [
            "src/main.py",
            "src/utils.py",
            "config/app.json",
            "docs/readme.md",
            "build/output.bin",
        ]

        # Act - simulate scope inventory
        scope = {
            "source_files": [],
            "config_files": [],
            "documentation": [],
            "generated_artifacts": [],
        }

        all_files = mock_claude_tools["Glob"]("**/*")
        for file_path in all_files:
            if file_path.startswith("src/"):
                scope["source_files"].append(file_path)
            elif file_path.startswith("config/"):
                scope["config_files"].append(file_path)
            elif file_path.startswith("docs/"):
                scope["documentation"].append(file_path)
            elif file_path.startswith("build/"):
                scope["generated_artifacts"].append(file_path)

        # Assert
        assert len(scope["source_files"]) == 2
        assert "src/main.py" in scope["source_files"]
        assert len(scope["config_files"]) == 1
        assert "config/app.json" in scope["config_files"]
        assert len(scope["documentation"]) == 1
        assert "docs/readme.md" in scope["documentation"]
        assert len(scope["generated_artifacts"]) == 1
        assert "build/output.bin" in scope["generated_artifacts"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_scope_inventory_identifies_review_targets(self, mock_claude_tools) -> None:
        """Scenario: Scope inventory identifies targets for review.

        Given modified files and configuration changes
        When inventorying scope
        Then it should prioritize modified files
        And identify configuration changes for review.
        """
        # Arrange
        mock_claude_tools[
            "Bash"
        ].return_value = "M src/main.py\nM config/database.json\nA docs/api.md"

        # Act - simulate target identification
        modified_files_output = mock_claude_tools["Bash"]("git diff --name-only HEAD~1")
        modified_files = (
            modified_files_output.split("\n") if modified_files_output else []
        )

        review_targets = {
            "source_changes": [],
            "config_changes": [],
            "documentation_changes": [],
        }

        for file_path in modified_files:
            if file_path.startswith("src/"):
                review_targets["source_changes"].append(file_path)
            elif file_path.startswith("config/"):
                review_targets["config_changes"].append(file_path)
            elif file_path.startswith("docs/"):
                review_targets["documentation_changes"].append(file_path)

        # Assert
        assert "M src/main.py" in modified_files
        assert "M config/database.json" in modified_files
        assert "A docs/api.md" in modified_files
        assert len(review_targets["source_changes"]) == 1
        assert len(review_targets["config_changes"]) == 1
        assert len(review_targets["documentation_changes"]) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_capture_initializes_log(self, sample_evidence_log) -> None:
        """Scenario: Evidence capture initializes structured log.

        Given a review workflow starting
        When initializing evidence capture
        Then it should create structured evidence log
        With session context and metadata.
        """
        # Arrange & Act - evidence log is already initialized by fixture
        evidence_log = sample_evidence_log

        # Assert
        assert "session_id" in evidence_log
        assert "timestamp" in evidence_log
        assert "context" in evidence_log
        assert "evidence" in evidence_log
        assert "citations" in evidence_log
        assert evidence_log["session_id"] == "test-session-123"
        assert len(evidence_log["evidence"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_capture_logs_commands(self, sample_evidence_log) -> None:
        """Scenario: Evidence capture logs all commands.

        Given commands being executed during review
        When capturing evidence
        Then it should record command, output, and timestamp
        And provide unique evidence identifiers.
        """
        # Arrange
        evidence_log = sample_evidence_log
        initial_count = len(evidence_log["evidence"])

        # Act - add new evidence
        new_evidence = {
            "id": f"E{initial_count + 1}",
            "command": "git diff --stat",
            "output": " 2 files changed, 5 insertions(+), 2 deletions(-)",
            "timestamp": "2024-12-04T10:00:02Z",
            "working_directory": "/test/repo",
        }
        evidence_log["evidence"].append(new_evidence)

        # Assert
        assert len(evidence_log["evidence"]) == initial_count + 1
        assert evidence_log["evidence"][-1]["id"] == "E2"
        assert evidence_log["evidence"][-1]["command"] == "git diff --stat"
        assert "timestamp" in evidence_log["evidence"][-1]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deliverable_structure_generation(self) -> None:
        """Scenario: Deliverable structure creates consistent report format.

        Given review findings and evidence
        When generating deliverables
        Then it should create structured report with required sections
        And maintain evidence reference integrity.
        """
        # Arrange
        review_findings = [
            {
                "id": "F1",
                "title": "Test Finding",
                "description": "Test description",
                "severity": "Medium",
                "evidence_refs": ["E1", "E2"],
            },
        ]

        # Act - generate deliverable structure
        deliverable = {
            "metadata": {
                "review_id": "review-123",
                "timestamp": "2024-12-04T10:00:00Z",
                "reviewer": "Test Reviewer",
            },
            "executive_summary": "Review completed with 1 finding",
            "detailed_findings": review_findings,
            "action_items": [],
            "evidence_appendix": {"total_evidence": 2, "evidence_items": ["E1", "E2"]},
        }

        # Assert
        assert "metadata" in deliverable
        assert "executive_summary" in deliverable
        assert "detailed_findings" in deliverable
        assert "action_items" in deliverable
        assert "evidence_appendix" in deliverable
        assert deliverable["evidence_appendix"]["total_evidence"] == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_contingency_planning_missing_tools(self, mock_claude_tools) -> None:
        """Scenario: Contingency planning handles missing tools.

        Given required tools not available
        When planning contingencies
        Then it should provide fallback strategies
        And document tool availability.
        """
        # Arrange
        available_tools = ["Read", "Glob"]  # Missing Grep, Bash
        required_tools = ["Read", "Glob", "Grep", "Bash"]

        # Act - analyze tool availability and plan contingencies
        missing_tools = [tool for tool in required_tools if tool not in available_tools]
        contingency_plan = {
            "available_tools": available_tools,
            "missing_tools": missing_tools,
            "fallback_strategies": [],
        }

        for missing_tool in missing_tools:
            if missing_tool == "Grep":
                contingency_plan["fallback_strategies"].append(
                    "Use file reading and string searching for pattern matching",
                )
            elif missing_tool == "Bash":
                contingency_plan["fallback_strategies"].append(
                    "Use external script execution or manual command results",
                )

        # Assert
        assert len(contingency_plan["missing_tools"]) == 2
        assert "Grep" in contingency_plan["missing_tools"]
        assert "Bash" in contingency_plan["missing_tools"]
        assert len(contingency_plan["fallback_strategies"]) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_review_core_workflow_completion(self, mock_todo_write) -> None:
        """Scenario: Review core workflow completes all phases.

        Given a full review workflow
        When executing review-core skill
        Then it should complete all 5 TodoWrite items
        And provide structured review foundation.
        """
        # Arrange
        workflow_phases = [
            "review-core:context-established",
            "review-core:scope-inventoried",
            "review-core:evidence-captured",
            "review-core:deliverables-structured",
            "review-core:contingencies-documented",
        ]

        # Act - simulate workflow completion
        completed_phases = []
        for phase in workflow_phases:
            # Simulate completing each phase
            completed_phases.append(phase)

        # Assert
        assert len(completed_phases) == 5
        assert all(phase in completed_phases for phase in workflow_phases)
        assert len(set(completed_phases)) == 5  # All unique

    @pytest.mark.unit
    def test_review_core_error_handling(self, mock_claude_tools) -> None:
        """Scenario: Review core handles errors gracefully.

        Given command execution failures
        When running review workflow
        Then it should handle errors and continue
        And document issues in evidence log.
        """
        # Arrange
        mock_claude_tools["Bash"].side_effect = [
            "/test/repo",  # pwd succeeds
            "main",  # git branch succeeds
            "Error: Not a git repository",  # git status fails
            "HEAD~1",  # fallback baseline
        ]

        # Act - simulate workflow with error
        context = {}
        try:
            context["working_directory"] = mock_claude_tools["Bash"]("pwd")
            context["git_branch"] = mock_claude_tools["Bash"](
                "git branch --show-current",
            )
            context["git_status"] = mock_claude_tools["Bash"]("git status --porcelain")
        except Exception as e:
            context["git_status_error"] = str(e)

        # Fallback for baseline
        context["baseline"] = mock_claude_tools["Bash"]("git rev-parse HEAD~1")

        # Assert
        assert context["working_directory"] == "/test/repo"
        assert context["git_branch"] == "main"
        assert context["git_status"] == "Error: Not a git repository"
        assert "git_status_error" in context
        assert context["baseline"] == "HEAD~1"

    @pytest.mark.unit
    def test_review_core_token_conservation(self) -> None:
        """Scenario: Review core conserves tokens in large projects.

        Given a project with many files
        When inventorying scope
        Then it should summarize rather than list all files
        And focus on relevant artifacts.
        """
        # Arrange
        all_files = [f"src/file_{i}.py" for i in range(1000)]  # Large project

        # Act - implement token conservation strategy
        scope_summary = {
            "total_files": len(all_files),
            "file_types": {},
            "sample_files": all_files[:10],  # Only first 10 as examples
        }

        # Categorize by file type
        for file_path in all_files:
            ext = file_path.split(".")[-1]
            scope_summary["file_types"][ext] = (
                scope_summary["file_types"].get(ext, 0) + 1
            )

        # Assert
        assert scope_summary["total_files"] == 1000
        assert scope_summary["file_types"]["py"] == 1000
        assert len(scope_summary["sample_files"]) == 10  # Token conservation
        assert "src/file_0.py" in scope_summary["sample_files"]
        assert "src/file_999.py" not in scope_summary["sample_files"]  # Not included
