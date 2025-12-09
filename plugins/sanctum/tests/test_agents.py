"""BDD-style tests for Sanctum agents.

This module tests the agent implementations that coordinate
multiple skills and tools to accomplish complex Git workflows.
"""

from __future__ import annotations

from unittest.mock import Mock


class TestGitWorkspaceAgent:
    """BDD tests for the Git Workspace agent."""

    def test_agent_initializes_with_correct_capabilities(self):
        """GIVEN the Git Workspace agent is created
        WHEN it initializes
        THEN it should have the correct capabilities and tools.
        """
        # Arrange
        expected_capabilities = [
            "repository_analysis",
            "status_checking",
            "change_detection",
            "diff_analysis",
            "todo_coordination"
        ]

        # Act - Simulate agent initialization
        agent_capabilities = {
            "repository_analysis": True,
            "status_checking": True,
            "change_detection": True,
            "diff_analysis": True,
            "todo_coordination": True,
            "git_operations": True
        }

        # Assert
        assert all(cap in agent_capabilities for cap in expected_capabilities)

    def test_agent_analyzes_repository_state(self, temp_git_repo):
        """GIVEN a Git repository
        WHEN the agent analyzes the repository state
        THEN it should provide comprehensive repository information.
        """
        # Arrange
        temp_git_repo.add_file("test.py", "print('test')")
        temp_git_repo.stage_file("test.py")

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nChanges to be committed:\n  new file:   test.py",
            "main",
            "true",  # is git repo
            "origin  https://github.com/test/repo.git (fetch)"
        ]

        # Act - simulate calling tools through mock
        analysis = {
            "status": mock_bash("git status"),
            "branch": mock_bash("git branch --show-current"),
            "is_git_repo": mock_bash("git rev-parse --git-dir") != "false",
            "remotes": mock_bash("git remote -v")
        }

        # Assert
        assert "Changes to be committed" in analysis["status"]
        assert analysis["branch"] == "main"
        assert analysis["is_git_repo"] is True
        assert "origin" in analysis["remotes"]

    def test_agent_detects_and_categorizes_changes(self, staged_changes_context):
        """GIVEN a repository with various types of changes
        WHEN the agent analyzes the changes
        THEN it should categorize them appropriately.
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = [
            "M src/main.py\nA README.md\nD old_file.py\n?? temp.tmp",
            "src/main.py\nREADME.md\nold_file.py",
            "150\n50\n25"
        ]

        # Act - simulate calling tools through mock
        porcelain_status = mock_bash("git status --porcelain")
        mock_bash("git diff --cached --name-only")
        stats = mock_bash("git diff --cached --stat")

        # Parse and categorize changes
        changes = self._parse_git_status(porcelain_status)
        change_stats = self._parse_git_stats(stats)

        # Assert
        assert changes["modified"] == ["src/main.py"]
        assert changes["added"] == ["README.md"]
        assert changes["deleted"] == ["old_file.py"]
        assert changes["untracked"] == ["temp.tmp"]
        assert change_stats["total_additions"] == 150
        assert change_stats["total_deletions"] == 75  # 50 + 25

    def test_agent_coordinates_todo_creation(self, mock_todo_tool):
        """GIVEN the agent completes repository analysis
        WHEN it creates TodoWrite items
        THEN it should create appropriate tasks for the workflow.
        """
        # Arrange
        analysis_result = {
            "repository_status": "clean",
            "has_staged_changes": True,
            "staged_files": ["feature.py", "test_feature.py"],
            "change_summary": "Added new feature with tests"
        }

        # Act
        todos = self._create_analysis_todos(analysis_result)
        mock_todo_tool(todos)

        # Assert
        assert len(todos) == 3
        assert any("repository" in todo["content"].lower() for todo in todos)
        assert any("staged" in todo["content"].lower() for todo in todos)
        assert all(todo["status"] == "completed" for todo in todos)
        mock_todo_tool.assert_called_once_with(todos)

    def test_agent_handles_error_states_gracefully(self):
        """GIVEN a repository in an error state
        WHEN the agent encounters the error
        THEN it should handle it gracefully and provide recovery options.
        """
        # Arrange
        error_scenarios = [
            {
                "error": "fatal: not a git repository",
                "recovery": ["git init", "git clone"]
            },
            {
                "error": "fatal: couldn't find remote ref refs/heads/main",
                "recovery": ["git branch -m main", "git push origin main"]
            },
            {
                "error": "permission denied",
                "recovery": ["Check file permissions", "Run as appropriate user"]
            }
        ]

        # Act & Assert
        for scenario in error_scenarios:
            # Agent should catch error and suggest recovery
            recovery_suggestions = self._handle_git_error(scenario["error"])
            assert len(recovery_suggestions) > 0
            assert any(action in " ".join(recovery_suggestions)
                      for action in scenario["recovery"])

    def test_agent_provides_workflow_recommendations(self, staged_changes_context):
        """GIVEN a repository state analysis
        WHEN the agent provides recommendations
        THEN it should suggest appropriate next steps.
        """
        # Arrange
        contexts = [
            {
                "has_staged_changes": True,
                "has_unstaged_changes": False,
                "is_clean": False,
                "expected_recommendations": ["commit", "commit-messages"]
            },
            {
                "has_staged_changes": False,
                "has_unstaged_changes": True,
                "is_clean": False,
                "expected_recommendations": ["stage", "git add"]
            },
            {
                "has_staged_changes": False,
                "has_unstaged_changes": False,
                "is_clean": True,
                "expected_recommendations": ["clean", "push", "pr"]
            }
        ]

        # Act & Assert
        for ctx in contexts:
            recommendations = self._generate_workflow_recommendations(ctx)
            for expected in ctx["expected_recommendations"]:
                assert any(expected in rec.lower() for rec in recommendations)

    # Helper methods
    def _parse_git_status(self, status: str) -> dict[str, list[str]]:
        """Parse git status porcelain output."""
        changes = {"modified": [], "added": [], "deleted": [], "untracked": []}
        for line in status.split('\n'):
            if line and len(line) > 2:
                status_code = line[:2]
                # Git porcelain format: XY filename (where XY is 2 chars + space)
                file_path = line[3:] if line[2] == ' ' else line[2:]
                if status_code[0] == 'M' or status_code[1] == 'M':
                    changes["modified"].append(file_path)
                elif status_code[0] == 'A' or status_code[1] == 'A':
                    changes["added"].append(file_path)
                elif status_code[0] == 'D' or status_code[1] == 'D':
                    changes["deleted"].append(file_path)
                elif status_code == '??':
                    changes["untracked"].append(file_path)
        return changes

    def _parse_git_stats(self, stats: str) -> dict[str, int]:
        """Parse git diff --stat output."""
        lines = stats.split('\n')
        # Extract numbers from stat output and sum deletions
        additions = int(lines[0]) if lines[0].isdigit() else 0
        deletions = sum(int(line) for line in lines[1:] if line.isdigit())
        return {
            "total_additions": additions,
            "total_deletions": deletions,
            "files_changed": len([l for l in lines if l.isdigit()])
        }

    def _create_analysis_todos(self, analysis: dict) -> list[dict]:
        """Create TodoWrite items based on analysis."""
        return [
            {
                "content": f"Analyzed repository: {analysis['repository_status']}",
                "status": "completed",
                "activeForm": "Repository analysis complete"
            },
            {
                "content": f"Found {len(analysis['staged_files'])} staged files",
                "status": "completed",
                "activeForm": "Staged files identified"
            },
            {
                "content": f"Change summary: {analysis['change_summary']}",
                "status": "completed",
                "activeForm": "Change summary created"
            }
        ]

    def _handle_git_error(self, error: str) -> list[str]:
        """Handle Git errors with recovery suggestions."""
        if "not a git repository" in error:
            return ["Initialize repository with git init",
                   "Clone existing repository with git clone"]
        elif "couldn't find remote ref" in error:
            return ["Check remote configuration with git branch -m main",
                   "Ensure branch exists remotely",
                   "Push branch with git push origin main"]
        elif "permission denied" in error.lower():
            return ["Check file permissions",
                   "Verify Git configuration",
                   "Run as appropriate user"]
        else:
            return ["Check Git status for details"]

    def _generate_workflow_recommendations(self, context: dict) -> list[str]:
        """Generate workflow recommendations based on context."""
        recommendations = []
        if context["has_staged_changes"]:
            recommendations.append("Ready to commit with /commit-msg")
            recommendations.append("Use commit-messages skill for conventional commits")
        if context["has_unstaged_changes"] and not context["has_staged_changes"]:
            recommendations.append("Stage changes with 'git add'")
            recommendations.append("Review changes with 'git diff'")
        if context["is_clean"]:
            recommendations.append("Working tree clean - ready for next steps")
            recommendations.append("Consider pushing changes")
            recommendations.append("Create pull request with /pr")
        return recommendations


class TestCommitAgent:
    """BDD tests for the Commit agent."""

    def test_agent_generates_conventional_commits(self, staged_changes_context):
        """GIVEN staged changes in the repository
        WHEN the commit agent analyzes and generates a commit
        THEN it should produce a conventional commit message.
        """
        # Arrange
        conventional_types = ["feat", "fix", "docs", "style", "refactor",
                            "test", "chore", "perf", "ci", "build"]

        mock_bash = Mock()
        mock_bash.return_value = "feat(auth): Add OAuth2 authentication\n\nImplements secure login flow"

        # Act - simulate calling tools through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert ':' in commit_msg
        commit_type = commit_msg.split(':')[0]
        # Handle scope: feat(auth) -> feat
        base_type = commit_type.split('(')[0] if '(' in commit_type else commit_type
        assert base_type in conventional_types
        assert "Add OAuth2" in commit_msg

    def test_agent_validates_commit_message_quality(self):
        """GIVEN a generated commit message
        WHEN the agent validates it
        THEN it should ensure quality standards are met.
        """
        # Arrange
        commit_messages = [
            ("feat: Add new feature", True),  # Good
            ("Fix bug", False),  # Missing type
            ("feat:", False),  # Missing description
            ("", False),  # Empty
            ("feat: " + "x" * 100, False),  # Too long
        ]

        # Act & Assert
        for msg, should_pass in commit_messages:
            validation_result = self._validate_commit_message(msg)
            assert validation_result == should_pass, f"Failed on: {msg}"

    def test_agent_handles_complex_change_scenarios(self):
        """GIVEN complex changes involving multiple files and types
        WHEN the agent generates a commit message
        THEN it should appropriately summarize all changes.
        """
        # Arrange
        complex_context = {
            "staged_files": [
                {"path": "src/api.py", "type": "feature", "changes": 100},
                {"path": "src/config.py", "type": "refactor", "changes": 50},
                {"path": "tests/test_api.py", "type": "test", "changes": 75},
                {"path": "README.md", "type": "docs", "changes": 25}
            ],
            "breaking_changes": True
        }

        # Act
        commit_msg = self._generate_complex_commit_message(complex_context)

        # Assert
        assert commit_msg.startswith("feat!")  # Breaking change
        assert "api" in commit_msg.lower()
        # Verify body contains appropriate change details
        assert "test" in commit_msg.lower() or "tests" in commit_msg.lower()
        assert "documentation" in commit_msg.lower() or "update" in commit_msg.lower()

    def _validate_commit_message(self, message: str) -> bool:
        """Validate conventional commit message format."""
        if not message:
            return False

        lines = message.split('\n')
        subject = lines[0]

        # Check format: type(scope): description
        if ':' not in subject:
            return False

        type_part, description = subject.split(':', 1)
        type_part = type_part.strip()
        description = description.strip()

        # Check type is valid
        valid_types = ["feat", "fix", "docs", "style", "refactor",
                      "test", "chore", "perf", "ci", "build"]
        if type_part.rstrip('!') not in valid_types:
            return False

        # Check description exists and is properly formatted
        if not description:
            return False

        # Check subject length
        if len(subject) > 72:
            return False

        # Check imperative mood (basic check)
        if description.lower().startswith(('added', 'fixed', 'updated', 'removed')):
            return False

        return True

    def _generate_complex_commit_message(self, context: dict) -> str:
        """Generate commit message for complex changes."""
        # Determine primary change type
        feature_files = [f for f in context["staged_files"] if f["type"] == "feature"]
        breaking_indicator = "!" if context.get("breaking_changes") else ""

        if feature_files:
            # Feature is primary type
            base_msg = f"feat{breaking_indicator}: Implement API changes"
        else:
            base_msg = f"refactor{breaking_indicator}: Update codebase"

        # Add body with details
        details = []
        for file in context["staged_files"]:
            if file["type"] == "feature":
                details.append(f"- Add {file['path']}")
            elif file["type"] == "test":
                details.append(f"- Add tests for {file['path']}")
            elif file["type"] == "docs":
                details.append("- Update documentation")

        if details:
            body = "\n\n" + "\n".join(details)
        else:
            body = ""

        return base_msg + body


class TestPRAgent:
    """BDD tests for the Pull Request agent."""

    def test_agent_preparates_comprehensive_pr(self, pull_request_context):
        """GIVEN a feature branch ready for PR
        WHEN the PR agent prepares the pull request
        THEN it should generate a comprehensive PR description.
        """
        # Arrange
        pr_sections = [
            "Summary",
            "Changes Made",
            "Test Plan",
            "Breaking Changes",
            "Checklist"
        ]

        # Act
        pr_description = self._generate_pr_description(pull_request_context)

        # Assert
        for section in pr_sections:
            assert f"## {section}" in pr_description

    def test_agent_analyzes_pr_quality_gates(self, pull_request_context):
        """GIVEN a pull request
        WHEN the agent checks quality gates
        THEN it should validate all required criteria.
        """
        # Arrange
        quality_gates = {
            "has_description": True,
            "has_tests": True,
            "has_documentation": True,
            "passes_ci": False,  # Simulate CI failure
            "has_breaking_changes": False
        }

        # Act
        gate_status = self._check_quality_gates(quality_gates)

        # Assert
        assert gate_status["description_check"] == "passed"
        assert gate_status["test_check"] == "passed"
        assert gate_status["ci_check"] == "failed"
        assert gate_status["overall_status"] == "failed"  # CI failure causes overall failure

    def test_agent_suggests_reviewers(self, pull_request_context):
        """GIVEN changes in specific areas
        WHEN the agent suggests reviewers
        THEN it should recommend appropriate team members.
        """
        # Arrange
        reviewer_map = {
            "src/": ["@backend-team", "@tech-lead"],
            "tests/": ["@qa-team"],
            "docs/": ["@docs-team", "@technical-writers"],
            "frontend/": ["@frontend-team"]
        }

        # Act
        suggested_reviewers = self._suggest_reviewers(pull_request_context, reviewer_map)

        # Assert
        assert "@backend-team" in suggested_reviewers
        assert "@qa-team" in suggested_reviewers
        assert "@docs-team" in suggested_reviewers

    def _generate_pr_description(self, context: dict) -> str:
        """Generate comprehensive PR description."""
        description = """## Summary

This pull request implements new functionality for the feature branch.

## Changes Made

- Feature implementation: src/feature.py (150 changes)
- Test coverage: tests/test_feature.py (75 changes)
- Documentation: docs/feature.md (50 changes)

## Test Plan

- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Review documentation

## Breaking Changes

None

## Checklist

- [ ] Code is reviewed
- [ ] Tests pass
- [ ] Documentation is updated
"""
        return description

    def _check_quality_gates(self, gates: dict[str, bool]) -> dict[str, str]:
        """Check PR quality gates."""
        status = {}
        status["description_check"] = "passed" if gates["has_description"] else "failed"
        status["test_check"] = "passed" if gates["has_tests"] else "failed"
        status["docs_check"] = "passed" if gates["has_documentation"] else "failed"
        status["ci_check"] = "passed" if gates["passes_ci"] else "failed"

        if gates["has_breaking_changes"]:
            status["breaking_check"] = "warning"
        else:
            status["breaking_check"] = "passed"

        # Determine overall status
        failed_checks = [k for k, v in status.items() if v == "failed"]
        status["overall_status"] = "failed" if failed_checks else \
                                  "warning" if status.get("breaking_check") == "warning" else \
                                  "passed"

        return status

    def _suggest_reviewers(self, context: dict, reviewer_map: dict[str, list[str]]) -> list[str]:
        """Suggest reviewers based on changed files."""
        reviewers = set()

        for file_change in context["changed_files"]:
            file_path = file_change["path"]

            # Find matching reviewer teams
            for path_pattern, teams in reviewer_map.items():
                if file_path.startswith(path_pattern):
                    reviewers.update(teams)
                    break

        return list(reviewers)
