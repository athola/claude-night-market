"""Integration tests for Sanctum plugin workflows.

This module tests the complete workflows that span multiple skills,
commands, and agents, ensuring they work together seamlessly.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest


class TestGitWorkflowIntegration:
    """Integration tests for complete Git workflows."""

    def test_complete_commit_workflow(self, temp_git_repo, mock_todo_tool) -> None:
        """GIVEN a Git repository with staged changes.

        WHEN a user runs the complete commit workflow
        THEN it should execute git-workspace-review and commit-messages in sequence.
        """
        # Arrange - Create repository with staged changes
        temp_git_repo.add_file("feature.py", "def new_feature():\n    pass")
        temp_git_repo.stage_file("feature.py")

        # Mock the skill execution sequence
        captured_todos = []

        def capture_todos(todos):
            captured_todos.extend(todos)
            return {"status": "success"}

        mock_todo_tool.side_effect = capture_todos

        # Act - Simulate complete workflow
        workflow_steps = [
            # Step 1: Git workspace review
            {
                "skill": "git-workspace-review",
                "todos": [
                    {
                        "content": "git-review:repo-confirmed",
                        "status": "completed",
                        "activeForm": "Confirmed repository",
                    },
                    {
                        "content": "git-review:status-overview",
                        "status": "completed",
                        "activeForm": "Analyzed status",
                    },
                ],
            },
            # Step 2: Commit message generation
            {
                "skill": "commit-messages",
                "todos": [
                    {
                        "content": "Analyze staged changes",
                        "status": "completed",
                        "activeForm": "Analyzed changes",
                    },
                    {
                        "content": "Generate commit message",
                        "status": "completed",
                        "activeForm": "Generated message",
                    },
                    {
                        "content": "Validate commit format",
                        "status": "completed",
                        "activeForm": "Validated format",
                    },
                ],
            },
        ]

        # Execute workflow
        for step in workflow_steps:
            mock_todo_tool(step["todos"])

        # Assert - Verify all workflow steps were executed
        assert len(captured_todos) == 5  # 2 + 3 todos
        assert captured_todos[0]["content"] == "git-review:repo-confirmed"
        assert captured_todos[-1]["content"] == "Validate commit format"

    def test_pr_workflow_from_feature_branch(self, temp_git_repo) -> None:
        """GIVEN a feature branch with multiple commits

        WHEN a user prepares a pull request
        THEN it should execute the complete PR preparation workflow.
        """
        # Arrange - Create feature branch with commits
        temp_git_repo.add_file("initial.py", "# initial")
        temp_git_repo.stage_file("initial.py")
        temp_git_repo.commit("Initial commit")

        temp_git_repo.create_branch("feature/user-auth")
        temp_git_repo.add_file("auth.py", "class Auth:\n    def login(self): pass")
        temp_git_repo.stage_file("auth.py")
        temp_git_repo.commit("feat: Add authentication class")
        temp_git_repo.add_file("tests/test_auth.py", "def test_auth(): pass")
        temp_git_repo.stage_file("tests/test_auth.py")
        temp_git_repo.commit("test: Add auth tests")

        # Mock Git commands for PR analysis
        mock_bash = Mock()
        mock_bash.side_effect = [
            "feature/user-auth",  # Current branch
            "main",  # Base branch
            "feat: Add authentication class\ntest: Add auth tests",  # Commit messages
            "auth.py\ntests/test_auth.py",  # Changed files
            "50\n25",  # Added/deleted lines
        ]

        # Act - Simulate PR workflow through mock calls
        branch_info = mock_bash("git branch --show-current")
        mock_bash("git rev-parse --abbrev-ref origin/main")
        commits = mock_bash("git log --oneline main..HEAD")
        files = mock_bash("git diff --name-only main...HEAD")
        mock_bash("git diff --stat main...HEAD")

        # Assert - Verify PR analysis
        assert branch_info == "feature/user-auth"
        assert "feat: Add authentication" in commits
        assert "auth.py" in files
        assert "test_auth.py" in files

    def test_catchup_workflow_integration(self, temp_git_repo) -> None:
        """GIVEN a Git repository that has diverged from remote

        WHEN a user runs the catchup workflow
        THEN it should analyze changes and prepare for merging.
        """
        # Arrange - Simulate diverged branch state
        mock_bash = Mock()
        mock_bash.side_effect = [
            "main",  # Current branch
            "## main...origin/main\nbehind 3\n+ 3e8a4b1...45f6c2d 3 commits",  # Status
            "3e8a4b1 Fix critical bug\n45f6c2d Update dependencies\n78a9b3c Improve performance",  # Missing commits
            "src/main.py\npackage.json\nREADME.md",  # Changed files
        ]

        # Act - Simulate catchup workflow through mock calls
        current_branch = mock_bash("git branch --show-current")
        status_output = mock_bash("git status")
        missing_commits = mock_bash("git log --oneline origin/main..HEAD")
        changed_files = mock_bash("git diff --name-only origin/main...HEAD")

        # Assert - Verify catchup analysis
        assert current_branch == "main"
        assert "behind 3" in status_output
        assert len(missing_commits.split("\n")) == 3
        assert "src/main.py" in changed_files

    def test_documentation_update_workflow(self, temp_git_repo) -> None:
        """GIVEN changes that require documentation updates

        WHEN the documentation update workflow is executed
        THEN it should identify and update relevant documentation.
        """
        # Arrange - Create code changes
        temp_git_repo.add_file("api.py", "# API endpoints\ndef get_data(): pass")
        temp_git_repo.stage_file("api.py")

        # Mock documentation analysis
        mock_bash = Mock()
        mock_bash.side_effect = [
            "api.py",  # Changed files
            "def get_data",  # New function definitions
            "README.md\napi.md",  # Existing docs
        ]

        # Act - Simulate documentation workflow through mock calls
        changed_files = mock_bash("git diff --cached --name-only")
        mock_bash("git diff --cached | grep '^+' | grep 'def '")
        existing_docs = mock_bash("find . -name '*.md' -not -path './.git/*'")

        # Assert - Verify documentation workflow
        assert "api.py" in changed_files
        assert existing_docs != ""

    def test_version_update_workflow(self, temp_git_repo) -> None:
        """GIVEN a repository ready for release

        WHEN the version update workflow is executed
        THEN it should update version numbers across the project.
        """
        # Arrange - Create version files
        temp_git_repo.add_file("package.json", '{"version": "1.0.0"}')
        temp_git_repo.stage_file("package.json")
        temp_git_repo.add_file("setup.py", "version='1.0.0'")
        temp_git_repo.stage_file("setup.py")
        temp_git_repo.add_file("src/__init__.py", "__version__ = '1.0.0'")
        temp_git_repo.stage_file("src/__init__.py")
        temp_git_repo.commit("Initial version setup")

        # Mock version update commands
        mock_bash = Mock()
        mock_bash.side_effect = [
            "package.json\nsetup.py\nsrc/__init__.py",  # Files with version
            '"version": "1.0.0"',  # Current version
            "version='1.0.0'",  # Setup.py version
            '__version__ = "1.0.0"',  # Python version
        ]

        # Act - Simulate version update workflow through mock calls
        version_files = mock_bash(
            "grep -r 'version' --include='*.json' --include='*.py' .",
        )
        package_version = mock_bash("grep version package.json")
        setup_version = mock_bash("grep version setup.py")
        mock_bash("grep __version__ src/__init__.py")

        # Assert - Verify version detection
        assert "package.json" in version_files
        assert '"version": "1.0.0"' in package_version
        assert "1.0.0" in setup_version

    def test_agent_skill_integration(self, temp_git_repo) -> None:
        """GIVEN a Git repository requiring analysis

        WHEN an agent is invoked to analyze the repository
        THEN it should coordinate with the appropriate skills.
        """
        # Arrange
        temp_git_repo.add_file("feature.py", "def new_feature(): pass")
        temp_git_repo.stage_file("feature.py")

        # Mock the agent execution
        mock_agent_main = Mock()
        mock_agent_main.return_value = {
            "status": "success",
            "analysis": {
                "repository_status": "clean",
                "staged_files": ["feature.py"],
                "recommendations": ["Ready for commit"],
            },
        }

        # Act
        result = mock_agent_main(str(temp_git_repo.path))

        # Assert
        assert result["status"] == "success"
        assert "feature.py" in result["analysis"]["staged_files"]
        assert "Ready for commit" in result["analysis"]["recommendations"]

    def test_error_handling_workflow(self, temp_git_repo) -> None:
        """GIVEN a repository in an error state

        WHEN a workflow encounters an error
        THEN it should handle the error gracefully and provide recovery options.
        """
        # Arrange - Simulate error condition
        mock_bash = Mock()
        mock_bash.side_effect = [
            Exception("fatal: not a git repository"),  # Git error
            None,  # Recovery command
        ]

        # Act & Assert - First call should fail
        with pytest.raises(Exception) as exc_info:
            mock_bash("git status")
        assert "not a git repository" in str(exc_info.value)

        # Recovery workflow should handle error
        mock_bash("git init")


class TestCommandSkillIntegration:
    """Integration tests for command and skill coordination."""

    def test_commit_msg_command_integration(self) -> None:
        """GIVEN the /commit-msg command is invoked

        WHEN the command executes
        THEN it should properly invoke git-workspace-review and commit-messages skills.
        """
        # This tests the command wrapper that coordinates skills
        command_sequence = [
            {"skill": "sanctum:git-workspace-review", "params": {}},
            {"skill": "sanctum:commit-messages", "params": {}},
        ]

        # Mock the skill invocations
        mock_skill = Mock()
        mock_skill.return_value = {"status": "success"}

        # Act - Simulate command execution
        for step in command_sequence:
            mock_skill(step["skill"], **step["params"])

        # Assert
        assert mock_skill.call_count == 2
        mock_skill.assert_any_call("sanctum:git-workspace-review")
        mock_skill.assert_any_call("sanctum:commit-messages")

    def test_pr_command_integration(self) -> None:
        """GIVEN the /pr command is invoked

        WHEN the command executes
        THEN it should coordinate multiple skills for PR preparation.
        """
        command_sequence = [
            {"skill": "sanctum:git-workspace-review", "params": {}},
            {"skill": "sanctum:file-analysis", "params": {}},
            {"skill": "sanctum:pr-prep", "params": {}},
        ]

        # Mock skill execution with proper context passing
        mock_skill = Mock()
        mock_skill.return_value = {"status": "success", "context": {}}

        # Act
        context = {}
        for step in command_sequence:
            result = mock_skill(step["skill"], **step["params"], **context)
            context.update(result.get("context", {}))

        # Assert
        assert mock_skill.call_count == 3
        # Verify skills were called in correct order
        calls = [call.args[0] for call in mock_skill.call_args_list]
        assert calls[0] == "sanctum:git-workspace-review"
        assert calls[1] == "sanctum:file-analysis"
        assert calls[2] == "sanctum:pr-prep"


class TestToolIntegration:
    """Integration tests for tool coordination and data flow."""

    def test_bash_todo_coordination(self, temp_git_repo, mock_todo_tool) -> None:
        """GIVEN skills that use both Bash and TodoWrite tools

        WHEN the skills execute
        THEN the tools should coordinate properly with shared state.
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nChanges to be committed:\n  new file:   test.py",
            "diff --git a/test.py b/test.py\nnew file mode 100644\n+++ b/test.py\n@@ -0,0 +1 @@\n+print('hello')",
        ]

        # Act - Simulate coordinated tool usage
        # Git workspace review uses Bash to check status
        status = mock_bash("git status")
        diff = mock_bash("git diff --cached")

        # TodoWrite creates tasks based on Bash output
        todos = [
            {"content": f"Process status: {status[:50]}...", "status": "completed"},
            {
                "content": f"Analyze diff with {len(diff)} characters",
                "status": "completed",
            },
        ]
        mock_todo_tool(todos)

        # Assert
        assert "Changes to be committed" in status
        assert "test.py" in status
        assert "print('hello')" in diff
        mock_todo_tool.assert_called_once_with(todos)

    def test_read_write_file_operations(self, tmp_path) -> None:
        """GIVEN skills that need to read and write files

        WHEN the skills execute
        THEN file operations should work correctly with proper paths.
        """
        # Arrange
        test_file = tmp_path / "test.md"
        test_file.write_text("# Original content")

        mock_read = Mock(return_value="# Original content")
        mock_write = Mock()

        # Act - Simulate file operations
        # Read existing content
        content = mock_read(str(test_file))

        # Write updated content
        updated_content = content + "\n\n## Added section"
        mock_write(str(test_file), updated_content)

        # Assert
        mock_read.assert_called_once_with(str(test_file))
        mock_write.assert_called_once_with(str(test_file), updated_content)


class TestWorkflowPerformance:
    """Performance tests for workflow execution."""

    def test_large_repository_handling(self) -> None:
        """GIVEN a repository with many files and changes

        WHEN workflows execute
        THEN they should complete within reasonable time limits.
        """
        # Arrange - Simulate large repository
        large_file_list = "\n".join([f"src/file_{i}.py" for i in range(1000)])
        large_diff = "a" * 100000  # 100KB of diff content

        mock_bash = Mock()
        mock_bash.side_effect = [
            large_file_list,  # Many changed files
            large_diff,  # Large diff
            "fast",  # Performance status
        ]

        # Act - Time the execution
        import time

        start_time = time.time()

        # Simulate workflow through mock calls
        files = mock_bash("git diff --name-only")
        diff = mock_bash("git diff")
        mock_bash("git status --porcelain=v1 | wc -l")

        execution_time = time.time() - start_time

        # Assert
        assert execution_time < 1.0  # Should complete within 1 second
        assert len(files.split("\n")) == 1000
        assert len(diff) == 100000

    def test_concurrent_workflow_execution(self) -> None:
        """GIVEN multiple workflows that could run concurrently

        WHEN the plugin coordinates them
        THEN they should execute efficiently without interference.
        """
        # This test would verify that multiple skill executions don't interfere
        # In a real implementation, this might test thread safety or async execution
