"""Tests for code comment quality guidelines module.

This module validates the comment guidelines for sanctum pr-review
following TDD/BDD patterns.

Issue #66: Code comment quality guidelines for sanctum:code-review
"""

import re
from pathlib import Path

import pytest


class TestCommentGuidelinesStructure:
    """Feature: Comment guidelines module structure.

    As a plugin developer
    I want the module to have proper structure
    So that it integrates with pr-review skill
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Return the module file path."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "pr-review"
            / "modules"
            / "comment-guidelines.md"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_file_exists(self, module_path: Path) -> None:
        """Scenario: Module file exists.

        Given the pr-review skill
        When checking for comment-guidelines module
        Then the file should exist.
        """
        assert module_path.exists(), f"Module not found at {module_path}"


class TestCommentGuidelinesContent:
    """Feature: Comment guidelines content.

    As a developer
    I want guidance on code comments
    So that comments add value without bloat
    """

    @pytest.fixture
    def module_content(self) -> str:
        """Return the module file content."""
        module_path = (
            Path(__file__).parents[3]
            / "skills"
            / "pr-review"
            / "modules"
            / "comment-guidelines.md"
        )
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_why_not_what(self, module_content: str) -> None:
        """Scenario: Module emphasizes 'why' over 'what'.

        Given the module content
        When checking for comment philosophy
        Then 'why not what' should be documented.
        """
        assert re.search(r"why", module_content, re.IGNORECASE), (
            "'Why' guidance not found"
        )
        assert re.search(r"what", module_content, re.IGNORECASE), (
            "'What' contrast not found"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_good_comment_examples(self, module_content: str) -> None:
        """Scenario: Module has good comment examples.

        Given the module content
        When checking for examples
        Then good comment examples should be present.
        """
        good_indicators = ["good", "example", "recommended"]
        has_good_examples = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in good_indicators
        )
        assert has_good_examples, "Good comment examples not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_bad_comment_examples(self, module_content: str) -> None:
        """Scenario: Module has bad comment examples.

        Given the module content
        When checking for anti-patterns
        Then bad comment examples should be marked.
        """
        bad_indicators = ["bad", "avoid", "don't", "anti-pattern"]
        has_bad_examples = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in bad_indicators
        )
        assert has_bad_examples, "Bad comment anti-patterns not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_over_commenting(self, module_content: str) -> None:
        """Scenario: Module addresses over-commenting.

        Given the module content
        When checking for over-commenting guidance
        Then warning about excessive comments should exist.
        """
        over_indicators = ["over-comment", "too many", "excessive", "bloat"]
        has_over_guidance = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in over_indicators
        )
        assert has_over_guidance, "Over-commenting guidance not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_stale_comments(self, module_content: str) -> None:
        """Scenario: Module addresses stale comments.

        Given the module content
        When checking for staleness guidance
        Then warning about outdated comments should exist.
        """
        stale_indicators = ["stale", "outdated", "out of date", "sync"]
        has_stale_guidance = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in stale_indicators
        )
        assert has_stale_guidance, "Stale comment guidance not found"


class TestCommentGuidelinesThresholds:
    """Feature: Comment thresholds and criteria.

    As a reviewer
    I want clear thresholds for when comments are needed
    So that I can apply consistent standards
    """

    @pytest.fixture
    def module_content(self) -> str:
        """Return the module file content."""
        module_path = (
            Path(__file__).parents[3]
            / "skills"
            / "pr-review"
            / "modules"
            / "comment-guidelines.md"
        )
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_when_to_comment(self, module_content: str) -> None:
        """Scenario: Module defines when comments are warranted.

        Given the module content
        When checking for criteria
        Then clear triggers for comments should be defined.
        """
        when_indicators = ["when to", "warrant", "require", "need"]
        has_when = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in when_indicators
        )
        assert has_when, "When-to-comment criteria not defined"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_docstrings(self, module_content: str) -> None:
        """Scenario: Module covers docstring conventions.

        Given the module content
        When checking for docstring guidance
        Then docstring conventions should be addressed.
        """
        assert re.search(r"docstring", module_content, re.IGNORECASE), (
            "Docstring guidance not found"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_complex_logic(self, module_content: str) -> None:
        """Scenario: Module addresses comments for complex logic.

        Given the module content
        When checking for complexity guidance
        Then complex algorithm documentation should be mentioned.
        """
        complex_indicators = ["complex", "algorithm", "non-obvious", "tricky"]
        has_complex = any(
            re.search(indicator, module_content, re.IGNORECASE)
            for indicator in complex_indicators
        )
        assert has_complex, "Complex logic comment guidance not found"
