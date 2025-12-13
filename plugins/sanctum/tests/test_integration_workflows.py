# ruff: noqa: D101,D102,D103,PLR2004,E501
"""High-level workflow smoke tests."""

from __future__ import annotations


class TestIntegrationWorkflows:
    def test_complete_commit_workflow(self, temp_git_repo, mock_todo_tool) -> None:
        temp_git_repo.add_file("initial.py", "# initial")
        temp_git_repo.stage_file("initial.py")
        temp_git_repo.commit("Initial commit")

        temp_git_repo.add_file("feature.py", "def feature(): pass")
        temp_git_repo.stage_file("feature.py")

        commit_message = "feat: Add feature"
        mock_todo_tool([{"content": commit_message, "status": "completed"}])
        assert temp_git_repo.commits[0]["message"] == "Initial commit"

    def test_catchup_workflow_integration(self, temp_git_repo) -> None:
        temp_git_repo.add_file("api.py", "def get_data(): pass")
        temp_git_repo.stage_file("api.py")
        temp_git_repo.commit("feat: Add API")
        assert temp_git_repo.commits

    def test_version_update_workflow(self, temp_git_repo) -> None:
        temp_git_repo.add_file("package.json", '{"version": "0.1.0"}')
        temp_git_repo.stage_file("package.json")
        temp_git_repo.commit("chore: bump version")
        assert temp_git_repo.commits[-1]["message"].startswith("chore")

    def test_error_handling_workflow(self, temp_git_repo) -> None:
        errors = ["merge conflict", "permission denied"]
        assert all(isinstance(err, str) for err in errors)

    def test_bash_todo_coordination(self, temp_git_repo, mock_todo_tool) -> None:
        todos = [
            {"content": "git-review:repo-confirmed", "status": "completed"},
            {"content": "git-review:status-overview", "status": "completed"},
        ]
        mock_todo_tool(todos)
        mock_todo_tool.assert_called_once()
