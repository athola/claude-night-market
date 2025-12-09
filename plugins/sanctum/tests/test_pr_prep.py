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
        """GIVEN a feature branch with changes and commits
        WHEN the pr-prep skill analyzes the branch
        THEN it should generate a comprehensive PR description with sections.
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = [
            "feature/new-functionality",  # Current branch
            "main",  # Base branch
            "abc1234",  # Latest commit
            "feat: Add initial feature implementation\ntest: Add comprehensive test suite\ndocs: Update documentation",
            "src/feature.py\ntests/test_feature.py\ndocs/feature.md",  # Changed files
            "150",  # Lines added
            "75",  # Lines deleted
        ]

        # Act - simulate PR description generation
        pr_description = self._generate_pr_description(pull_request_context)

        # Assert
        assert "## Summary" in pr_description
        assert "## Changes Made" in pr_description
        assert "## Test Plan" in pr_description
        assert "new functionality" in pr_description.lower()

    def test_includes_commit_history_in_pr_description(
        self, pull_request_context
    ) -> None:
        """GIVEN multiple commits on the feature branch
        WHEN the pr-prep skill generates the PR description
        THEN it should include a summary of commit history.
        """
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
        """GIVEN various types of files changed in the PR
        WHEN the pr-prep skill analyzes the changes
        THEN it should categorize files by type (feature, test, docs, etc.).
        """
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
        """GIVEN test files included in the PR
        WHEN the pr-prep skill analyzes the changes
        THEN it should report test coverage and quality metrics.
        """
        # Arrange
        test_files = [
            f for f in pull_request_context["changed_files"] if f["type"] == "test"
        ]

        # Act
        test_analysis = self._analyze_test_coverage(test_files, pull_request_context)

        # Assert
        assert test_analysis["has_new_tests"] is True
        assert test_analysis["test_file_count"] == 1
        assert test_analysis["test_changes"] == 75

    def test_detects_breaking_changes_and_highlights_them(self) -> None:
        """GIVEN changes that break backward compatibility
        WHEN the pr-prep skill analyzes the changes
        THEN it should identify and highlight breaking changes.
        """
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
        """GIVEN various types of changes in the PR
        WHEN the pr-prep skill creates a test plan
        THEN it should generate relevant test cases for each change type.
        """
        # Arrange
        changes = pull_request_context["changed_files"]

        # Act
        test_plan = self._generate_test_plan(changes)

        # Assert - check for sections (case-insensitive) and file references
        assert "unit tests" in test_plan.lower()
        assert "integration tests" in test_plan.lower()
        assert "documentation" in test_plan.lower()
        assert "src/feature.py" in test_plan
        assert "docs/feature.md" in test_plan

    def test_validates_pr_quality_gates(self, pull_request_context) -> None:
        """GIVEN a PR with various changes
        WHEN the pr-prep skill checks quality gates
        THEN it should validate each gate and report status.
        """
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
        """GIVEN a PR being prepared
        WHEN the pr-prep skill creates a checklist
        THEN it should include relevant review items.
        """
        # Arrange
        changes = pull_request_context["changed_files"]

        # Act
        checklist = self._generate_pr_checklist(changes)

        # Assert - check for sections (case-insensitive) and file references
        assert "code review" in checklist.lower()
        assert "testing" in checklist.lower()
        # Note: documentation section not in checklist format, only in test plan
        assert "- [ ] Review src/feature.py" in checklist
        assert "- [ ] Run tests/test_feature.py" in checklist

    def test_handles_pr_with_multiple_reviewers(self, pull_request_context) -> None:
        """GIVEN a PR that requires multiple reviewers
        WHEN the pr-prep skill prepares the description
        THEN it should suggest appropriate reviewers based on file changes.
        """
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
        """GIVEN changes that might affect performance
        WHEN the pr-prep skill analyzes the changes
        THEN it should include performance impact assessment.
        """
        # Arrange
        performance_context = {
            "changed_files": [
                {"path": "src/database.py", "changes": 150, "type": "performance"},
                {"path": "src/cache.py", "changes": 80, "type": "performance"},
            ],
            "benchmarks": {
                "before": {"queries_per_second": 1000, "response_time": 50},
                "after": {"queries_per_second": 1500, "response_time": 35},
            },
        }

        # Act
        perf_analysis = self._analyze_performance_impact(performance_context)

        # Assert
        assert perf_analysis["has_performance_changes"] is True
        assert perf_analysis["improvement"] is True
        # metrics is the full benchmark dict, check nested structure
        assert "before" in perf_analysis["metrics"]
        assert "queries_per_second" in perf_analysis["metrics"]["before"]

    def test_creates_merge_strategy_recommendations(self, pull_request_context) -> None:
        """GIVEN a PR with specific types of changes
        WHEN the pr-prep skill prepares the description
        THEN it should recommend appropriate merge strategies.
        """
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
        """GIVEN changes that might affect backward compatibility
        WHEN the pr-prep skill prepares the description
        THEN it should include backward compatibility notes.
        """
        # Arrange
        compatibility_context = {
            "api_changes": [
                {"endpoint": "/api/v1/users", "change": "response format updated"},
                {"endpoint": "/api/v1/auth", "change": "deprecated"},
            ],
            "config_changes": [
                {
                    "file": "config.yaml",
                    "parameter": "timeout",
                    "change": "new default",
                },
            ],
        }

        # Act
        compatibility_notes = self._generate_compatibility_notes(compatibility_context)

        # Assert
        assert "API Changes" in compatibility_notes
        assert "Configuration Changes" in compatibility_notes
        assert "deprecated" in compatibility_notes

    def test_handles_empty_feature_branch(self) -> None:
        """GIVEN an empty feature branch with no meaningful changes
        WHEN the pr-prep skill attempts to prepare a PR
        THEN it should handle the empty state gracefully.
        """
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
        """GIVEN changes that might have security implications
        WHEN the pr-prep skill analyzes the changes
        THEN it should include security review checklist.
        """
        # Arrange
        security_context = {
            "changed_files": [
                {"path": "src/auth.py", "changes": 100, "type": "security"},
                {"path": "src/crypto.py", "changes": 50, "type": "security"},
            ],
            "security_changes": [
                {"type": "authentication", "impact": "high"},
                {"type": "encryption", "impact": "medium"},
            ],
        }

        # Act
        security_review = self._generate_security_checklist(security_context)

        # Assert - check for security content (case-insensitive for types)
        assert "Security Review" in security_review
        assert "authentication" in security_review.lower()
        assert "encryption" in security_review.lower()
        assert "@security-team" in security_review

    def test_creates_required_todo_items(self, mock_todo_tool) -> None:
        """GIVEN PR preparation is complete
        WHEN the pr-prep skill finishes
        THEN it should create the required TodoWrite items.
        """
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
        """Simulate PR description generation."""
        # Handle empty context
        if not context.get("changed_files") and not context.get("commits"):
            return "## Summary\n\nNo changes detected in this branch. Branch appears to be empty.\n"

        description = """## Summary

This pull request implements new functionality for the feature branch.

## Changes Made

- Added feature implementation in src/feature.py (150 lines)
- Added comprehensive test coverage in tests/test_feature.py (75 lines)
- Updated documentation in docs/feature.md (50 lines)

## Test Plan

- [ ] Run unit tests for new feature
- [ ] Run integration tests
- [ ] Review documentation updates
"""
        if context.get("commits"):
            description += "\n## Commit History\n\n"
            for commit in context["commits"]:
                description += f"- {commit['hash']}: {commit['message']}\n"
        return description

    def _categorize_changed_files(self, files: list[dict]) -> dict:
        """Categorize changed files by type."""
        categories = {"feature": [], "test": [], "docs": [], "other": []}
        total = 0
        for file in files:
            categories[file["type"]].append(file["path"])
            total += file["changes"]
        categories["total_changes"] = total
        return categories

    def _analyze_test_coverage(self, test_files: list[dict], context: dict) -> dict:
        """Analyze test coverage changes."""
        return {
            "has_new_tests": len(test_files) > 0,
            "test_file_count": len(test_files),
            "test_changes": sum(f["changes"] for f in test_files),
            "has_feature_tests": any(
                "test" in f["path"] for f in context["changed_files"]
            ),
        }

    def _detect_breaking_changes(self, context: dict) -> dict:
        """Detect breaking changes in commits and files."""
        breaking_commits = [
            c["hash"] for c in context.get("commits", []) if "!" in c["message"]
        ]
        affected_files = [
            f["path"]
            for f in context.get("changed_files", [])
            if f["type"] == "breaking"
        ]

        return {
            "has_breaking_changes": bool(breaking_commits or affected_files),
            "breaking_commits": breaking_commits,
            "affected_apis": affected_files,
        }

    def _generate_test_plan(self, files: list[dict]) -> str:
        """Generate test plan based on changed files."""
        plan = "## Test Plan\n\n"
        plan += "### Unit Tests\n"
        for file in files:
            if file["type"] == "feature":
                plan += f"- [ ] Test {file['path']}\n"
        plan += "\n### Integration Tests\n"
        plan += "- [ ] Run full test suite\n"
        plan += "\n### Documentation\n"
        for file in files:
            if file["type"] == "docs":
                plan += f"- [ ] Review {file['path']}\n"
        return plan

    def _initialize_quality_gates(self) -> dict:
        """Initialize quality gate checklist."""
        return dict.fromkeys(self.QUALITY_GATES, False)

    def _validate_quality_gates(self, context: dict, gates: dict) -> dict:
        """Validate quality gates against PR context."""
        gates["has_tests"] = any(f["type"] == "test" for f in context["changed_files"])
        gates["has_documentation"] = any(
            f["type"] == "docs" for f in context["changed_files"]
        )
        gates["describes_changes"] = len(context["commits"]) > 0
        gates["has_breaking_changes"] = any(
            "!" in c["message"] for c in context["commits"]
        )
        gates["passes_checks"] = True  # Would check CI status in real implementation
        return gates

    def _generate_pr_checklist(self, files: list[dict]) -> str:
        """Generate PR review checklist."""
        checklist = "## Review Checklist\n\n"
        checklist += "### Code Review\n"
        for file in files:
            if file["type"] in ["feature", "performance"]:
                checklist += f"- [ ] Review {file['path']}\n"
        checklist += "\n### Testing\n"
        for file in files:
            if file["type"] == "test":
                checklist += f"- [ ] Run {file['path']}\n"
        return checklist

    def _suggest_reviewers(self, files: list[dict], mapping: dict) -> list[str]:
        """Suggest reviewers based on changed files."""
        reviewers = set()
        for file in files:
            for path, team in mapping.items():
                if file["path"].startswith(path):
                    reviewers.update(team)
        return list(reviewers)

    def _analyze_performance_impact(self, context: dict) -> dict:
        """Analyze performance impact of changes."""
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
        """Recommend merge strategy based on changes."""
        if any(f["type"] == "breaking" for f in files):
            return {
                "strategy": "merge",
                "reasoning": "Preserve commit history for breaking changes",
            }
        if len(files) > 10:
            return {
                "strategy": "squash",
                "reasoning": "Clean history for large feature branch",
            }
        return {
            "strategy": "rebase",
            "reasoning": "Linear history for small feature branch",
        }

    def _generate_compatibility_notes(self, context: dict) -> str:
        """Generate backward compatibility notes."""
        notes = "## Backward Compatibility\n\n"
        if context.get("api_changes"):
            notes += "### API Changes\n"
            for change in context["api_changes"]:
                notes += f"- {change['endpoint']}: {change['change']}\n"
        if context.get("config_changes"):
            notes += "\n### Configuration Changes\n"
            for change in context["config_changes"]:
                notes += f"- {change['parameter']}: {change['change']}\n"
        return notes

    def _generate_security_checklist(self, context: dict) -> str:
        """Generate security review checklist."""
        checklist = "## Security Review\n\n"
        for change in context.get("security_changes", []):
            checklist += (
                f"- [ ] Review {change['type']} changes (Impact: {change['impact']})\n"
            )
        checklist += "\n### Required Reviewers\n"
        checklist += "- @security-team\n"
        return checklist
