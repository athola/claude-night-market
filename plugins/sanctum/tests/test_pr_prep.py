# ruff: noqa: D101,D102,D103,PLR2004,E501
"""BDD-style tests for PR preparation helpers.

Tests the PRPrepAnalyzer class from src/sanctum/pr_prep.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sanctum.pr_prep import (
    BreakingChanges,
    FileCategories,
    MergeStrategy,
    PRPrepAnalyzer,
    _is_test_path,
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

    def test_detect_breaking_changes_reads_only_conventional_markers(self) -> None:
        """
        GIVEN an exclamation in a subject's prose and a BREAKING CHANGE footer
        WHEN detect_breaking_changes is called
        THEN only the footer commit and the scoped type! commit are breaking

        Any "!" in the message counted, so
        "fix: stop crashing on empty input!" was flagged and the
        BREAKING CHANGE footer was missed.
        """
        context = {
            "commits": [
                {"hash": "a1", "message": "fix: stop crashing on empty input!"},
                {
                    "hash": "b2",
                    "message": "feat(api): drop v1 routes\n\nBREAKING CHANGE: /v1 removed",
                },
                {"hash": "c3", "message": "refactor(core)!: rename the entry point"},
                {
                    "hash": "d4",
                    "message": "chore: tidy\n\nBREAKING-CHANGE: env var renamed",
                },
            ],
            "changed_files": [],
        }
        result = PRPrepAnalyzer.detect_breaking_changes(context)
        assert result.breaking_commits == ["b2", "c3", "d4"]

    def test_file_type_alone_does_not_mark_a_change_breaking(self) -> None:
        """
        GIVEN a file dict typed "breaking", a type no producer emits
        WHEN detect_breaking_changes is called
        THEN only commit messages decide (SAN-14)
        """
        context = {
            "commits": [],
            "changed_files": [
                {"path": "src/api.py", "type": "breaking"},
            ],
        }
        result = PRPrepAnalyzer.detect_breaking_changes(context)
        assert result.has_breaking_changes is False

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
        THEN every gate is None, meaning not evaluated
        """
        gates = PRPrepAnalyzer.initialize_quality_gates()
        assert (
            len(gates) == 4
        )  # describes_changes removed: paths cannot judge a description
        assert all(v is None for v in gates.values())
        assert "has_tests" in gates
        assert "has_documentation" in gates

    def test_quality_gates_do_not_pass_by_default(self) -> None:
        """
        GIVEN a gate no analyzer has evaluated
        WHEN initialize_quality_gates is called
        THEN that gate is not True
        """
        gates = PRPrepAnalyzer.initialize_quality_gates()
        assert gates["passes_checks"] is None
        assert gates["includes_breaking_changes"] is None

    def test_unevaluated_gates_stay_unevaluated_after_validation(self) -> None:
        """
        GIVEN a context with changed files
        WHEN validate_quality_gates is called
        THEN the two gates it never computes are still None
        """
        context = {"changed_files": [{"path": "src/feature.py"}]}
        result = PRPrepAnalyzer.validate_quality_gates(
            context, PRPrepAnalyzer.initialize_quality_gates()
        )
        assert result["passes_checks"] is None
        assert result["includes_breaking_changes"] is None

    def test_has_tests_ignores_latest_directory(self) -> None:
        """
        GIVEN a path whose name merely contains the substring "test"
        WHEN validate_quality_gates is called
        THEN has_tests is False
        """
        context = {"changed_files": [{"path": "plugins/latest/x.py"}]}
        result = PRPrepAnalyzer.validate_quality_gates(
            context, PRPrepAnalyzer.initialize_quality_gates()
        )
        assert result["has_tests"] is False

    def test_has_tests_matches_a_test_path_segment(self) -> None:
        """
        GIVEN a tests/ directory and a test_ prefixed module
        WHEN validate_quality_gates is called
        THEN has_tests is True for each
        """
        for path in ("plugins/a/tests/unit/test_y.py", "src/test_helpers.py"):
            result = PRPrepAnalyzer.validate_quality_gates(
                {"changed_files": [{"path": path}]},
                PRPrepAnalyzer.initialize_quality_gates(),
            )
            assert result["has_tests"] is True, path

    def test_validate_quality_gates(self) -> None:
        """
        GIVEN context and gates
        WHEN validate_quality_gates is called
        THEN gates are updated appropriately
        """
        context = {
            "changed_files": [
                {"path": "src/feature.py"},
                {"path": "tests/test_feature.py"},
                {"path": "docs/README.md"},
            ],
        }
        gates = PRPrepAnalyzer.initialize_quality_gates()
        result = PRPrepAnalyzer.validate_quality_gates(context, gates)
        # Paths cannot say whether the description states intent, so the
        # analyzer offers no gate for it.
        assert "describes_changes" not in result
        assert result["has_documentation"] is True
        assert result["has_tests"] is True

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
        THEN it is an intent skeleton, not the changed-file list

        A list of paths restates the diff, which the report already shows
        by bucket. The skeleton asks for why before what.
        """
        context = {
            "changed_files": [{"path": "src/feature.py"}, {"path": "src/other.py"}]
        }
        result = PRPrepAnalyzer.generate_pr_description(context)
        assert result.index("## Why") < result.index("## What and how")
        assert "## Test plan" in result
        assert "2 files" in result
        assert "src/feature.py" not in result
        # Only the file count is known; the merge timing is the author's call.
        assert "| **When** | on merge |" not in result

    def test_generated_scaffold_matches_the_pr_template(self) -> None:
        """The scaffold is the pr-prep template's shape, not a second copy of it."""
        template = (
            Path(__file__).resolve().parents[1]
            / "skills"
            / "pr-prep"
            / "modules"
            / "pr-template.md"
        ).read_text(encoding="utf-8")
        result = PRPrepAnalyzer.generate_pr_description(
            {"changed_files": [{"path": "a.py"}]}
        )
        headings = [line for line in result.splitlines() if line.startswith("## ")]
        labels = re.findall(r"\| (\*\*\w+\*\*) \|", result)
        assert headings
        for item in headings + labels:
            assert item in template, item

    def test_generate_pr_description_without_changes(self) -> None:
        """
        GIVEN context without changed files
        WHEN generate_pr_description is called
        THEN 'No changes' message is returned
        """
        context = {"changed_files": []}
        result = PRPrepAnalyzer.generate_pr_description(context)
        assert "No changes" in result


class TestIsTestPath:
    """Test files from the ecosystems a PR commonly touches count as tests."""

    @pytest.mark.parametrize(
        "path",
        [
            "pkg/handler_test.go",
            "web/src/__tests__/App.jsx",
            "src/app.spec.ts",
            "src/app.spec.js",
            "spec/models/user_spec.rb",
        ],
    )
    def test_non_python_test_files_are_tests(self, path: str) -> None:
        assert _is_test_path(path)

    def test_a_name_merely_containing_test_is_not_a_test(self) -> None:
        assert not _is_test_path("plugins/latest/config.py")


def test_has_documentation_true_for_rst_change() -> None:
    """The gate counted only .md while classify buckets .rst/.txt/.adoc as
    docs, so one report said both "docs" and has_documentation False (SAN-6).
    """

    gates = PRPrepAnalyzer.validate_quality_gates(
        {"changed_files": [{"path": "docs/a.rst", "type": "docs"}], "commits": []},
        PRPrepAnalyzer.initialize_quality_gates(),
    )
    assert gates["has_documentation"] is True
