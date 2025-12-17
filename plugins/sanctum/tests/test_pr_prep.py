# ruff: noqa: D101,D102,D103,PLR2004,E501
"""BDD-style tests for PR preparation helpers.

Tests the PRPrepAnalyzer class from src/sanctum/pr_prep.py.
"""

from __future__ import annotations

from sanctum.pr_prep import (
    BreakingChanges,
    FileCategories,
    MergeStrategy,
    PRPrepAnalyzer,
)


class TestFileCategories:
    """Tests for FileCategories dataclass."""

    def test_default_initialization(self) -> None:
        """GIVEN no arguments WHEN FileCategories created THEN all lists empty."""
        categories = FileCategories()
        assert categories.feature == []
        assert categories.test == []
        assert categories.docs == []
        assert categories.other == []
        assert categories.total_changes == 0


class TestBreakingChanges:
    """Tests for BreakingChanges dataclass."""

    def test_default_initialization(self) -> None:
        """GIVEN breaking flag WHEN BreakingChanges created THEN defaults correct."""
        changes = BreakingChanges(has_breaking_changes=False)
        assert changes.has_breaking_changes is False
        assert changes.breaking_commits == []
        assert changes.affected_apis == []


class TestMergeStrategy:
    """Tests for MergeStrategy dataclass."""

    def test_initialization(self) -> None:
        """GIVEN strategy and reasoning WHEN MergeStrategy created THEN stored."""
        strategy = MergeStrategy(strategy="squash", reasoning="Clean history")
        assert strategy.strategy == "squash"
        assert strategy.reasoning == "Clean history"


class TestPRPrepAnalyzer:
    """BDD-style tests for PRPrepAnalyzer."""

    def test_categorize_changed_files_with_feature_files(self) -> None:
        """
        GIVEN files with feature type
        WHEN categorize_changed_files is called
        THEN files are placed in feature category
        """
        files = [
            {"path": "src/feature.py", "type": "feature", "changes": 50},
            {"path": "src/utils.py", "type": "feature", "changes": 30},
        ]
        result = PRPrepAnalyzer.categorize_changed_files(files)
        assert len(result.feature) == 2
        assert result.total_changes == 80

    def test_categorize_changed_files_with_test_files(self) -> None:
        """
        GIVEN files with test type
        WHEN categorize_changed_files is called
        THEN files are placed in test category
        """
        files = [{"path": "tests/test_feature.py", "type": "test", "changes": 25}]
        result = PRPrepAnalyzer.categorize_changed_files(files)
        assert len(result.test) == 1
        assert "tests/test_feature.py" in result.test

    def test_categorize_changed_files_with_docs_files(self) -> None:
        """
        GIVEN files with docs type
        WHEN categorize_changed_files is called
        THEN files are placed in docs category
        """
        files = [{"path": "docs/README.md", "type": "docs", "changes": 10}]
        result = PRPrepAnalyzer.categorize_changed_files(files)
        assert len(result.docs) == 1

    def test_categorize_changed_files_with_unknown_type(self) -> None:
        """
        GIVEN files with unknown or missing type
        WHEN categorize_changed_files is called
        THEN files are placed in other category
        """
        files = [
            {"path": "Makefile", "changes": 5},
            {"path": "config.yaml", "type": "config", "changes": 3},
        ]
        result = PRPrepAnalyzer.categorize_changed_files(files)
        assert len(result.other) == 2

    def test_detect_breaking_changes_with_bang_in_commit(self) -> None:
        """
        GIVEN commits with ! marker in message
        WHEN detect_breaking_changes is called
        THEN has_breaking_changes is True
        """
        context = {
            "commits": [
                {"hash": "abc123", "message": "feat!: Change API response format"},
                {"hash": "def456", "message": "feat: Add new endpoint"},
            ],
            "changed_files": [],
        }
        result = PRPrepAnalyzer.detect_breaking_changes(context)
        assert result.has_breaking_changes is True
        assert "abc123" in result.breaking_commits
        assert "def456" not in result.breaking_commits

    def test_detect_breaking_changes_with_breaking_file_type(self) -> None:
        """
        GIVEN files marked as breaking type
        WHEN detect_breaking_changes is called
        THEN affected_apis contains those files
        """
        context = {
            "commits": [],
            "changed_files": [
                {"path": "src/api.py", "type": "breaking"},
            ],
        }
        result = PRPrepAnalyzer.detect_breaking_changes(context)
        assert result.has_breaking_changes is True
        assert "src/api.py" in result.affected_apis

    def test_detect_breaking_changes_with_no_breaking_changes(self) -> None:
        """
        GIVEN context without breaking markers
        WHEN detect_breaking_changes is called
        THEN has_breaking_changes is False
        """
        context = {
            "commits": [{"hash": "abc123", "message": "feat: Add feature"}],
            "changed_files": [{"path": "src/feature.py", "type": "feature"}],
        }
        result = PRPrepAnalyzer.detect_breaking_changes(context)
        assert result.has_breaking_changes is False

    def test_initialize_quality_gates(self) -> None:
        """
        GIVEN no arguments
        WHEN initialize_quality_gates is called
        THEN all gates are True by default
        """
        gates = PRPrepAnalyzer.initialize_quality_gates()
        assert len(gates) == 5
        assert all(v is True for v in gates.values())
        assert "has_tests" in gates
        assert "has_documentation" in gates

    def test_validate_quality_gates(self) -> None:
        """
        GIVEN context and gates
        WHEN validate_quality_gates is called
        THEN gates are updated appropriately
        """
        context = {"changed_files": [{"path": "src/feature.py"}]}
        gates = PRPrepAnalyzer.initialize_quality_gates()
        result = PRPrepAnalyzer.validate_quality_gates(context, gates)
        assert result["describes_changes"] is True
        assert result["has_documentation"] is True

    def test_suggest_reviewers_matches_path_prefix(self) -> None:
        """
        GIVEN changes and reviewer mapping
        WHEN suggest_reviewers is called
        THEN reviewers matching path prefixes are returned
        """
        changes = [
            {"path": "src/feature.py"},
            {"path": "tests/test_feature.py"},
        ]
        mapping = {
            "src/": ["@backend-team"],
            "tests/": ["@qa-team"],
            "docs/": ["@docs-team"],
        }
        result = PRPrepAnalyzer.suggest_reviewers(changes, mapping)
        assert "@backend-team" in result
        assert "@qa-team" in result
        assert "@docs-team" not in result

    def test_suggest_reviewers_returns_sorted_list(self) -> None:
        """
        GIVEN multiple matching reviewers
        WHEN suggest_reviewers is called
        THEN result is sorted alphabetically
        """
        changes = [{"path": "src/feature.py"}]
        mapping = {"src/": ["@zeta-team", "@alpha-team"]}
        result = PRPrepAnalyzer.suggest_reviewers(changes, mapping)
        assert result == ["@alpha-team", "@zeta-team"]

    def test_recommend_merge_strategy_with_files(self) -> None:
        """
        GIVEN non-empty file list
        WHEN recommend_merge_strategy is called
        THEN squash strategy is recommended
        """
        files = [{"path": "src/feature.py"}]
        result = PRPrepAnalyzer.recommend_merge_strategy(files)
        assert result.strategy == "squash"

    def test_recommend_merge_strategy_without_files(self) -> None:
        """
        GIVEN empty file list
        WHEN recommend_merge_strategy is called
        THEN merge strategy is recommended
        """
        result = PRPrepAnalyzer.recommend_merge_strategy([])
        assert result.strategy == "merge"

    def test_generate_pr_description_with_changes(self) -> None:
        """
        GIVEN context with changed files
        WHEN generate_pr_description is called
        THEN description is generated
        """
        context = {"changed_files": [{"path": "src/feature.py"}]}
        result = PRPrepAnalyzer.generate_pr_description(context)
        assert result == "Generated PR description"

    def test_generate_pr_description_without_changes(self) -> None:
        """
        GIVEN context without changed files
        WHEN generate_pr_description is called
        THEN 'No changes' message is returned
        """
        context = {"changed_files": []}
        result = PRPrepAnalyzer.generate_pr_description(context)
        assert "No changes" in result
