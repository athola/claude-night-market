"""Tests for the rules_validator module.

Feature: Rules Validation
    As a plugin developer
    I want to validate Claude Code rules in .claude/rules/ directories
    So that I can catch frontmatter errors, bad glob patterns, and quality issues
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest  # noqa: I001

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from rules_validator import (  # noqa: E402
    evaluate_rules_directory,
    validate_content_quality,
    validate_frontmatter,
    validate_glob_patterns,
    validate_organization,
)


class TestValidateFrontmatter:
    """Feature: Frontmatter validation for rule files

    As a rules author
    I want frontmatter validated for correctness
    So that my rules load properly in Claude Code
    """

    @pytest.mark.unit
    def test_valid_frontmatter_with_paths(self, tmp_path: Path) -> None:
        """Scenario: Rule file has valid frontmatter with paths
        Given a rule file with properly quoted glob paths
        When I validate the frontmatter
        Then it should report no errors
        """
        rule_file = tmp_path / "api-rules.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            description: API validation rules
            paths:
              - "src/api/**/*.ts"
              - "lib/api/**/*.ts"
            ---
            Use strict input validation for all API endpoints.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.unit
    def test_valid_frontmatter_without_paths(self, tmp_path: Path) -> None:
        """Scenario: Rule file has no paths (unconditional rule)
        Given a rule file with no paths field
        When I validate the frontmatter
        Then it should report no errors (unconditional is valid)
        """
        rule_file = tmp_path / "global-rules.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            description: Global coding standards
            ---
            Always use meaningful variable names.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.unit
    def test_no_frontmatter_is_valid(self, tmp_path: Path) -> None:
        """Scenario: Rule file has no frontmatter at all
        Given a rule file with no YAML frontmatter
        When I validate the frontmatter
        Then it should report valid (frontmatter is optional)
        """
        rule_file = tmp_path / "simple.md"
        rule_file.write_text("Just plain content with no frontmatter.\n")

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_cursor_specific_fields_flagged(self, tmp_path: Path) -> None:
        """Scenario: Rule file uses Cursor-specific fields
        Given a rule file with alwaysApply or globs fields
        When I validate the frontmatter
        Then it should report errors about Cursor-specific fields
        """
        rule_file = tmp_path / "cursor-style.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            globs:
              - "*.ts"
            alwaysApply: true
            ---
            Some content.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is False
        error_texts = " ".join(result["errors"])
        assert "globs" in error_texts
        assert "alwaysApply" in error_texts

    @pytest.mark.unit
    def test_paths_must_be_list(self, tmp_path: Path) -> None:
        """Scenario: paths field is a string instead of a list
        Given a rule file where paths is a scalar string
        When I validate the frontmatter
        Then it should report an error about paths type
        """
        rule_file = tmp_path / "bad-paths.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            paths: "**/*.ts"
            ---
            Content here.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is False
        assert any("list" in e.lower() for e in result["errors"])

    @pytest.mark.unit
    def test_frontmatter_closing_at_eof(self, tmp_path: Path) -> None:
        """Scenario: Frontmatter closing delimiter at end of file
        Given a rule file where --- closes at EOF with no trailing newline
        When I validate the frontmatter
        Then it should parse successfully
        """
        rule_file = tmp_path / "eof-close.md"
        rule_file.write_text("---\ndescription: test\n---")

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.unit
    def test_empty_yaml_body_parses_as_empty_dict(self, tmp_path: Path) -> None:
        """Scenario: Frontmatter with empty YAML body
        Given a rule file with --- delimiters but no YAML content
        When I validate the frontmatter
        Then it should treat it as valid with empty frontmatter
        """
        rule_file = tmp_path / "empty-yaml.md"
        rule_file.write_text("---\n---\nSome body content.\n")

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert result["score"] == 25

    @pytest.mark.unit
    def test_non_dict_yaml_reports_error(self, tmp_path: Path) -> None:
        """Scenario: Frontmatter YAML is a list instead of a mapping
        Given a rule file where YAML parses to a list
        When I validate the frontmatter
        Then it should report a mapping error
        """
        rule_file = tmp_path / "list-yaml.md"
        rule_file.write_text("---\n- item1\n- item2\n---\nBody.\n")

        result = validate_frontmatter(rule_file)
        assert result["valid"] is False
        assert any("mapping" in e.lower() for e in result["errors"])

    @pytest.mark.unit
    def test_unknown_fields_produce_warnings(self, tmp_path: Path) -> None:
        """Scenario: Frontmatter contains unrecognized fields
        Given a rule file with fields not in VALID_FIELDS or CURSOR_FIELDS
        When I validate the frontmatter
        Then it should produce warnings about unknown fields
        And the score should be reduced
        """
        rule_file = tmp_path / "unknown-fields.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            description: Valid field
            author: Some Person
            priority: high
            ---
            Content here.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert any("author" in w for w in result["warnings"])
        assert any("priority" in w for w in result["warnings"])
        assert result["score"] < 25

    @pytest.mark.unit
    def test_unclosed_frontmatter_treated_as_no_frontmatter(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Frontmatter opening delimiter but no closing delimiter
        Given a rule file that starts with --- but never closes it
        When I validate the frontmatter
        Then it should treat it as no frontmatter (valid)
        """
        rule_file = tmp_path / "unclosed.md"
        rule_file.write_text("---\ndescription: test\nNo closing delimiter here")

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert result["score"] == 25

    @pytest.mark.unit
    def test_empty_paths_list_warns(self, tmp_path: Path) -> None:
        """Scenario: paths field is an empty list
        Given a rule file where paths is [] (empty list)
        When I validate the frontmatter
        Then it should warn about removing the empty paths field
        """
        rule_file = tmp_path / "empty-paths.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            paths: []
            ---
            Content here.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is True
        assert any("empty" in w.lower() for w in result["warnings"])

    @pytest.mark.unit
    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Scenario: Rule file has invalid YAML in frontmatter
        Given a rule file with malformed YAML
        When I validate the frontmatter
        Then it should report a YAML parse error
        """
        rule_file = tmp_path / "bad-yaml.md"
        rule_file.write_text(
            textwrap.dedent("""\
            ---
            paths:
              - **/*.ts
              bad indent
            ---
            Content.
            """)
        )

        result = validate_frontmatter(rule_file)
        assert result["valid"] is False
        assert len(result["errors"]) > 0


class TestValidateGlobPatterns:
    """Feature: Glob pattern validation

    As a rules author
    I want glob patterns checked for correctness
    So that rules apply to the intended files
    """

    @pytest.mark.unit
    def test_good_patterns_pass(self) -> None:
        """Scenario: Well-formed glob patterns
        Given a list of properly formed glob patterns
        When I validate them
        Then all should pass validation
        """
        patterns = ["src/api/**/*.ts", "tests/**/*.test.ts", "{src,lib}/**/*.ts"]
        result = validate_glob_patterns(patterns)
        assert result["valid"] is True
        assert result["warnings"] == []

    @pytest.mark.unit
    def test_overly_broad_pattern_warns(self) -> None:
        """Scenario: Overly broad glob pattern
        Given a pattern that matches everything
        When I validate it
        Then it should produce a warning about breadth
        """
        result = validate_glob_patterns(["**/*"])
        assert len(result["warnings"]) > 0
        assert any("broad" in w.lower() for w in result["warnings"])

    @pytest.mark.unit
    def test_empty_pattern_list(self) -> None:
        """Scenario: Empty pattern list
        Given an empty list of patterns
        When I validate it
        Then it should pass (no patterns to validate)
        """
        result = validate_glob_patterns([])
        assert result["valid"] is True


class TestValidateOrganization:
    """Feature: Rules directory organization validation

    As a rules author
    I want directory organization checked
    So that my rules follow naming conventions
    """

    @pytest.mark.unit
    def test_good_organization(self, tmp_path: Path) -> None:
        """Scenario: Well-organized rules directory
        Given a rules directory with descriptive kebab-case filenames
        When I validate the organization
        Then it should report no issues
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api-validation.md").write_text("---\n---\nContent")
        (rules_dir / "testing-standards.md").write_text("---\n---\nContent")

        result = validate_organization(rules_dir)
        assert result["score"] > 0

    @pytest.mark.unit
    def test_non_descriptive_names_flagged(self, tmp_path: Path) -> None:
        """Scenario: Rules with generic filenames
        Given a rules directory with non-descriptive names like rules1.md
        When I validate the organization
        Then it should flag naming issues
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rules1.md").write_text("Content")
        (rules_dir / "misc.md").write_text("Content")

        result = validate_organization(rules_dir)
        assert len(result["warnings"]) > 0

    @pytest.mark.unit
    def test_spaces_in_filename_flagged(self, tmp_path: Path) -> None:
        """Scenario: Rule file with spaces in name
        Given a rule file named with spaces
        When I validate the organization
        Then it should flag the naming issue
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "my rules.md").write_text("Content")

        result = validate_organization(rules_dir)
        assert len(result["warnings"]) > 0

    @pytest.mark.unit
    def test_uppercase_filename_flagged(self, tmp_path: Path) -> None:
        """Scenario: Rule file with uppercase letters in name
        Given a rule file not in kebab-case (contains uppercase or underscores)
        When I validate the organization
        Then it should warn about kebab-case convention
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "ApiRules.md").write_text("Content here for validation.")

        result = validate_organization(rules_dir)
        assert any("kebab-case" in w.lower() for w in result["warnings"])

    @pytest.mark.unit
    def test_broken_symlink_flagged(self, tmp_path: Path) -> None:
        """Scenario: Rules directory contains a broken symlink
        Given a rules directory with a symlink pointing to a missing target
        When I validate the organization
        Then it should report an error about the broken symlink
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        broken_link = rules_dir / "broken-link.md"
        broken_link.symlink_to(tmp_path / "nonexistent-target.md")

        result = validate_organization(rules_dir)
        assert any("symlink" in e.lower() for e in result["errors"])

    @pytest.mark.unit
    def test_nonexistent_directory_errors(self, tmp_path: Path) -> None:
        """Scenario: Validate organization of a nonexistent directory
        Given a path that does not exist
        When I validate the organization
        Then it should report an error and score 0
        """
        result = validate_organization(tmp_path / "nonexistent")
        assert result["score"] == 0
        assert len(result["errors"]) > 0

    @pytest.mark.unit
    def test_empty_directory_warns(self, tmp_path: Path) -> None:
        """Scenario: Validate organization of an empty directory
        Given a rules directory with no .md files
        When I validate the organization
        Then it should warn about no rule files found
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        result = validate_organization(rules_dir)
        assert result["score"] == 0
        assert any("no rule files" in w.lower() for w in result["warnings"])

    @pytest.mark.unit
    def test_empty_glob_pattern_in_list_flagged(self) -> None:
        """Scenario: Glob pattern list contains a whitespace-only entry
        Given a patterns list with an empty/whitespace string
        When I validate the patterns
        Then it should report an error about empty pattern
        """
        result = validate_glob_patterns(["src/**/*.ts", "  ", "lib/**/*.ts"])
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])


class TestValidateContentQuality:
    """Feature: Content quality assessment

    As a rules author
    I want content quality checked
    So that rules are actionable and concise
    """

    @pytest.mark.unit
    def test_concise_actionable_content(self) -> None:
        """Scenario: Good quality rule content
        Given concise actionable rule content
        When I assess content quality
        Then it should score well
        """
        content = (
            "Use strict TypeScript. Enable noImplicitAny. "
            "Prefer interfaces over type aliases."
        )
        result = validate_content_quality(content)
        assert result["score"] > 0
        assert result["token_count"] < 500

    @pytest.mark.unit
    def test_empty_content_flagged(self) -> None:
        """Scenario: Empty rule content
        Given a rule file with no content after frontmatter
        When I assess content quality
        Then it should flag the lack of content
        """
        result = validate_content_quality("")
        assert result["score"] == 0
        assert len(result["warnings"]) > 0

    @pytest.mark.unit
    def test_short_content_warned(self) -> None:
        """Scenario: Very short rule content
        Given rule content with fewer than 10 words
        When I assess content quality
        Then it should warn about insufficient detail
        """
        content = "Use TypeScript."
        result = validate_content_quality(content)
        assert any("short" in w.lower() for w in result["warnings"])
        assert result["score"] < 25

    @pytest.mark.unit
    def test_verbose_content_warned(self) -> None:
        """Scenario: Overly verbose rule content
        Given rule content exceeding 500 tokens
        When I assess content quality
        Then it should warn about verbosity
        """
        # Create content with many words to exceed 500 tokens
        content = "This is a verbose rule. " * 200
        result = validate_content_quality(content)
        assert any(
            "verbose" in w.lower() or "token" in w.lower() for w in result["warnings"]
        )


class TestEvaluateRulesDirectory:
    """Feature: Full rules directory evaluation

    As a plugin developer
    I want a comprehensive evaluation of a rules directory
    So that I get an overall quality score and actionable feedback
    """

    @pytest.mark.unit
    def test_full_evaluation_returns_score(self, tmp_path: Path) -> None:
        """Scenario: Evaluate a well-formed rules directory
        Given a rules directory with valid rule files
        When I run a full evaluation
        Then it should return a score out of 100
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api-validation.md").write_text(
            textwrap.dedent("""\
            ---
            description: API validation rules
            paths:
              - "src/api/**/*.ts"
            ---
            Use strict input validation for all API endpoints.
            Validate request bodies against schemas.
            """)
        )

        result = evaluate_rules_directory(rules_dir)
        assert "total_score" in result
        assert 0 <= result["total_score"] <= 100
        assert "files_evaluated" in result
        assert result["files_evaluated"] == 1

    @pytest.mark.unit
    def test_empty_directory_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Evaluate an empty rules directory
        Given an empty rules directory
        When I run a full evaluation
        Then it should return score 0 with a warning
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        result = evaluate_rules_directory(rules_dir)
        assert result["total_score"] == 0
        assert result["files_evaluated"] == 0

    @pytest.mark.unit
    def test_file_without_paths_gets_full_glob_score(self, tmp_path: Path) -> None:
        """Scenario: Rule file with no paths field in evaluate_rules_directory
        Given a rule file with no paths frontmatter
        When running a full evaluation
        Then the glob pattern score should be full (20 points)
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general-rules.md").write_text(
            textwrap.dedent("""\
            ---
            description: General coding rules
            ---
            Use meaningful variable names and follow coding standards.
            Always write clear documentation for public APIs.
            """)
        )

        result = evaluate_rules_directory(rules_dir)
        assert result["total_score"] > 0
        assert result["files_evaluated"] == 1

    @pytest.mark.unit
    def test_token_efficiency_tiers(self, tmp_path: Path) -> None:
        """Scenario: Token efficiency scoring across different content sizes
        Given rule files with different content lengths
        When running a full evaluation
        Then token efficiency should scale with content size
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        # Create a file with content between 500-1000 tokens (~385-770 words)
        medium_content = "Follow this important coding standard carefully. " * 100
        (rules_dir / "medium-rules.md").write_text(
            f"---\ndescription: Medium rules\n---\n{medium_content}\n"
        )

        result = evaluate_rules_directory(rules_dir)
        assert result["total_score"] > 0
        assert result["files_evaluated"] == 1

    @pytest.mark.unit
    def test_high_token_count_reduces_score(self, tmp_path: Path) -> None:
        """Scenario: Very verbose rule file reduces token efficiency score
        Given a rule file exceeding 1000 estimated tokens
        When running a full evaluation
        Then it should score lower due to token inefficiency
        """
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        # Create content exceeding 1000 tokens (~770+ words)
        verbose_content = "This is an extremely verbose and detailed rule. " * 200
        (rules_dir / "verbose-rules.md").write_text(
            f"---\ndescription: Verbose rules\n---\n{verbose_content}\n"
        )

        result_verbose = evaluate_rules_directory(rules_dir)

        # Compare with a concise version
        concise_dir = tmp_path / ".claude2" / "rules"
        concise_dir.mkdir(parents=True)
        (concise_dir / "concise-rules.md").write_text(
            textwrap.dedent("""\
            ---
            description: Concise rules
            ---
            Use strict TypeScript. Enable noImplicitAny.
            Prefer interfaces over type aliases. Keep functions short.
            """)
        )

        result_concise = evaluate_rules_directory(concise_dir)
        assert result_concise["total_score"] > result_verbose["total_score"]

    @pytest.mark.unit
    def test_nonexistent_directory_errors(self, tmp_path: Path) -> None:
        """Scenario: Evaluate a nonexistent rules directory
        Given a path that does not exist
        When I run a full evaluation
        Then it should return an error
        """
        result = evaluate_rules_directory(tmp_path / "nonexistent")
        assert result["total_score"] == 0
        assert len(result["errors"]) > 0
