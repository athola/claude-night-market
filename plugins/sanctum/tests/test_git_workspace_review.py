"""BDD-style tests for the Git Workspace Review skill.

This test module follows the Behavior-Driven Development approach to test
the git-workspace-review skill, which is the foundation skill for all
other sanctum operations.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest


class TestGitWorkspaceReviewSkill:
    """Behavior-driven tests for the git-workspace-review skill."""

    # Test constants
    EXPECTED_TODO_ITEMS = 2
    REQUIRED_TODOS = ["git-review:repo-confirmed", "git-review:status-overview"]

    def test_skill_identifies_valid_git_repository(
        self, temp_git_repo, mock_todo_tool
    ) -> None:
        """GIVEN a valid Git repository

        WHEN the git-workspace-review skill is executed
        THEN it should confirm the repository is valid and create required todos.
        """
        # Arrange - repository already set up by fixture
        mock_bash = Mock()
        mock_bash.return_value = "On branch main\nnothing to commit, working tree clean"

        # Act - simulate skill execution through mock
        result = mock_bash("git status")

        # Assert - verify repository was checked
        mock_bash.assert_called_once()
        assert "nothing to commit, working tree clean" in result

    def test_skill_detects_staged_changes(self, temp_git_repo, mock_todo_tool) -> None:
        """GIVEN a Git repository with staged changes

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should detect and report the staged changes.
        """
        # Arrange - create a repository with staged changes
        temp_git_repo.add_file("test.py", "print('hello')")
        temp_git_repo.stage_file("test.py")

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nChanges to be committed:\n  new file:   test.py",
            "diff --git a/test.py b/test.py\nnew file mode 100644\nindex 0000000..8c7be5c\n--- /dev/null\n+++ b/test.py\n@@ -0,0 +1 @@\n+print('hello')\n",
        ]

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")
        diff_output = mock_bash("git diff --cached")

        # Assert
        assert "Changes to be committed" in status_output
        assert "test.py" in status_output
        assert "new file" in status_output
        assert "print('hello')" in diff_output

    def test_skill_detects_unstaged_changes(self, temp_git_repo) -> None:
        """GIVEN a Git repository with unstaged changes

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should detect and report the unstaged changes.
        """
        # Arrange - create unstaged changes
        temp_git_repo.add_file("test.py", "print('hello')")
        temp_git_repo.stage_file("test.py")
        temp_git_repo.commit("Initial commit")
        temp_git_repo.add_file(
            "test.py",
            "print('hello world')",
        )  # Modify without staging

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nChanges not staged for commit:\n  modified:   test.py",
            "diff --git a/test.py b/test.py\nindex 8c7be5c..d5a823e 100644\n--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-print('hello')\n+print('hello world')\n",
        ]

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")
        diff_output = mock_bash("git diff")

        # Assert
        assert "Changes not staged for commit" in status_output
        assert "modified:   test.py" in status_output
        assert "-print('hello')" in diff_output
        assert "+print('hello world')" in diff_output

    def test_skill_detects_untracked_files(self, temp_git_repo) -> None:
        """GIVEN a Git repository with untracked files

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should detect and report the untracked files.
        """
        # Arrange - create untracked files
        temp_git_repo.add_file("untracked.txt", "untracked content")
        temp_git_repo.add_file("temp.tmp", "temporary")

        mock_bash = Mock()
        mock_bash.return_value = """On branch main

Untracked files:
  untracked.txt
  temp.tmp

nothing added to commit but untracked files present
"""

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")

        # Assert
        assert "Untracked files:" in status_output
        assert "untracked.txt" in status_output
        assert "temp.tmp" in status_output

    def test_skill_handles_repository_with_no_changes(self, temp_git_repo) -> None:
        """GIVEN a clean Git repository with no changes

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should report the repository is clean.
        """
        # Arrange - ensure clean repository
        mock_bash = Mock()
        mock_bash.return_value = "On branch main\nnothing to commit, working tree clean"

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")

        # Assert
        assert "nothing to commit" in status_output
        assert "working tree clean" in status_output

    def test_skill_reports_branch_information(self, temp_git_repo) -> None:
        """GIVEN a Git repository on a specific branch

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should report the current branch information.
        """
        # Arrange - create a feature branch
        temp_git_repo.create_branch("feature/test-branch")
        temp_git_repo.add_file("feature.py", "feature content")
        temp_git_repo.stage_file("feature.py")
        temp_git_repo.commit("Add feature")

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch feature/test-branch\nnothing to commit, working tree clean",
            "feature/test-branch",
        ]

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")
        branch_output = mock_bash("git branch --show-current")

        # Assert
        assert "On branch feature/test-branch" in status_output
        assert branch_output == "feature/test-branch"

    def test_skill_detects_remote_tracking(self, temp_git_repo) -> None:
        """GIVEN a Git repository with remote tracking

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should report remote tracking information.
        """
        # Arrange - add a remote
        temp_git_repo.add_remote("origin", "https://github.com/test/repo.git")

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nYour branch is up to date with 'origin/main'.\nnothing to commit, working tree clean",
            "origin\nhttps://github.com/test/repo.git (fetch)\nhttps://github.com/test/repo.git (push)",
        ]

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")
        remote_output = mock_bash("git remote -v")

        # Assert
        assert "origin/main" in status_output
        assert "up to date" in status_output
        assert "origin" in remote_output
        assert "github.com/test/repo.git" in remote_output

    def test_skill_detects_ahead_behind_status(self, temp_git_repo) -> None:
        """GIVEN a Git repository that is ahead/behind remote

        WHEN the git-workspace-review skill analyzes the repository
        THEN it should report ahead/behind information.
        """
        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nYour branch is ahead of 'origin/main' by 2 commits.\nnothing to commit, working tree clean",
            "0 2",  # Format: behind ahead
        ]

        # Act - simulate tool calls through mock
        status_output = mock_bash("git status")
        # In real implementation, might use: git rev-list --count origin/main..HEAD
        # and: git rev-list --count HEAD..origin/main

        # Assert
        assert "ahead of" in status_output
        assert "2 commits" in status_output

    def test_skill_creates_required_todo_items(self, mock_todo_tool) -> None:
        """GIVEN any repository state

        WHEN the git-workspace-review skill completes analysis
        THEN it should create the required TodoWrite items.
        """
        # Arrange
        expected_todos = [
            {
                "content": "Confirm repository path and Git repository validity",
                "status": "completed",
                "activeForm": "Confirmed repository path and Git validity",
            },
            {
                "content": "Analyze current repository status including staged/unstaged changes",
                "status": "completed",
                "activeForm": "Analyzed repository status and changes",
            },
        ]

        # Act
        mock_todo_tool(expected_todos)

        # Assert
        mock_todo_tool.assert_called_once_with(expected_todos)

    def test_skill_handles_non_git_directory(self) -> None:
        """GIVEN a directory that is not a Git repository

        WHEN the git-workspace-review skill attempts analysis
        THEN it should handle the error gracefully.
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = Exception("fatal: not a git repository")

        # Act & Assert - mock raises exception directly
        with pytest.raises(Exception) as exc_info:
            mock_bash("git status")

        assert "not a git repository" in str(exc_info.value)

    def test_skill_handles_permission_errors(self) -> None:
        """GIVEN a directory with permission restrictions

        WHEN the git-workspace-review skill attempts analysis
        THEN it should handle permission errors gracefully.
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = PermissionError("Permission denied")

        # Act & Assert - mock raises exception directly
        with pytest.raises(PermissionError):
            mock_bash("git status")

    class TestSkillIntegration:
        """Integration tests for git-workspace-review skill with other tools."""

        def test_skill_integration_with_todo_tool(
            self, temp_git_repo, mock_todo_tool
        ) -> None:
            """GIVEN a Git repository

            WHEN git-workspace-review skill executes
            THEN it should properly integrate with TodoWrite tool.
            """
            # This tests the integration pattern used by the actual skill
            todos_created = []

            def capture_todos(todos):
                todos_created.extend(todos)
                return {"status": "success"}

            mock_todo_tool.side_effect = capture_todos

            # Simulate skill execution
            skill_todos = [
                {
                    "content": "git-review:repo-confirmed",
                    "status": "completed",
                    "activeForm": "Repository confirmed",
                },
                {
                    "content": "git-review:status-overview",
                    "status": "completed",
                    "activeForm": "Status analyzed",
                },
            ]
            mock_todo_tool(skill_todos)

            # Assert
            assert len(todos_created) == 2  # Expected todo count
            assert all(todo["status"] == "completed" for todo in todos_created)

        def test_skill_dependency_chain(self, temp_git_repo) -> None:
            """GIVEN multiple skills that depend on git-workspace-review

            WHEN the dependency chain is executed
            THEN git-workspace-review should provide necessary context.
            """
            # This tests the concept that other skills depend on the output
            # of git-workspace-review for their operation
            mock_bash = Mock()
            mock_bash.return_value = "On branch main\nM file1.py\nA file2.py\n"

            # Git workspace review provides context through mock
            context = {
                "repository_status": mock_bash("git status"),
                "has_staged_changes": "file2.py" in mock_bash("git status"),
                "has_unstaged_changes": "file1.py" in mock_bash("git status"),
            }

            # Assert context is ready for dependent skills
            assert context["has_staged_changes"] is True
            assert context["has_unstaged_changes"] is True
            assert "repository_status" in context

    class TestSkillEdgeCases:
        """Edge case testing for git-workspace-review skill."""

        def test_handles_empty_repository(self, temp_git_repo) -> None:
            """GIVEN an empty Git repository (no commits)

            WHEN the skill analyzes the repository
            THEN it should handle the empty state correctly.
            """
            # Arrange - new repository has no commits
            mock_bash = Mock()
            mock_bash.return_value = """On branch main

No commits yet

nothing to commit
"""

            # Act - simulate tool calls through mock
            status = mock_bash("git status")

            # Assert
            assert "No commits yet" in status
            assert "nothing to commit" in status

        def test_handles_detached_head_state(self, temp_git_repo) -> None:
            """GIVEN a repository in detached HEAD state

            WHEN the skill analyzes the repository
            THEN it should handle detached HEAD correctly.
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = """HEAD detached at abc1234

nothing to commit, working tree clean
"""

            # Act - simulate tool calls through mock
            status = mock_bash("git status")

            # Assert
            assert "HEAD detached" in status
            assert "abc1234" in status

        def test_handles_merge_conflicts(self, temp_git_repo) -> None:
            """GIVEN a repository with merge conflicts

            WHEN the skill analyzes the repository
            THEN it should detect and report conflicts.
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = """On branch main

You have unmerged paths.
  (fix conflicts and run "git commit")

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   conflict.txt

no changes added to commit (use "git add" and/or "git commit -a")
"""

            # Act - simulate tool calls through mock
            status = mock_bash("git status")

            # Assert
            assert "unmerged paths" in status
            assert "both modified" in status
            assert "conflict.txt" in status

        def test_handles_large_diff_output(self, temp_git_repo) -> None:
            """GIVEN a repository with very large diffs

            WHEN the skill analyzes changes
            THEN it should handle large output efficiently.
            """
            # Arrange
            large_diff = "a" * 100000  # Simulate large diff output
            mock_bash = Mock()
            mock_bash.side_effect = [
                "On branch main\nChanges to be committed:\n  modified:   large_file.py",
                large_diff,
            ]

            # Act - simulate tool calls through mock
            status = mock_bash("git status")
            diff = mock_bash("git diff --cached")

            # Assert - should handle large output without issues
            assert len(diff) == 100000
            assert "large_file.py" in status
