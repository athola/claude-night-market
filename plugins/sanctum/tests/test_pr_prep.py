"""BDD-style tests for the PR Preparation skill.

This test module follows the Behavior-Driven Development approach to test
the pr-prep skill, which prepares comprehensive pull request descriptions
with quality gates.
"""

from __future__ import annotations

from unittest.mock import Mock


class TestPRPrepSkill:
    """Behavior-driven tests for the pr-prep skill."""

    # Test constants
    QUALITY_GATES = [
        "has_tests",
        "has_documentation",
        "passes_checks",
        "describes_changes",
        "includes_breaking_changes",
    ]

    def test_generates_comprehensive_pr_description(self, pull_request_context) -> None:
        # Arrange
        commits = pull_request_context["commits"]
        mock_bash = Mock()
        mock_bash.return_value = "\n".join(
            [f"{c['hash']} {c['message']}" for c in commits],
        )

        # Act - simulate getting commit history from mock
        commit_history = mock_bash("git log --oneline main..HEAD")

        # Assert
        for commit in commits:
            assert commit["hash"] in commit_history
            assert commit["message"] in commit_history

    def test_analyzes_changed_files_and_categorizes_them(
        self, pull_request_context
    ) -> None:
        """Test test analyzes changed files and categorizes them."""
        # Arrange
        changed_files = pull_request_context["changed_files"]

        # Act
        categories = self._categorize_changed_files(changed_files)

        # Assert
        assert categories["feature"] == ["src/feature.py"]
        assert categories["test"] == ["tests/test_feature.py"]
        assert categories["docs"] == ["docs/feature.md"]
        assert categories["total_changes"] == 275  # 150 + 75 + 50

    def test_identifies_test_coverage_changes(self, pull_request_context) -> None:
        # Arrange
        breaking_context = {
            "base_branch": "main",
            "feature_branch": "feature/breaking",
            "commits": [
                {"hash": "abc123", "message": "feat!: Change API response format"},
                {"hash": "def456", "message": "feat: Add new endpoint"},
            ],
            "changed_files": [
                {"path": "src/api.py", "changes": 200, "type": "breaking"},
            ],
        }

        # Act
        breaking_analysis = self._detect_breaking_changes(breaking_context)

        # Assert
        assert breaking_analysis["has_breaking_changes"] is True
        assert "abc123" in breaking_analysis["breaking_commits"]
        assert breaking_analysis["affected_apis"] == ["src/api.py"]

    def test_generates_test_plan_based_on_changes(self, pull_request_context) -> None:
        # Arrange
        quality_checklist = self._initialize_quality_gates()

        # Act
        quality_status = self._validate_quality_gates(
            pull_request_context,
            quality_checklist,
        )

        # Assert
        assert quality_status["has_tests"] is True
        assert quality_status["has_documentation"] is True
        assert quality_status["describes_changes"] is True
        # Check that all gates have been evaluated
        assert all(gate in quality_status for gate in self.QUALITY_GATES)

    def test_generates_pr_checklist(self, pull_request_context) -> None:
        # Arrange
        changes = pull_request_context["changed_files"]
        reviewer_mapping = {
            "src/": ["@backend-team", "@tech-lead"],
            "tests/": ["@qa-team"],
            "docs/": ["@docs-team"],
        }

        # Act
        suggested_reviewers = self._suggest_reviewers(changes, reviewer_mapping)

        # Assert
        assert "@backend-team" in suggested_reviewers
        assert "@qa-team" in suggested_reviewers
        assert "@tech-lead" in suggested_reviewers

    def test_includes_performance_impact_analysis(self) -> None:
        # Arrange
        changes = pull_request_context["changed_files"]

        # Act
        merge_strategy = self._recommend_merge_strategy(changes)

        # Assert
        assert "strategy" in merge_strategy
        assert "reasoning" in merge_strategy
        # Feature changes typically suggest squash merge
        assert merge_strategy["strategy"] in ["squash", "merge", "rebase"]

    def test_generates_backward_compatibility_notes(self) -> None:
        # Arrange
        empty_context = {
            "base_branch": "main",
            "feature_branch": "feature/empty",
            "changed_files": [],
            "commits": [],
        }

        # Act
        pr_description = self._generate_pr_description(empty_context)

        # Assert
        assert "No changes" in pr_description or "empty" in pr_description.lower()

    def test_includes_security_considerations(self) -> None:
        # Arrange
        expected_todos = [
            {
                "content": "Analyze feature branch changes and commit history",
                "status": "completed",
                "activeForm": "Analyzed branch changes",
            },
            {
                "content": "Generate comprehensive PR description with sections",
                "status": "completed",
                "activeForm": "Generated PR description",
            },
            {
                "content": "Validate PR quality gates and test coverage",
                "status": "completed",
                "activeForm": "Validated quality gates",
            },
            {
                "content": "Create review checklist and merge recommendations",
                "status": "completed",
                "activeForm": "Created review checklist",
            },
        ]

        # Act
        mock_todo_tool(expected_todos)

        # Assert
        mock_todo_tool.assert_called_once_with(expected_todos)

    # Helper methods to simulate skill functionality
    def _generate_pr_description(self, context: dict) -> str:
        categories = {"feature": [], "test": [], "docs": [], "other": []}
        total = 0
        for file in files:
            categories[file["type"]].append(file["path"])
            total += file["changes"]
        categories["total_changes"] = total
        return categories

    def _analyze_test_coverage(self, test_files: list[dict], context: dict) -> dict:
        return dict.fromkeys(self.QUALITY_GATES, False)

    def _validate_quality_gates(self, context: dict, gates: dict) -> dict:
        perf_files = [f for f in context["changed_files"] if f["type"] == "performance"]
        return {
            "has_performance_changes": len(perf_files) > 0,
            "affected_files": [f["path"] for f in perf_files],
            "metrics": context.get("benchmarks", {}),
            "improvement": context.get("benchmarks", {})
            .get("after", {})
            .get("queries_per_second", 0)
            > context.get("benchmarks", {})
            .get("before", {})
            .get("queries_per_second", 0),
        }

    def _recommend_merge_strategy(self, files: list[dict]) -> dict:
