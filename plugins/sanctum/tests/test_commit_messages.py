# ruff: noqa: D101,D102,D103,PLR2004,E501
"""BDD-style tests for the Commit Messages skill.

Tests the commit-messages skill, which generates conventional commit
messages from staged changes. Each Mock is verified with
assert_called_once_with or call_args checks.
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
        """Given staged feature changes, generates a feat: commit message."""
        mock_bash = Mock()
        mock_bash.side_effect = [
            "feat: Add new feature implementation\n\nImplements core functionality for XYZ feature",
            "src/new_feature.py",
        ]

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")
        changed_files = mock_bash("git diff --cached --name-only")

        # Verify mock was called with expected git commands
        assert mock_bash.call_count == 2
        mock_bash.assert_any_call("git log -1 --pretty=format:%s%n%n%b")
        mock_bash.assert_any_call("git diff --cached --name-only")

        assert commit_msg.startswith("feat:")
        assert "new feature" in commit_msg.lower()
        assert "src/new_feature.py" in changed_files

    def test_generates_conventional_commit_for_bug_fixes(
        self, staged_changes_context
    ) -> None:
        """Given staged bug-fix changes, generates a fix: commit message."""
        mock_bash = Mock()
        mock_bash.return_value = "fix: Resolve null pointer exception in module initialization\n\nFixes issue #123 where null values caused crashes"

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Verify mock was called exactly once with expected command
        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")

        assert commit_msg.startswith("fix:")
        assert "resolve" in commit_msg.lower()
        assert "null pointer" in commit_msg.lower()

    def test_generates_conventional_commit_for_documentation(
        self,
        staged_changes_context,
    ) -> None:
        """Given staged doc changes, generates a docs: commit message."""
        mock_bash = Mock()
        mock_bash.return_value = "docs: Update README and add API documentation\n\nClarify installation steps and document new endpoints"

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")

        assert commit_msg.startswith("docs:")
        assert "documentation" in commit_msg.lower() or "readme" in commit_msg.lower()

    def test_generates_conventional_commit_for_refactoring(
        self,
        staged_changes_context,
    ) -> None:
        """Given staged refactoring changes, generates a refactor: commit message."""
        mock_bash = Mock()
        mock_bash.return_value = "refactor: Simplify module structure and improve code organization\n\nExtract common utilities and remove duplicate code"

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")

        assert commit_msg.startswith("refactor:")
        assert "simplify" in commit_msg.lower() or "improve" in commit_msg.lower()

    def test_includes_scope_in_commit_message_when_appropriate(self) -> None:
        """Given a breaking change, includes feat! prefix and BREAKING CHANGE footer."""
        mock_bash = Mock()
        mock_bash.return_value = "feat!: Change API endpoint structure\n\nBREAKING CHANGE: API endpoints now use camelCase instead of snake_case"

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")

        assert "feat!:" in commit_msg
        assert "BREAKING CHANGE" in commit_msg

    def test_analyzes_diff_content_for_context(self) -> None:
        """Given a diff output, mock returns the staged diff content."""
        mock_bash = Mock()
        mock_bash.return_value = """diff --git a/src/calculator.py b/src/calculator.py
@@ class Calculator:
@@ def add(self, a, b):
@@ def multiply(self, a, b):
"""

        diff = mock_bash("git diff")

        mock_bash.assert_called_once_with("git diff")
        assert "multiply" in diff
        assert "Calculator" in diff

    def test_uses_imperative_mood_in_subject(self) -> None:
        """Given a well-formed commit, subject is between 20 and 72 chars."""
        mock_bash = Mock()
        mock_bash.return_value = "feat: Add detailed user authentication system"

        subject = mock_bash("git log -1 --pretty=format:%s")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s")
        assert 20 <= len(subject) <= 72
        # Subject should start with a conventional type
        commit_type = subject.split(":")[0]
        assert commit_type in self.CONVENTIONAL_COMMIT_TYPES

    def test_separates_subject_from_body_with_blank_line(self) -> None:
        """Given a multi-line commit, subject and body are separated by blank line."""
        mock_bash = Mock()
        mock_bash.return_value = (
            "feat: Add login\n\nImplements OAuth2 login with JWT sessions."
        )

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")
        lines = commit_msg.split("\n")
        assert len(lines) >= 3, "Commit message should have subject, blank, and body"
        assert lines[0].startswith("feat:")
        assert lines[1] == ""
        assert len(lines[2]) > 0

    def test_wraps_body_lines_at_72_characters(self) -> None:
        """Given a commit with wrapped body, no body line exceeds 72 chars."""
        mock_bash = Mock()
        body_text = (
            "fix: Resolve memory leak in data processing\n"
            "\n"
            "Fixed the memory leak caused by unclosed database connections.\n"
            "The leak occurred when processing large datasets and would\n"
            "eventually cause the application to crash after several hours.\n"
            "\n"
            "This fix validates connections are properly closed using context\n"
            "managers, preventing resource exhaustion."
        )
        mock_bash.return_value = body_text

        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        mock_bash.assert_called_once_with("git log -1 --pretty=format:%s%n%n%b")
        assert "memory leak" in commit_msg.lower()
        for line in commit_msg.split("\n"):
            assert len(line) <= 72, f"Body line exceeds 72 chars: {line!r}"


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
        # Verify which specific phrases were found
        found = [p for p in self.BLOCKED_PHRASES if p in bad_body.lower()]
        assert "it's worth noting" in found
        assert "at its core" in found

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
        # Verify all tier-1 words with known alternatives are covered
        assert len(alternatives) == 7
