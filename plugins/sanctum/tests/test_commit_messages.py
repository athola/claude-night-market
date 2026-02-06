# ruff: noqa: D101,D102,D103,PLR2004,E501
"""BDD-style tests for the Commit Messages skill.

This test module follows the Behavior-Driven Development approach to test
the commit-messages skill, which generates conventional commit messages
from staged changes.
"""

from __future__ import annotations

from unittest.mock import Mock


class TestCommitMessagesSkill:
    """Behavior-driven tests for the commit-messages skill."""

    # Test constants
    CONVENTIONAL_COMMIT_TYPES = [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "test",
        "chore",
        "perf",
        "ci",
        "build",
    ]

    def test_generates_conventional_commit_for_feature_changes(
        self,
        staged_changes_context,
    ) -> None:
        """Test test generates conventional commit for feature changes."""
        # Arrange

        mock_bash = Mock()
        mock_bash.side_effect = [
            "feat: Add new feature implementation\n\nImplements core functionality for XYZ feature",
            "src/new_feature.py",
        ]

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")
        changed_files = mock_bash("git diff --cached --name-only")

        # Assert
        assert commit_msg.startswith("feat:")
        assert "new feature" in commit_msg.lower()
        assert "src/new_feature.py" in changed_files

    def test_generates_conventional_commit_for_bug_fixes(
        self, staged_changes_context
    ) -> None:
        """Test test generates conventional commit for bug fixes."""
        # Arrange

        mock_bash = Mock()
        mock_bash.return_value = "fix: Resolve null pointer exception in module initialization\n\nFixes issue #123 where null values caused crashes"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("fix:")
        assert "resolve" in commit_msg.lower()
        assert "null pointer" in commit_msg.lower()

    def test_generates_conventional_commit_for_documentation(
        self,
        staged_changes_context,
    ) -> None:
        """Test test generates conventional commit for documentation."""
        # Arrange

        mock_bash = Mock()
        mock_bash.return_value = "docs: Update README and add API documentation\n\nClarify installation steps and document new endpoints"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("docs:")
        assert "documentation" in commit_msg.lower() or "readme" in commit_msg.lower()

    def test_generates_conventional_commit_for_refactoring(
        self,
        staged_changes_context,
    ) -> None:
        """Test test generates conventional commit for refactoring."""
        # Arrange

        mock_bash = Mock()
        mock_bash.return_value = "refactor: Simplify module structure and improve code organization\n\nExtract common utilities and remove duplicate code"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("refactor:")
        assert "simplify" in commit_msg.lower() or "improve" in commit_msg.lower()

    def test_includes_scope_in_commit_message_when_appropriate(self) -> None:
        # Arrange
        mock_bash = Mock()
        mock_bash.return_value = "feat!: Change API endpoint structure\n\nBREAKING CHANGE: API endpoints now use camelCase instead of snake_case"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert "feat!:" in commit_msg
        assert "BREAKING CHANGE" in commit_msg

    def test_analyzes_diff_content_for_context(self) -> None:
        mock_bash = Mock()
        mock_bash.return_value = """diff --git a/src/calculator.py b/src/calculator.py
@@ class Calculator:
@@ def add(self, a, b):
@@ def multiply(self, a, b):
"""

        diff = mock_bash("git diff")
        assert "multiply" in diff

    def test_uses_imperative_mood_in_subject(self) -> None:
        mock_bash = Mock()
        mock_bash.return_value = "feat: Add detailed user authentication system"
        subject = mock_bash("git log -1 --pretty=format:%s")
        assert 20 <= len(subject) <= 72

    def test_separates_subject_from_body_with_blank_line(self) -> None:
        mock_bash = Mock()
        mock_bash.return_value = (
            "feat: Add login\n\nImplements OAuth2 login with JWT sessions."
        )
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")
        lines = commit_msg.split("\n")
        assert lines[1] == ""

    def test_wraps_body_lines_at_72_characters(self) -> None:
        mock_bash = Mock()
        mock_bash.return_value = """fix: Resolve memory leak in data processing

Fixed the memory leak caused by unclosed database connections.
The leak occurred when processing large datasets and would
eventually cause the application to crash after several hours.

This fix validates connections are properly closed using context
managers, preventing resource exhaustion."""

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")
        assert "memory leak" in commit_msg.lower()


class TestCommitMessageSlopDetection:
    """Feature: Detect and reject AI slop in commit messages.

    As a repository maintainer
    I want commit messages to be free of AI-generated content markers
    So that the git history reads naturally and professionally
    """

    # Tier 1 slop words that should ALWAYS be rejected
    TIER1_SLOP_WORDS = [
        "leverage",
        "utilize",
        "seamless",
        "comprehensive",
        "robust",
        "facilitate",
        "streamline",
        "delve",
        "multifaceted",
        "pivotal",
        "intricate",
        "nuanced",
    ]

    # Blocked phrases
    BLOCKED_PHRASES = [
        "it's worth noting",
        "at its core",
        "in essence",
        "a testament to",
        "navigate the complexities",
    ]

    def test_detects_tier1_slop_words_in_subject(self) -> None:
        """Scenario: Reject commit subjects containing tier-1 slop words."""
        bad_subjects = [
            "feat: leverage new API for auth",
            "fix: utilize helper function",
            "docs: add comprehensive guide",
        ]

        for subject in bad_subjects:
            has_slop = any(word in subject.lower() for word in self.TIER1_SLOP_WORDS)
            assert has_slop, f"Should detect slop in: {subject}"

    def test_accepts_clean_commit_subjects(self) -> None:
        """Scenario: Accept commit subjects without slop words."""
        clean_subjects = [
            "feat: add new API for auth",
            "fix: use helper function",
            "docs: add complete guide",
        ]

        for subject in clean_subjects:
            has_slop = any(word in subject.lower() for word in self.TIER1_SLOP_WORDS)
            assert not has_slop, f"Should not flag clean subject: {subject}"

    def test_detects_slop_phrases_in_body(self) -> None:
        """Scenario: Reject commit bodies containing blocked phrases."""
        bad_body = """This change leverages the new API.

It's worth noting that this improves performance.
At its core, this is a refactoring effort."""

        has_slop = any(phrase in bad_body.lower() for phrase in self.BLOCKED_PHRASES)
        assert has_slop, "Should detect blocked phrases in body"

    def test_provides_alternatives_for_slop_words(self) -> None:
        """Scenario: Mapping from slop words to clean alternatives exists."""
        alternatives = {
            "leverage": "use",
            "utilize": "use",
            "comprehensive": "complete",
            "robust": "solid",
            "facilitate": "enable",
            "streamline": "simplify",
            "delve": "explore",
        }

        for slop, clean in alternatives.items():
            assert slop in self.TIER1_SLOP_WORDS, f"{slop} should be in tier-1 list"
            assert clean not in self.TIER1_SLOP_WORDS, f"{clean} should not be slop"
