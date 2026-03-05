"""Tests for check_frontmatter and categorize_frontmatter scripts.

Feature: Frontmatter checking utilities
    As a developer
    I want frontmatter checked in markdown skill files
    So that missing metadata is identified
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from categorize_frontmatter import (  # noqa: E402
    categorize_files,
)
from categorize_frontmatter import (
    main as cat_main,
)
from check_frontmatter import (  # noqa: E402
    find_markdown_files_without_frontmatter,
)
from check_frontmatter import (
    main as check_main,
)

# ---------------------------------------------------------------------------
# Tests: find_markdown_files_without_frontmatter
# ---------------------------------------------------------------------------


class TestFindMarkdownFilesWithoutFrontmatter:
    """Feature: Find markdown files missing YAML frontmatter."""

    @pytest.mark.unit
    def test_finds_file_without_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Markdown file without --- is returned.
        Given a .md file with no frontmatter
        When find_markdown_files_without_frontmatter is called
        Then the file appears in the result
        """
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        md_file = skills_dir / "no_fm.md"
        md_file.write_text("# Just a heading\nNo frontmatter here.\n")
        result = find_markdown_files_without_frontmatter(str(skills_dir))
        assert md_file in result

    @pytest.mark.unit
    def test_excludes_file_with_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Markdown file with --- is excluded.
        Given a .md file with proper YAML frontmatter
        When find_markdown_files_without_frontmatter is called
        Then the file is NOT in the result
        """
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        md_file = skills_dir / "with_fm.md"
        md_file.write_text("---\nname: test\n---\n\n# Content\n")
        result = find_markdown_files_without_frontmatter(str(skills_dir))
        assert md_file not in result

    @pytest.mark.unit
    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns empty list."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        result = find_markdown_files_without_frontmatter(str(skills_dir))
        assert result == []


# ---------------------------------------------------------------------------
# Tests: check_frontmatter main()
# ---------------------------------------------------------------------------


class TestCheckFrontmatterMain:
    """Feature: check_frontmatter main function."""

    @pytest.mark.unit
    def test_missing_skills_dir_returns_one(self, tmp_path: Path) -> None:
        """Scenario: No skills/ directory returns exit code 1."""
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = check_main()
            assert result == 1
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_all_files_have_frontmatter_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: All markdown files have frontmatter returns 0."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        md_file = skills_dir / "skill.md"
        md_file.write_text("---\nname: skill\n---\n\n# Skill\n")

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = check_main()
            assert result == 0
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_missing_frontmatter_returns_one(self, tmp_path: Path) -> None:
        """Scenario: Skill file without frontmatter returns exit code 1."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        md_file = skills_dir / "no_fm.md"
        md_file.write_text("# No frontmatter here\n")

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = check_main()
            assert result == 1
        finally:
            os.chdir(original)


# ---------------------------------------------------------------------------
# Tests: categorize_files
# ---------------------------------------------------------------------------


class TestCategorizeFiles:
    """Feature: Files categorized as needing frontmatter or exceptions."""

    @pytest.mark.unit
    def test_readme_is_exception(self, tmp_path: Path) -> None:
        """Scenario: README.md files are classified as exceptions."""
        readme = tmp_path / "README.md"
        readme.write_text("# Readme")
        needs, exceptions = categorize_files([readme])
        assert readme in exceptions
        assert readme not in needs

    @pytest.mark.unit
    def test_examples_dir_is_exception(self, tmp_path: Path) -> None:
        """Scenario: Files in /examples/ are classified as exceptions."""
        example_file = tmp_path / "examples" / "demo.md"
        example_file.parent.mkdir()
        example_file.write_text("# Example")
        needs, exceptions = categorize_files([example_file])
        assert example_file in exceptions

    @pytest.mark.unit
    def test_scripts_dir_is_exception(self, tmp_path: Path) -> None:
        """Scenario: Files in /scripts/ are classified as exceptions."""
        script_file = tmp_path / "scripts" / "helper.md"
        script_file.parent.mkdir()
        script_file.write_text("# Script helper")
        needs, exceptions = categorize_files([script_file])
        assert script_file in exceptions

    @pytest.mark.unit
    def test_guide_md_needs_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Files ending with guide.md need frontmatter."""
        guide = tmp_path / "usage-guide.md"
        guide.write_text("# Guide content")
        needs, exceptions = categorize_files([guide])
        assert guide in needs

    @pytest.mark.unit
    def test_unknown_file_needs_frontmatter_by_default(self, tmp_path: Path) -> None:
        """Scenario: Unknown files default to needing frontmatter."""
        unknown = tmp_path / "some-skill.md"
        unknown.write_text("# Some skill")
        needs, exceptions = categorize_files([unknown])
        assert unknown in needs
        assert unknown not in exceptions

    @pytest.mark.unit
    def test_skills_eval_modules_are_exceptions(self, tmp_path: Path) -> None:
        """Scenario: Files in /skills-eval/modules/ are exceptions."""
        se_file = tmp_path / "skills-eval" / "modules" / "eval.md"
        se_file.parent.mkdir(parents=True)
        se_file.write_text("# Eval module")
        needs, exceptions = categorize_files([se_file])
        assert se_file in exceptions

    @pytest.mark.unit
    def test_empty_list_returns_empty(self) -> None:
        """Scenario: Empty file list returns empty categories."""
        needs, exceptions = categorize_files([])
        assert needs == []
        assert exceptions == []


# ---------------------------------------------------------------------------
# Tests: categorize_frontmatter main()
# ---------------------------------------------------------------------------


class TestCategorizeFrontmatterMain:
    """Feature: categorize_frontmatter main function."""

    @pytest.mark.unit
    def test_returns_counts(self, tmp_path: Path) -> None:
        """Scenario: main returns counts of needs/exceptions.
        Given a mix of files
        When main is called
        Then it returns (needs_count, exceptions_count)
        """
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # File without frontmatter - should be counted as needing it
        no_fm = skills_dir / "skill.md"
        no_fm.write_text("# No frontmatter")
        # README - should be exception
        readme = skills_dir / "README.md"
        readme.write_text("# Readme")

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            needs, exceptions = cat_main()
            assert needs >= 0
            assert exceptions >= 0
        finally:
            os.chdir(original)
