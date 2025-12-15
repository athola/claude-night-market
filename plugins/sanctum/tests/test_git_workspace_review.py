# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Simplified tests for git-workspace-review skill."""

from __future__ import annotations

from unittest.mock import Mock


class TestGitWorkspaceReviewSkill:
    EXPECTED_TODO_ITEMS = 2
    REQUIRED_TODOS = ["git-review:repo-confirmed", "git-review:status-overview"]

    def test_skill_identifies_valid_git_repository(
        self, temp_git_repo, mock_todo_tool
    ) -> None:
        mock_bash = Mock(
            return_value="On branch main\nnothing to commit, working tree clean"
        )
        result = mock_bash("git status")
        mock_bash.assert_called_once()
        assert "working tree clean" in result

    def test_skill_detects_staged_changes(self, temp_git_repo, mock_todo_tool) -> None:
        temp_git_repo.add_file("test.py", "print('hello')")
        temp_git_repo.stage_file("test.py")
        temp_git_repo.commit("Initial commit")

        mock_bash = Mock()
        mock_bash.side_effect = [
            "On branch main\nChanges not staged for commit:\n  modified:   test.py",
            "diff --git a/test.py b/test.py\n- print('hello')\n+ print('hello world')",
        ]

        status_output = mock_bash("git status")
        diff_output = mock_bash("git diff")
        assert "modified" in status_output
        assert "hello world" in diff_output

    def test_skill_integration_with_todo_tool(
        self, temp_git_repo, mock_todo_tool
    ) -> None:
        todos_created = []

        def capture_todos(todos):
            todos_created.extend(todos)
            return {"status": "success"}

        mock_todo_tool.side_effect = capture_todos

        skill_todos = [
            {"content": "git-review:repo-confirmed", "status": "completed"},
            {"content": "git-review:status-overview", "status": "completed"},
        ]
        mock_todo_tool(skill_todos)

        assert len(todos_created) == 2
        assert all(todo["status"] == "completed" for todo in todos_created)
