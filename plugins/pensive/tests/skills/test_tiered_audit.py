"""Tests for the tiered audit skill.

Tests git-history analysis, escalation criteria matching,
and tier routing logic.
"""

from __future__ import annotations

import pytest

from pensive.skills.tiered_audit import (
    EscalationFlag,
    Tier1Results,
    _module_from_path,
    check_churn_hotspots,
    check_fix_on_fix,
    check_large_diffs,
    check_new_file_clusters,
    should_escalate_to_tier2,
)

# --------------- churn hotspot tests ---------------


class TestChurnHotspots:
    """Feature: Detect files with excessive churn.

    As an auditor
    I want to identify files changed too frequently
    So that I can focus deeper review on unstable areas.
    """

    @pytest.mark.unit
    def test_flags_module_with_repeated_changes(self) -> None:
        """Scenario: Module has 3+ files changed, one changed >2 times.

        Given a file change log with 4 files in plugins/imbue/
        And one file changed 3 times
        When checking for churn hotspots
        Then plugins/imbue/ is flagged.
        """
        file_changes = [
            "plugins/imbue/skills/proof-of-work/SKILL.md",
            "plugins/imbue/skills/proof-of-work/SKILL.md",
            "plugins/imbue/skills/proof-of-work/SKILL.md",
            "plugins/imbue/scripts/validator.py",
            "plugins/imbue/tests/test_validator.py",
            "plugins/imbue/README.md",
        ]
        flags = check_churn_hotspots(file_changes)
        assert len(flags) == 1
        assert "plugins/imbue" in flags[0].area

    @pytest.mark.unit
    def test_no_flag_when_no_file_changed_more_than_twice(self) -> None:
        """Scenario: Multiple files changed but none more than twice.

        Given 5 different files each changed once
        When checking for churn hotspots
        Then no areas are flagged.
        """
        file_changes = [
            "plugins/imbue/a.md",
            "plugins/imbue/b.md",
            "plugins/imbue/c.md",
            "plugins/imbue/d.md",
            "plugins/imbue/e.md",
        ]
        flags = check_churn_hotspots(file_changes)
        assert len(flags) == 0

    @pytest.mark.unit
    def test_no_flag_when_fewer_than_3_files(self) -> None:
        """Scenario: One file changed many times but only 2 unique files.

        Given 2 unique files in a module, one changed 5 times
        When checking for churn hotspots
        Then no areas are flagged (need 3+ files).
        """
        file_changes = [
            "plugins/imbue/a.md",
            "plugins/imbue/a.md",
            "plugins/imbue/a.md",
            "plugins/imbue/a.md",
            "plugins/imbue/a.md",
            "plugins/imbue/b.md",
        ]
        flags = check_churn_hotspots(file_changes)
        assert len(flags) == 0


# --------------- fix-on-fix tests ---------------


class TestFixOnFix:
    """Feature: Detect fix-on-fix commit patterns.

    As an auditor
    I want to find commits that fix previous fixes
    So that I can identify areas of instability.
    """

    @pytest.mark.unit
    def test_detects_fix_commits(self) -> None:
        """Scenario: Commit log contains fix and revert entries.

        Given a list of commit messages
        And 2 contain fix/revert keywords
        When checking for fix-on-fix patterns
        Then 2 flags are returned.
        """
        commits = [
            ("abc1234", "feat: add new validation"),
            ("def5678", "fix: correct null check in validator"),
            ("ghi9012", "refactor: clean up imports"),
            ("jkl3456", "revert: undo broken migration"),
        ]
        flags = check_fix_on_fix(commits)
        assert len(flags) == 2

    @pytest.mark.unit
    def test_no_flags_when_no_fix_commits(self) -> None:
        """Scenario: Clean commit history with no fixes.

        Given a list of commit messages with no fix keywords
        When checking for fix-on-fix patterns
        Then no flags are returned.
        """
        commits = [
            ("abc1234", "feat: add validation"),
            ("def5678", "refactor: reorganize modules"),
            ("ghi9012", "docs: update README"),
        ]
        flags = check_fix_on_fix(commits)
        assert len(flags) == 0

    @pytest.mark.unit
    def test_case_insensitive_detection(self) -> None:
        """Scenario: Fix keywords in various cases.

        Given commits with "Fix", "HOTFIX", "Patch"
        When checking for fix-on-fix patterns
        Then all are detected.
        """
        commits = [
            ("a", "Fix: capital F"),
            ("b", "HOTFIX: all caps"),
            ("c", "patch: lowercase"),
        ]
        flags = check_fix_on_fix(commits)
        assert len(flags) == 3


# --------------- large diff tests ---------------


class TestLargeDiffs:
    """Feature: Detect commits with large diffs.

    As an auditor
    I want to identify oversized commits
    So that I can review them more carefully.
    """

    @pytest.mark.unit
    def test_flags_commit_over_200_lines(self) -> None:
        """Scenario: Commit with 250 insertions in one module.

        Given a commit with 250 lines changed
        When checking for large diffs
        Then the commit is flagged.
        """
        diff_stats = [
            ("abc1234", "feat: big refactor", 250, 50),
        ]
        flags = check_large_diffs(diff_stats, threshold=200)
        assert len(flags) == 1

    @pytest.mark.unit
    def test_no_flag_under_threshold(self) -> None:
        """Scenario: Small commit under threshold.

        Given a commit with 50 lines changed
        When checking for large diffs with threshold 200
        Then no flags are returned.
        """
        diff_stats = [
            ("abc1234", "fix: small change", 30, 20),
        ]
        flags = check_large_diffs(diff_stats, threshold=200)
        assert len(flags) == 0

    @pytest.mark.unit
    def test_flags_commit_at_exact_threshold(self) -> None:
        """Scenario: Commit at exactly the threshold boundary.

        Given a commit with exactly 200 lines changed
        When checking for large diffs with threshold 200
        Then the commit is flagged (>= boundary).
        """
        diff_stats = [
            ("abc1234", "feat: borderline commit", 120, 80),
        ]
        flags = check_large_diffs(diff_stats, threshold=200)
        assert len(flags) == 1


# --------------- new file cluster tests ---------------


class TestNewFileClusters:
    """Feature: Detect modules with many new files.

    As an auditor
    I want to find modules where many files were added
    So that I can review new feature areas.
    """

    @pytest.mark.unit
    def test_flags_module_with_5_plus_new_files(self) -> None:
        """Scenario: 6 new files added to one module.

        Given 6 new files in plugins/new-plugin/
        When checking for new file clusters
        Then plugins/new-plugin is flagged.
        """
        new_files = [
            "plugins/new-plugin/a.md",
            "plugins/new-plugin/b.md",
            "plugins/new-plugin/c.md",
            "plugins/new-plugin/d.md",
            "plugins/new-plugin/e.md",
            "plugins/new-plugin/f.md",
        ]
        flags = check_new_file_clusters(new_files, threshold=5)
        assert len(flags) == 1
        assert "plugins/new-plugin" in flags[0].area

    @pytest.mark.unit
    def test_no_flag_under_threshold(self) -> None:
        """Scenario: Only 3 new files in a module.

        Given 3 new files in a module
        When checking with threshold 5
        Then no flags are returned.
        """
        new_files = [
            "plugins/foo/a.md",
            "plugins/foo/b.md",
            "plugins/foo/c.md",
        ]
        flags = check_new_file_clusters(new_files, threshold=5)
        assert len(flags) == 0


# --------------- escalation decision tests ---------------


class TestEscalationDecision:
    """Feature: Decide whether to escalate from Tier 1 to Tier 2.

    As an auditor
    I want clear escalation criteria
    So that Tier 2 runs only when warranted.
    """

    @pytest.mark.unit
    def test_escalates_when_churn_flags_exist(self) -> None:
        """Scenario: Tier 1 found churn hotspots.

        Given Tier 1 results with 1 churn flag
        When checking escalation
        Then escalation is recommended.
        """
        results = Tier1Results(
            churn_flags=[
                EscalationFlag(
                    area="plugins/imbue",
                    reason="churn",
                    detail="4 files, 1 changed 3x",
                )
            ],
            fix_flags=[],
            large_diff_flags=[],
            new_cluster_flags=[],
        )
        assert should_escalate_to_tier2(results) is True

    @pytest.mark.unit
    def test_no_escalation_when_clean(self) -> None:
        """Scenario: Tier 1 found nothing.

        Given Tier 1 results with no flags
        When checking escalation
        Then no escalation is recommended.
        """
        results = Tier1Results(
            churn_flags=[],
            fix_flags=[],
            large_diff_flags=[],
            new_cluster_flags=[],
        )
        assert should_escalate_to_tier2(results) is False

    @pytest.mark.unit
    def test_escalation_areas_are_unique(self) -> None:
        """Scenario: Same area flagged by multiple criteria.

        Given churn and fix flags both targeting plugins/imbue
        When getting escalation targets
        Then plugins/imbue appears only once.
        """
        results = Tier1Results(
            churn_flags=[
                EscalationFlag(area="plugins/imbue", reason="churn", detail="...")
            ],
            fix_flags=[
                EscalationFlag(area="plugins/imbue", reason="fix-on-fix", detail="...")
            ],
            large_diff_flags=[],
            new_cluster_flags=[],
        )
        areas = results.escalation_targets()
        assert areas == ["plugins/imbue"]


# --------------- module path extraction edge cases ---------------


class TestModuleFromPath:
    """Feature: Extract module prefix from file paths.

    As the churn/cluster analysis
    I want correct module grouping for all path shapes
    So that root-level files and shallow paths group correctly.
    """

    @pytest.mark.unit
    def test_single_component_path(self) -> None:
        """Given a root-level file like 'README.md', return it as-is."""
        assert _module_from_path("README.md") == "README.md"

    @pytest.mark.unit
    def test_two_component_path(self) -> None:
        """Given 'hooks/pre-commit.py', return 'hooks/pre-commit.py'."""
        assert _module_from_path("hooks/pre-commit.py") == "hooks/pre-commit.py"

    @pytest.mark.unit
    def test_deep_path(self) -> None:
        """Given a deep path, return first two components."""
        assert _module_from_path("plugins/imbue/skills/foo.md") == "plugins/imbue"

    @pytest.mark.unit
    def test_leading_slash_stripped(self) -> None:
        """Given a path with leading slash, strip before splitting."""
        assert _module_from_path("/plugins/imbue/foo.py") == "plugins/imbue"

    @pytest.mark.unit
    def test_empty_string(self) -> None:
        """Given an empty string, return empty string."""
        assert _module_from_path("") == ""
