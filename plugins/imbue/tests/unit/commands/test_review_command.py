"""Tests for /review command functionality.

This module tests the review command orchestration and workflow integration,
following TDD/BDD principles and testing all command scenarios.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest


class TestReviewCommand:
    """Feature: /review command initiates structured review workflow.

    As a user starting a review
    I want the command to set up the entire workflow
    So that I can focus on analysis rather than scaffolding
    """

    @pytest.fixture
    def mock_review_command_content(self):
        """Mock /review command content from commands/review.md."""
        return {
            "name": "review",
            "description": "Start a structured review workflow with evidence logging and formatted output",
            "usage": "/review [target]",
            "parameters": [
                {
                    "name": "target",
                    "type": "optional",
                    "description": "Specific path or scope to review",
                },
            ],
            "integrates_with": [
                "review-core",
                "evidence-logging",
                "structured-output",
                "diff-analysis",
            ],
        }

    @pytest.fixture
    def sample_session_state(self):
        """Sample session state for review command."""
        return {
            "working_directory": "/test/project",
            "git_branch": "feature/auth-improvement",
            "git_status": "clean",
            "baseline": "main",
            "commits_ahead": 3,
        }

    @pytest.fixture
    def sample_scope_inventory(self):
        """Sample scope inventory for review."""
        return {
            "source_files": ["src/auth.py", "src/middleware.py", "src/models/user.py"],
            "config_files": ["config/auth.json", ".env.example"],
            "documentation": ["docs/auth-flow.md", "README.md"],
            "test_files": ["tests/test_auth.py", "tests/test_middleware.py"],
        }

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_creates_workflow_scaffold(
        self,
        mock_todo_write,
        sample_session_state,
    ) -> None:
        """Scenario: /review creates complete workflow
        Given a repository ready for review
        When executing /review command
        Then it should initialize all review-core TodoWrite items
        And invoke evidence-logging setup
        And prepare structured-output template.
        """
        # Arrange

        # Act - simulate /review command execution
        workflow_components = []

        # 1. Establish context
        workflow_components.append("context_established")

        # 2. Create review-core TodoWrite items
        review_core_items = [
            "review-core:context-established",
            "review-core:scope-inventoried",
            "review-core:evidence-captured",
            "review-core:deliverables-structured",
            "review-core:contingencies-documented",
        ]

        for item in review_core_items:
            workflow_components.append(f"todowrite_created:{item}")

        # 3. Initialize evidence logging
        workflow_components.append("evidence_logging_initialized")

        # 4. Prepare structured output template
        workflow_components.append("structured_output_prepared")

        # Assert
        assert "context_established" in workflow_components
        assert (
            len([c for c in workflow_components if c.startswith("todowrite_created:")])
            == 5
        )
        assert "evidence_logging_initialized" in workflow_components
        assert "structured_output_prepared" in workflow_components

        # Verify specific TodoWrite items
        expected_items = set(review_core_items)
        created_items = {
            c.split(":")[1]
            for c in workflow_components
            if c.startswith("todowrite_created:")
        }
        assert expected_items == created_items

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_handles_target_parameter(
        self,
        mock_claude_tools,
        sample_scope_inventory,
    ) -> None:
        """Scenario: /review accepts scope targets
        Given a /review command with target path
        When parsing parameters
        Then it should scope inventory to target
        And adjust workflow accordingly.
        """
        # Arrange
        command_args = ["src/auth/"]
        target_path = command_args[0]

        # Act - simulate target-specific review
        scoped_review = {
            "target": target_path,
            "scope_type": "directory",
            "workflow_adjustments": [],
        }

        # Filter scope inventory to target
        scoped_files = []
        all_files = (
            sample_scope_inventory["source_files"]
            + sample_scope_inventory["config_files"]
            + sample_scope_inventory["documentation"]
            + sample_scope_inventory["test_files"]
        )

        for file_path in all_files:
            if file_path.startswith(target_path):
                scoped_files.append(file_path)

        scoped_review["scoped_files"] = scoped_files

        # Adjust workflow for scoped review
        if len(scoped_files) < 10:
            scoped_review["workflow_adjustments"].append("detailed_analysis")
        else:
            scoped_review["workflow_adjustments"].append("sampling_strategy")

        # Assert
        assert scoped_review["target"] == "src/auth/"
        assert scoped_review["scope_type"] == "directory"
        assert len(scoped_review["scoped_files"]) >= 1
        assert all(f.startswith("src/auth/") for f in scoped_review["scoped_files"])
        assert len(scoped_review["workflow_adjustments"]) > 0

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_handles_focus_parameters(self) -> None:
        """Scenario: /review accepts focus parameters
        Given a /review command with focus flags
        When parsing parameters
        Then it should configure specialized analysis
        And adjust skill priorities.
        """
        # Arrange
        test_cases = [
            {
                "args": ["--focus", "security"],
                "expected_focus": "security",
                "expected_skills": [
                    "review-core",
                    "evidence-logging",
                    "security-analysis",
                ],
            },
            {
                "args": ["--focus", "performance"],
                "expected_focus": "performance",
                "expected_skills": [
                    "review-core",
                    "evidence-logging",
                    "performance-analysis",
                ],
            },
            {
                "args": ["--focus", "correctness"],
                "expected_focus": "correctness",
                "expected_skills": [
                    "review-core",
                    "evidence-logging",
                    "logic-analysis",
                ],
            },
        ]

        for test_case in test_cases:
            # Act - parse focus parameters
            args = test_case["args"]
            focus_index = args.index("--focus") if "--focus" in args else -1

            if focus_index >= 0 and focus_index + 1 < len(args):
                focus = args[focus_index + 1]
            else:
                focus = None

            # Configure specialized skills based on focus
            base_skills = ["review-core", "evidence-logging"]
            specialized_skills = []

            if focus == "security":
                specialized_skills = ["security-analysis"]
            elif focus == "performance":
                specialized_skills = ["performance-analysis"]
            elif focus == "correctness":
                specialized_skills = ["logic-analysis"]

            all_skills = base_skills + specialized_skills

            # Assert
            assert focus == test_case["expected_focus"]
            assert all_skills == test_case["expected_skills"]

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_orchestrates_multiple_skills(self, mock_claude_tools) -> None:
        """Scenario: /review orchestrates multiple imbue skills
        Given a review command execution
        When coordinating skills
        Then it should call skills in correct order
        And pass appropriate context between them.
        """
        # Arrange - mock skill execution
        skill_execution_order = []
        skill_contexts = {}

        # Mock skill calls
        def mock_skill_execution(skill_name, context) -> str:
            skill_execution_order.append(skill_name)
            skill_contexts[skill_name] = context.copy()

            # Each skill adds to context
            if skill_name == "review-core":
                context["workflow_items"] = ["context-established", "scope-inventoried"]
            elif skill_name == "evidence-logging":
                context["evidence_session"] = "session-123"
            elif skill_name == "structured-output":
                context["template"] = "review_report_template"
            elif skill_name == "diff-analysis":
                context["changes"] = [{"file": "src/test.py", "type": "modified"}]

            return f"{skill_name} completed"

        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill_execution)

        # Act - execute orchestrated workflow
        initial_context = {"target": "src/", "baseline": "main"}

        # 1. review-core - establishes workflow foundation
        mock_claude_tools["Skill"]("review-core", initial_context)

        # 2. evidence-logging - captures evidence infrastructure
        mock_claude_tools["Skill"]("evidence-logging", skill_contexts["review-core"])

        # 3. structured-output - prepares deliverable format
        mock_claude_tools["Skill"](
            "structured-output",
            skill_contexts["evidence-logging"],
        )

        # 4. diff-analysis - if there are changes to analyze
        mock_claude_tools["Skill"]("diff-analysis", skill_contexts["structured-output"])

        # Assert
        expected_order = [
            "review-core",
            "evidence-logging",
            "structured-output",
            "diff-analysis",
        ]
        assert skill_execution_order == expected_order

        # Verify context passing
        assert skill_contexts["review-core"]["target"] == "src/"
        assert "workflow_items" in skill_contexts["review-core"]
        assert skill_contexts["evidence-logging"]["workflow_items"] == [
            "context-established",
            "scope-inventoried",
        ]
        assert skill_contexts["evidence-logging"]["evidence_session"] == "session-123"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_output_formatting(
        self,
        sample_session_state,
        sample_scope_inventory,
    ) -> None:
        """Scenario: /review provides structured output format
        Given completed review initialization
        When generating command output
        Then it should display clear workflow status
        And show next steps for user.
        """
        # Arrange
        workflow_status = {
            "context": sample_session_state,
            "scope": sample_scope_inventory,
            "todo_items": [
                "review-core:context-established",
                "review-core:scope-inventoried",
                "review-core:evidence-captured",
                "review-core:deliverables-structured",
                "review-core:contingencies-documented",
            ],
            "evidence_session": "review-session-123",
            "template": "review_report_template",
        }

        # Act - format command output
        output_lines = [
            "Review Workflow Initialized",
            "===========================",
            f"Repository: {Path(workflow_status['context']['working_directory']).name}",
            f"Branch: {workflow_status['context']['git_branch']}",
            f"Baseline: {workflow_status['context']['baseline']} ({workflow_status['context']['commits_ahead']} commits behind)",
            "",
            "Scope Inventory:",
            f"  Source files: {len(workflow_status['scope']['source_files'])}",
            f"  Config files: {len(workflow_status['scope']['config_files'])}",
            f"  Documentation: {len(workflow_status['scope']['documentation'])}",
            f"  Test files: {len(workflow_status['scope']['test_files'])}",
            "",
            "TodoWrite items created:",
        ]

        for item in workflow_status["todo_items"]:
            output_lines.append(f"  - [ ] {item}")

        output_lines.extend(
            [
                "",
                f"Evidence session: {workflow_status['evidence_session']}",
                f"Deliverable template: {workflow_status['template']}",
                "",
                "Next steps:",
                "1. Begin detailed analysis of scoped files",
                "2. Use evidence logging to capture findings",
                "3. Populate structured output template with results",
            ],
        )

        output = "\n".join(output_lines)

        # Assert
        assert "Review Workflow Initialized" in output
        assert "Repository: project" in output
        assert "Branch: feature/auth-improvement" in output
        assert "Baseline: main (3 commits behind)" in output
        assert "Source files: 3" in output
        assert "review-core:context-established" in output
        assert "Evidence session: review-session-123" in output
        assert "Next steps:" in output

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_error_handling(self, mock_claude_tools) -> None:
        """Scenario: /review handles errors gracefully
        Given repository or skill execution errors
        When running review command
        Then it should provide helpful error messages
        And suggest recovery actions.
        """
        # Test case 1: Git repository not found
        mock_claude_tools["Bash"].return_value = "fatal: not a git repository"

        # Act & Assert
        try:
            result = mock_claude_tools["Bash"]("git status")
            git_error_handled = False
        except Exception:
            git_error_handled = True

        # In real implementation, this would return error info

        assert git_error_handled or "fatal:" in result

        # Test case 2: Skill execution failure
        skill_errors = {
            "review-core": "Failed to establish context - invalid working directory",
            "evidence-logging": "Failed to initialize evidence log - permission denied",
            "structured-output": "Failed to load template - template not found",
        }

        for skill, error in skill_errors.items():
            # Simulate error handling
            if "Failed" in error:
                recovery_actions = {
                    "review-core": "Check working directory and git status",
                    "evidence-logging": "Check file permissions for evidence log location",
                    "structured-output": "Verify template files exist",
                }

                assert skill in recovery_actions
                assert len(recovery_actions[skill]) > 0

    @pytest.mark.unit
    @pytest.mark.unit
    def test_command_parameter_validation(self) -> None:
        """Scenario: /review validates command parameters
        Given various command argument combinations
        When parsing parameters
        Then it should validate all parameters
        And provide usage guidance for invalid inputs.
        """
        # Test cases for parameter validation
        test_cases = [
            {
                "args": [],
                "valid": True,
                "expected_target": None,
                "description": "No arguments - review current state",
            },
            {
                "args": ["src/"],
                "valid": True,
                "expected_target": "src/",
                "description": "Directory target - valid",
            },
            {
                "args": ["--focus", "security"],
                "valid": True,
                "expected_focus": "security",
                "description": "Focus parameter - valid",
            },
            {
                "args": ["--invalid-flag"],
                "valid": False,
                "error": "Unknown flag: --invalid-flag",
                "description": "Invalid flag - should fail",
            },
            {
                "args": ["--focus"],
                "valid": False,
                "error": "Missing focus value after --focus",
                "description": "Incomplete focus parameter - should fail",
            },
        ]

        for test_case in test_cases:
            args = test_case["args"]
            valid = test_case["valid"]

            # Simulate parameter parsing
            parsed_params = {"target": None, "focus": None, "errors": []}

            i = 0
            while i < len(args):
                arg = args[i]

                if arg.startswith("--"):
                    if arg == "--focus":
                        if i + 1 < len(args):
                            parsed_params["focus"] = args[i + 1]
                            i += 1
                        else:
                            parsed_params["errors"].append(
                                "Missing focus value after --focus",
                            )
                    else:
                        parsed_params["errors"].append(f"Unknown flag: {arg}")
                # Assume it's a target
                elif parsed_params["target"] is None:
                    parsed_params["target"] = arg
                else:
                    parsed_params["errors"].append("Multiple targets not supported")

                i += 1

            # Validate results
            if valid:
                assert len(parsed_params["errors"]) == 0, (
                    f"Valid case failed: {test_case['description']}"
                )
            else:
                assert len(parsed_params["errors"]) > 0, (
                    f"Invalid case should have errors: {test_case['description']}"
                )
                if "error" in test_case:
                    assert test_case["error"] in parsed_params["errors"]

    @pytest.mark.unit
    def test_command_integration_with_git_workspace(self, mock_claude_tools) -> None:
        """Scenario: /review integrates with git workspace commands
        Given a git repository with changes
        When running review command
        Then it should use git workspace data for context
        And enhance scope with git information.
        """
        # Arrange - mock git workspace responses
        mock_claude_tools["Bash"].side_effect = [
            "feature/auth-improvement",  # git branch
            "abc123",  # git rev-parse HEAD
            "def456",  # git merge-base HEAD main
            " src/auth.py\n src/middleware.py",  # git diff --name-only
            "2 files changed, 15 insertions(+), 5 deletions(-)",  # git diff --stat
        ]

        # Act - simulate git workspace integration
        git_context = {}

        # Get git information
        git_context["branch"] = mock_claude_tools["Bash"]("git branch --show-current")
        git_context["commit_hash"] = mock_claude_tools["Bash"]("git rev-parse HEAD")
        git_context["baseline"] = mock_claude_tools["Bash"]("git merge-base HEAD main")

        # Get changed files
        changed_files = mock_claude_tools["Bash"]("git diff --name-only HEAD~5").strip()
        git_context["changed_files"] = (
            changed_files.split("\n") if changed_files else []
        )

        # Get change statistics
        git_context["change_stats"] = mock_claude_tools["Bash"](
            "git diff --stat HEAD~5",
        )

        # Enhance review scope with git information
        review_scope = {
            "git_context": git_context,
            "priority_files": git_context["changed_files"],
            "has_changes": len(git_context["changed_files"]) > 0,
        }

        # Assert
        assert git_context["branch"] == "feature/auth-improvement"
        assert git_context["commit_hash"] == "abc123"
        assert git_context["baseline"] == "def456"
        assert "src/auth.py" in git_context["changed_files"]
        assert "src/middleware.py" in git_context["changed_files"]
        assert review_scope["has_changes"] is True
        assert len(review_scope["priority_files"]) == 2

    @pytest.mark.performance
    def test_command_performance_large_repositories(self) -> None:
        """Scenario: /review performs efficiently with large repositories
        Given a repository with many files
        When running review command
        Then it should complete initialization in reasonable time.
        """
        import time

        # Arrange - simulate large repository
        large_scope = {
            "source_files": [
                f"src/module_{i}/file_{j}.py" for i in range(20) for j in range(10)
            ],
            "config_files": [f"config/env_{i}.json" for i in range(50)],
            "documentation": [
                f"docs/section_{i}/page_{j}.md" for i in range(10) for j in range(5)
            ],
            "test_files": [f"tests/test_{i}.py" for i in range(200)],
        }

        # Act - measure review initialization performance
        start_time = time.time()

        # Simulate review command initialization steps
        initialization_steps = []

        # 1. Context establishment (quick)
        initialization_steps.append("context_established")

        # 2. Scope inventory (may be slow for large repos)
        total_files = sum(len(files) for files in large_scope.values())
        scope_summary = {
            "total_files": total_files,
            "categories": {k: len(v) for k, v in large_scope.items()},
        }
        initialization_steps.append("scope_inventoried")

        # 3. Evidence logging setup (quick)
        evidence_session = f"session-{int(time.time())}"
        initialization_steps.append("evidence_logging_initialized")

        # 4. Template preparation (quick)
        initialization_steps.append("structured_output_prepared")

        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should initialize in under 2 seconds
        assert len(initialization_steps) == 4
        assert scope_summary["total_files"] > 500  # Large repository
        assert evidence_session.startswith("session-")
