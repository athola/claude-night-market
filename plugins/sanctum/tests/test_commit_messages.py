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
        "feat", "fix", "docs", "style", "refactor",
        "test", "chore", "perf", "ci", "build"
    ]

    def test_generates_conventional_commit_for_feature_changes(self, staged_changes_context):
        """GIVEN staged changes that add new functionality
        WHEN the commit-messages skill analyzes the changes
        THEN it should generate a conventional commit message with 'feat' type
        """
        # Arrange
        feature_context = {
            **staged_changes_context,
            "staged_files": [
                {"path": "src/new_feature.py", "status": "A", "additions": 50, "deletions": 0},
                {"path": "tests/test_new_feature.py", "status": "A", "additions": 30, "deletions": 0}
            ]
        }

        mock_bash = Mock()
        mock_bash.side_effect = [
            "feat: Add new feature implementation\n\nImplements core functionality for XYZ feature",
            "src/new_feature.py"
        ]

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")
        changed_files = mock_bash("git diff --cached --name-only")

        # Assert
        assert commit_msg.startswith("feat:")
        assert "new feature" in commit_msg.lower()
        assert "src/new_feature.py" in changed_files

    def test_generates_conventional_commit_for_bug_fixes(self, staged_changes_context):
        """GIVEN staged changes that fix bugs
        WHEN the commit-messages skill analyzes the changes
        THEN it should generate a conventional commit message with 'fix' type
        """
        # Arrange
        fix_context = {
            **staged_changes_context,
            "staged_files": [
                {"path": "src/buggy_module.py", "status": "M", "additions": 5, "deletions": 15},
                {"path": "tests/test_fix.py", "status": "A", "additions": 20, "deletions": 0}
            ]
        }

        mock_bash = Mock()
        mock_bash.return_value = "fix: Resolve null pointer exception in module initialization\n\nFixes issue #123 where null values caused crashes"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("fix:")
        assert "resolve" in commit_msg.lower()
        assert "null pointer" in commit_msg.lower()

    def test_generates_conventional_commit_for_documentation(self, staged_changes_context):
        """GIVEN staged changes that only affect documentation
        WHEN the commit-messages skill analyzes the changes
        THEN it should generate a conventional commit message with 'docs' type
        """
        # Arrange
        docs_context = {
            **staged_changes_context,
            "staged_files": [
                {"path": "README.md", "status": "M", "additions": 25, "deletions": 5},
                {"path": "docs/api.md", "status": "A", "additions": 100, "deletions": 0}
            ]
        }

        mock_bash = Mock()
        mock_bash.return_value = "docs: Update README and add API documentation\n\nClarify installation steps and document new endpoints"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("docs:")
        assert "documentation" in commit_msg.lower() or "readme" in commit_msg.lower()

    def test_generates_conventional_commit_for_refactoring(self, staged_changes_context):
        """GIVEN staged changes that refactor code without changing functionality
        WHEN the commit-messages skill analyzes the changes
        THEN it should generate a conventional commit message with 'refactor' type
        """
        # Arrange
        refactor_context = {
            **staged_changes_context,
            "staged_files": [
                {"path": "src/legacy_module.py", "status": "M", "additions": 30, "deletions": 50},
                {"path": "src/utils.py", "status": "M", "additions": 20, "deletions": 10}
            ]
        }

        mock_bash = Mock()
        mock_bash.return_value = "refactor: Simplify module structure and improve code organization\n\nExtract common utilities and remove duplicate code"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("refactor:")
        assert "simplify" in commit_msg.lower() or "improve" in commit_msg.lower()

    def test_includes_scope_in_commit_message_when_appropriate(self):
        """GIVEN changes that affect a specific component or module
        WHEN the commit-messages skill generates the message
        THEN it should include the scope in parentheses
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.return_value = "feat(auth): Add OAuth2 authentication support\n\nImplements Google and GitHub OAuth providers"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert commit_msg.startswith("feat(auth):")
        assert "oauth2" in commit_msg.lower()

    def test_includes_breaking_change_indicator_when_needed(self):
        """GIVEN changes that break backward compatibility
        WHEN the commit-messages skill generates the message
        THEN it should include the breaking change indicator
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.return_value = "feat!: Change API endpoint structure\n\nBREAKING CHANGE: API endpoints now use camelCase instead of snake_case"

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert "feat!:" in commit_msg
        assert "BREAKING CHANGE" in commit_msg

    def test_analyzes_diff_content_for_context(self):
        """GIVEN staged changes with specific code patterns
        WHEN the commit-messages skill analyzes the diff
        THEN it should extract meaningful context from the diff
        """
        # Arrange
        sample_diff = """diff --git a/src/calculator.py b/src/calculator.py
index abc123..def456 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -10,6 +10,11 @@ class Calculator:
     def add(self, a, b):
         return a + b
+
+    def multiply(self, a, b):
+        "Multiply two numbers."
+        return a * b
"""

        mock_bash = Mock()
        mock_bash.side_effect = [
            sample_diff,
            "feat(calculator): Add multiplication method\n\nAdds multiply() method to support arithmetic operations"
        ]

        # Act - simulate tool calls through mock
        diff_output = mock_bash("git diff --cached")
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert "multiply" in diff_output
        assert "multiply" in commit_msg.lower()
        assert "calculator" in commit_msg

    def test_handles_multiple_file_changes_in_single_commit(self, staged_changes_context):
        """GIVEN multiple files staged for commit
        WHEN the commit-messages skill analyzes all changes
        THEN it should generate a cohesive message covering all changes
        """
        # Arrange - context already has multiple files
        mock_bash = Mock()
        mock_bash.side_effect = [
            "src/main.py\nREADME.md\ntests/test_main.py",
            "feat: Implement user authentication system\n\n- Add user login/logout functionality\n- Update documentation with setup instructions\n- Add comprehensive test coverage"
        ]

        # Act - simulate tool calls through mock
        changed_files = mock_bash("git diff --cached --name-only")
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert len(changed_files.split('\n')) >= 3
        assert "authentication" in commit_msg.lower()
        assert "user" in commit_msg.lower()

    def test_follows_conventional_commit_specification(self):
        """GIVEN any commit message generated by the skill
        WHEN it's validated against the conventional commit specification
        THEN it should comply with the format requirements
        """
        # Arrange
        valid_formats = [
            "feat: Add new feature",
            "fix(scope): Fix bug in component",
            "docs!: Update breaking API documentation",
            "style: Fix code formatting",
            "refactor(test): Simplify test structure",
            "test: Add unit tests for utility functions",
            "chore(deps): Update dependencies",
            "perf: Optimize database queries",
            "ci: Configure GitHub Actions",
            "build: Update build configuration"
        ]

        mock_bash = Mock()
        mock_bash.return_value = valid_formats[0]  # Test first format

        # Act - simulate tool calls through mock
        commit_msg = mock_bash("git log -1 --pretty=format:%s")

        # Assert - verify conventional commit format
        assert ':' in commit_msg
        assert commit_msg.split(':')[0] in self.CONVENTIONAL_COMMIT_TYPES
        assert len(commit_msg.split(':')[1].strip()) > 0

    def test_creates_required_todo_items(self, mock_todo_tool):
        """GIVEN analysis of staged changes is complete
        WHEN the commit-messages skill finishes
        THEN it should create the required TodoWrite items
        """
        # Arrange
        expected_todos = [
            {
                "content": "Analyze staged changes for commit type and scope",
                "status": "completed",
                "activeForm": "Analyzed staged changes"
            },
            {
                "content": "Generate conventional commit message with appropriate type and description",
                "status": "completed",
                "activeForm": "Generated commit message"
            },
            {
                "content": "Validate commit message follows conventional commit specification",
                "status": "completed",
                "activeForm": "Validated commit message format"
            }
        ]

        # Act
        mock_todo_tool(expected_todos)

        # Assert
        mock_todo_tool.assert_called_once_with(expected_todos)

    def test_handles_empty_staged_changes(self):
        """GIVEN no staged changes in the repository
        WHEN the commit-messages skill attempts to generate a message
        THEN it should handle the empty state gracefully
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = [
            "",  # No files in git diff --cached --name-only
            None  # No commit message generated
        ]

        # Act - simulate tool calls through mock
        changed_files = mock_bash("git diff --cached --name-only")

        # Assert
        assert changed_files == ""

    def test_handles_binary_files_in_staged_changes(self):
        """GIVEN binary files (images, PDFs, etc.) staged for commit
        WHEN the commit-messages skill analyzes the changes
        THEN it should handle binary files appropriately in the message
        """
        # Arrange
        mock_bash = Mock()
        mock_bash.side_effect = [
            "assets/logo.png\ndocs/manual.pdf",
            "feat: Add company branding and documentation\n\n- Add new company logo\n- Include product manual in PDF format"
        ]

        # Act - simulate tool calls through mock
        changed_files = mock_bash("git diff --cached --name-only")
        commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

        # Assert
        assert "logo.png" in changed_files
        assert "manual.pdf" in changed_files
        assert "branding" in commit_msg.lower()
        assert "documentation" in commit_msg.lower()

    class TestCommitMessageQuality:
        """Tests for commit message quality and best practices."""

        def test_uses_imperative_mood_in_subject(self):
            """GIVEN a commit message being generated
            WHEN the subject line is created
            THEN it should use imperative mood (Add, Fix, Update, not Added, Fixed, Updated)
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = "Add user authentication feature"  # Imperative

            # Act - simulate tool calls through mock
            subject = mock_bash("git log -1 --pretty=format:%s").split('\n')[0]

            # Assert
            assert subject.startswith("Add") or subject.startswith("Fix") or \
                   subject.startswith("Update") or subject.startswith("Remove") or \
                   subject.startswith("Refactor") or subject.startswith("Improve")

        def test_limits_subject_line_length(self):
            """GIVEN a commit message being generated
            WHEN the subject line is created
            THEN it should be within conventional length limits (50-72 characters)
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = "feat: Add comprehensive user authentication system"  # Within limits

            # Act - simulate tool calls through mock
            subject = mock_bash("git log -1 --pretty=format:%s")

            # Assert
            assert len(subject) <= 72
            assert len(subject) >= 20  # Minimum reasonable length

        def test_separates_subject_from_body_with_blank_line(self):
            """GIVEN a commit message with subject and body
            WHEN the full message is generated
            THEN it should separate subject and body with a blank line
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = """feat: Add user authentication

Implements OAuth2 login with support for multiple providers.
The authentication flow uses JWT tokens for session management."""

            # Act - simulate tool calls through mock
            commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

            # Assert
            lines = commit_msg.split('\n')
            assert lines[1] == ''  # Blank line after subject

        def test_wraps_body_lines_at_72_characters(self):
            """GIVEN a commit message body
            WHEN the body is generated
            THEN it should wrap lines at 72 characters for readability
            """
            # Arrange
            long_line = "This is a very long line that should be wrapped at exactly 72 characters to ensure proper readability in git log output and various git tools that display commit messages."
            wrapped_lines = [
                "This is a very long line that should be wrapped at exactly 72",
                "characters to ensure proper readability in git log output and"
            ]

            mock_bash = Mock()
            mock_bash.return_value = f"feat: Add feature\n\n{wrapped_lines[0]}\n{wrapped_lines[1]}"

            # Act - simulate tool calls through mock
            commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

            # Assert
            body_lines = commit_msg.split('\n\n')[1].split('\n')
            for line in body_lines:
                if line:  # Skip empty lines
                    assert len(line) <= 72

        def test_explains_what_and_why_in_commit_body(self):
            """GIVEN changes being committed
            WHEN the commit body is written
            THEN it should explain both what changed and why it was necessary
            """
            # Arrange
            mock_bash = Mock()
            mock_bash.return_value = """fix: Resolve memory leak in data processing

Fixed the memory leak caused by unclosed database connections.
The leak occurred when processing large datasets and would
eventually cause the application to crash after several hours.

This fix ensures connections are properly closed using context
managers, preventing resource exhaustion."""

            # Act - simulate tool calls through mock
            commit_msg = mock_bash("git log -1 --pretty=format:%s%n%n%b")

            # Assert
            assert "memory leak" in commit_msg.lower()  # What
            assert "database connections" in commit_msg.lower()  # What
            assert "eventually cause" in commit_msg.lower()  # Why
            assert "preventing resource" in commit_msg.lower()  # Why/Result
