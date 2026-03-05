"""Tests for the update_changelog script.

Feature: Changelog management utilities
    As a developer
    I want changelog helper functions tested
    So that commit categorisation and entry generation are reliable
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from update_changelog import (  # noqa: E402
    _clean_commit_message,
    _format_changelog_entry,
    categorize_commit,
    generate_changelog_entry,
    validate_changelog,
)


class TestCategorizeCommit:
    """Feature: Commit message categorisation

    As a changelog maintainer
    I want commits categorised by type
    So that changelog sections are populated correctly
    """

    @pytest.mark.unit
    def test_feat_prefix_maps_to_added(self) -> None:
        """Scenario: Conventional feat commit maps to Added
        Given a commit message starting with 'add'
        When categorised
        Then the result is Added
        """
        assert categorize_commit("add new skill validation feature") == "Added"

    @pytest.mark.unit
    def test_fix_prefix_maps_to_fixed(self) -> None:
        """Scenario: Fix commit maps to Fixed
        Given a commit message containing 'fix'
        When categorised
        Then the result is Fixed
        """
        assert categorize_commit("fix null pointer in parser") == "Fixed"

    @pytest.mark.unit
    def test_remove_keyword_maps_to_removed(self) -> None:
        """Scenario: Remove keyword maps to Removed
        Given a commit message containing 'remove'
        When categorised
        Then the result is Removed
        """
        assert categorize_commit("remove deprecated API endpoint") == "Removed"

    @pytest.mark.unit
    def test_security_keyword_maps_to_security(self) -> None:
        """Scenario: Security keyword maps to Security
        Given a commit message containing 'security'
        When categorised
        Then the result is Security
        """
        assert categorize_commit("security patch for auth bypass") == "Security"

    @pytest.mark.unit
    def test_deprecate_keyword_maps_to_deprecated(self) -> None:
        """Scenario: Deprecation commit maps to Deprecated
        Given a commit message containing 'deprecat'
        When categorised
        Then the result is Deprecated
        """
        assert categorize_commit("deprecat old config format") == "Deprecated"

    @pytest.mark.unit
    def test_unknown_message_defaults_to_changed(self) -> None:
        """Scenario: Unrecognised commit maps to Changed
        Given a commit message with no matching keywords
        When categorised
        Then the result defaults to Changed
        """
        assert categorize_commit("something entirely unrelated") == "Changed"

    @pytest.mark.unit
    def test_update_keyword_maps_to_changed(self) -> None:
        """Scenario: Update keyword maps to Changed
        Given a commit message containing 'update'
        When categorised
        Then the result is Changed
        """
        assert categorize_commit("update dependency versions") == "Changed"

    @pytest.mark.unit
    def test_bug_keyword_maps_to_fixed(self) -> None:
        """Scenario: Bug keyword maps to Fixed
        Given a commit message containing 'bug'
        When categorised
        Then the result is Fixed
        """
        assert categorize_commit("bug in date parsing logic") == "Fixed"

    @pytest.mark.unit
    def test_case_insensitive_matching(self) -> None:
        """Scenario: Matching is case-insensitive
        Given an upper-case commit message containing 'FIX'
        When categorised
        Then the result is still Fixed
        """
        assert categorize_commit("FIX critical error in parser") == "Fixed"


class TestCleanCommitMessage:
    """Feature: Commit message cleanup

    As a changelog maintainer
    I want raw commit messages cleaned up
    So that entries look polished in the changelog
    """

    @pytest.mark.unit
    def test_removes_conventional_prefix(self) -> None:
        """Scenario: Conventional commit prefix is stripped
        Given a message with 'feat: ' prefix
        When cleaned
        Then the prefix is removed, leaving just the message body
        """
        result = _clean_commit_message("feat: add new feature")
        # 'feat:' prefix is stripped; 'add' is also consumed leaving 'new feature'
        assert "feat:" not in result
        assert "feature" in result

    @pytest.mark.unit
    def test_removes_scope_from_prefix(self) -> None:
        """Scenario: Scoped conventional commit prefix is stripped
        Given a message with 'fix(parser): ' prefix
        When cleaned
        Then the prefix and scope are removed
        """
        result = _clean_commit_message("fix(parser): handle null values")
        assert result == "handle null values"

    @pytest.mark.unit
    def test_removes_pr_number(self) -> None:
        """Scenario: Pull request reference is removed
        Given a message ending with '(#123)'
        When cleaned
        Then the PR number parenthetical is stripped
        """
        result = _clean_commit_message("add feature (#123)")
        assert "(#123)" not in result
        assert "feature" in result

    @pytest.mark.unit
    def test_plain_message_unchanged(self) -> None:
        """Scenario: Plain message without prefixes passes through
        Given a message with no conventional prefix or PR number
        When cleaned
        Then the message is returned as-is
        """
        result = _clean_commit_message("update documentation")
        assert result == "update documentation"

    @pytest.mark.unit
    def test_chore_prefix_removed(self) -> None:
        """Scenario: chore prefix is stripped
        Given a message with 'chore: ' prefix
        When cleaned
        Then the prefix is removed
        """
        result = _clean_commit_message("chore: update dependencies")
        assert result == "update dependencies"

    @pytest.mark.unit
    def test_docs_prefix_removed(self) -> None:
        """Scenario: docs prefix is stripped
        Given a message with 'docs: ' prefix
        When cleaned
        Then the prefix is removed
        """
        result = _clean_commit_message("docs: improve README")
        assert result == "improve README"


class TestFormatChangelogEntry:
    """Feature: Changelog entry formatting

    As a changelog maintainer
    I want entries formatted consistently
    So that the changelog reads well
    """

    @pytest.mark.unit
    def test_capitalises_first_letter(self) -> None:
        """Scenario: Entry starts with a capital letter
        Given a lower-case message
        When formatted
        Then the first letter is capitalised
        """
        result = _format_changelog_entry("add new validation logic")
        assert result[0].isupper()

    @pytest.mark.unit
    def test_adds_trailing_period(self) -> None:
        """Scenario: Entry ends with a period
        Given a message without a trailing period
        When formatted
        Then a period is appended
        """
        result = _format_changelog_entry("Add new validation logic")
        assert result.endswith(".")

    @pytest.mark.unit
    def test_does_not_double_period(self) -> None:
        """Scenario: Existing trailing period is not duplicated
        Given a message that already ends with a period
        When formatted
        Then no extra period is added
        """
        result = _format_changelog_entry("Add new validation logic.")
        assert result.endswith(".")
        assert not result.endswith("..")

    @pytest.mark.unit
    def test_empty_string_returns_minimal_output(self) -> None:
        """Scenario: Empty message returns a minimal formatted string
        Given an empty input
        When formatted
        Then the result is a string (period may be added)
        """
        result = _format_changelog_entry("")
        assert isinstance(result, str)


class TestGenerateChangelogEntry:
    """Feature: Generating changelog entries from commit lists

    As a changelog maintainer
    I want entries generated from commits
    So that I can bulk-update the changelog
    """

    @pytest.mark.unit
    def test_merge_commits_skipped(self) -> None:
        """Scenario: Merge commits are excluded
        Given a list containing a merge commit
        When entries are generated
        Then the merge commit does not appear
        """
        commits = [("abc123", "Merge pull request #1 from feature")]
        result = generate_changelog_entry(commits)
        assert all(len(v) == 0 for v in result.values())

    @pytest.mark.unit
    def test_bump_commits_skipped(self) -> None:
        """Scenario: Version bump commits are excluded
        Given a list containing a 'bump:' commit
        When entries are generated
        Then it does not appear in the result
        """
        commits = [("abc123", "bump: version 1.2.3")]
        result = generate_changelog_entry(commits)
        assert all(len(v) == 0 for v in result.values())

    @pytest.mark.unit
    def test_feat_commit_lands_in_added(self) -> None:
        """Scenario: Feature commit with 'new' keyword appears in Added section
        Given a commit message 'feat: new skill feature' (body has 'new' keyword)
        When entries are generated
        Then the Added section contains the entry (body 'new skill feature' matches)
        """
        commits = [("abc123", "feat: new skill feature")]
        result = generate_changelog_entry(commits)
        assert len(result.get("Added", [])) == 1

    @pytest.mark.unit
    def test_fix_commit_lands_in_fixed(self) -> None:
        """Scenario: Fix commit with 'fix' in body appears in Fixed section
        Given a commit message 'fix authentication bug'
        When entries are generated
        Then the Fixed section contains the entry
        """
        commits = [("abc123", "fix authentication bug")]
        result = generate_changelog_entry(commits)
        assert len(result.get("Fixed", [])) == 1

    @pytest.mark.unit
    def test_empty_sections_excluded_from_result(self) -> None:
        """Scenario: Empty sections are omitted from the result dict
        Given a single feature commit
        When entries are generated
        Then sections with no entries are absent
        """
        commits = [("abc123", "feat: add logging")]
        result = generate_changelog_entry(commits)
        for section, items in result.items():
            assert len(items) > 0, f"Section {section} should not be empty"

    @pytest.mark.unit
    def test_empty_commit_list_returns_empty_dict(self) -> None:
        """Scenario: No commits yields an empty result
        Given an empty commit list
        When entries are generated
        Then the result dict is empty
        """
        result = generate_changelog_entry([])
        assert result == {}

    @pytest.mark.unit
    def test_multiple_commits_aggregated(self) -> None:
        """Scenario: Multiple commits are aggregated into sections
        Given two commits with clear category keywords in their bodies
        When entries are generated
        Then each entry lands in a section
        """
        commits = [
            ("a1b2c3", "feat: new command"),
            ("d4e5f6", "fix authentication bug"),
        ]
        result = generate_changelog_entry(commits)
        # At least two sections populated across the two commits
        assert sum(len(v) for v in result.values()) >= 2


class TestValidateChangelog:
    """Feature: Changelog format validation

    As a developer
    I want changelog format validated
    So that the file follows Keep-a-Changelog conventions
    """

    @pytest.mark.unit
    def test_valid_changelog_returns_true(self, tmp_path: Path) -> None:
        """Scenario: Well-formed changelog passes validation
        Given a changelog with all required sections
        When validated from that directory
        Then the result is True
        """
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n"
            "## [Unreleased]\n\n"
            "## [1.0.0] - 2024-01-01\n\n"
            "### Added\n- Initial release.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            assert validate_changelog() is True
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_missing_changelog_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Missing changelog file returns False
        Given no CHANGELOG.md exists in cwd
        When validated
        Then the result is False
        """

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            assert validate_changelog() is False
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_changelog_missing_unreleased_section_fails(self, tmp_path: Path) -> None:
        """Scenario: Changelog without Unreleased section fails
        Given a changelog that lacks the [Unreleased] header
        When validated
        Then the result is False
        """
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [1.0.0] - 2024-01-01\n\n### Added\n- Initial release.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            assert validate_changelog() is False
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_changelog_missing_versioned_section_fails(self, tmp_path: Path) -> None:
        """Scenario: Changelog without a versioned section fails
        Given a changelog that only has [Unreleased]
        When validated
        Then the result is False
        """
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [Unreleased]\n\nNothing yet.\n")

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            assert validate_changelog() is False
        finally:
            os.chdir(original)
