"""Tests for the categorize_frontmatter script.

Feature: Frontmatter categorisation for skill files
    As a developer
    I want files sorted into those needing frontmatter vs exceptions
    So that I know which files to fix vs exclude
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from categorize_frontmatter import categorize_files  # noqa: E402


class TestCategorizeFiles:
    """Feature: File categorisation into needs-frontmatter vs exceptions

    As a developer
    I want files categorised correctly
    So that I can focus only on files that genuinely need frontmatter
    """

    @pytest.mark.unit
    def test_readme_files_are_exceptions(self, tmp_path: Path) -> None:
        """Scenario: README files are exceptions, not needing frontmatter
        Given a list containing a README.md path
        When categorise_files is called
        Then the README lands in should_be_exceptions
        """
        readme = tmp_path / "plugins" / "myplugin" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.touch()

        needs, exceptions = categorize_files([readme])
        assert readme in exceptions
        assert readme not in needs

    @pytest.mark.unit
    def test_example_files_are_exceptions(self, tmp_path: Path) -> None:
        """Scenario: Files in /examples/ directories are exceptions
        Given a path inside an /examples/ directory
        When categorise_files is called
        Then it lands in should_be_exceptions
        """
        example_file = tmp_path / "plugins" / "myplugin" / "examples" / "demo.md"
        example_file.parent.mkdir(parents=True)
        example_file.touch()

        needs, exceptions = categorize_files([example_file])
        assert example_file in exceptions
        assert example_file not in needs

    @pytest.mark.unit
    def test_scripts_directory_files_are_exceptions(self, tmp_path: Path) -> None:
        """Scenario: Files under /scripts/ are exceptions
        Given a path inside a /scripts/ directory
        When categorise_files is called
        Then it lands in should_be_exceptions
        """
        script_doc = tmp_path / "plugins" / "myplugin" / "scripts" / "notes.md"
        script_doc.parent.mkdir(parents=True)
        script_doc.touch()

        needs, exceptions = categorize_files([script_doc])
        assert script_doc in exceptions
        assert script_doc not in needs

    @pytest.mark.unit
    def test_core_skill_module_needs_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Core skill modules need frontmatter
        Given a path containing /modules/ and a core module name
        When categorise_files is called
        Then it lands in needs_frontmatter
        """
        module_file = (
            tmp_path
            / "plugins"
            / "myplugin"
            / "skills"
            / "my-skill"
            / "modules"
            / "core-workflow.md"
        )
        module_file.parent.mkdir(parents=True)
        module_file.touch()

        needs, exceptions = categorize_files([module_file])
        assert module_file in needs
        assert module_file not in exceptions

    @pytest.mark.unit
    def test_guide_files_need_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Guide files need frontmatter
        Given a path ending with 'guide.md'
        When categorise_files is called
        Then it lands in needs_frontmatter
        """
        guide = tmp_path / "plugins" / "myplugin" / "skills" / "usage-guide.md"
        guide.parent.mkdir(parents=True)
        guide.touch()

        needs, exceptions = categorize_files([guide])
        assert guide in needs
        assert guide not in exceptions

    @pytest.mark.unit
    def test_arbitrary_skill_file_needs_frontmatter_by_default(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Unclassified skill content defaults to needing frontmatter
        Given a path that does not match any exception pattern
        When categorise_files is called
        Then it lands in needs_frontmatter
        """
        skill_file = (
            tmp_path / "plugins" / "myplugin" / "skills" / "my-skill" / "SKILL.md"
        )
        skill_file.parent.mkdir(parents=True)
        skill_file.touch()

        needs, exceptions = categorize_files([skill_file])
        assert skill_file in needs
        assert skill_file not in exceptions

    @pytest.mark.unit
    def test_empty_list_returns_two_empty_lists(self) -> None:
        """Scenario: Empty input returns empty output lists
        Given an empty list of files
        When categorise_files is called
        Then both output lists are empty
        """
        needs, exceptions = categorize_files([])
        assert needs == []
        assert exceptions == []

    @pytest.mark.unit
    def test_mixed_list_split_correctly(self, tmp_path: Path) -> None:
        """Scenario: Mixed list is split across both categories
        Given a list with one README and one plain skill file
        When categorise_files is called
        Then each file lands in the correct category
        """
        readme = tmp_path / "plugins" / "p" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.touch()

        skill_doc = tmp_path / "plugins" / "p" / "skills" / "s" / "SKILL.md"
        skill_doc.parent.mkdir(parents=True)
        skill_doc.touch()

        needs, exceptions = categorize_files([readme, skill_doc])
        assert readme in exceptions
        assert skill_doc in needs

    @pytest.mark.unit
    def test_skills_eval_modules_are_exceptions(self, tmp_path: Path) -> None:
        """Scenario: Files under /skills-eval/modules/ are exceptions
        Given a path inside /skills-eval/modules/
        When categorise_files is called
        Then it lands in should_be_exceptions
        """
        eval_doc = (
            tmp_path / "plugins" / "myplugin" / "skills-eval" / "modules" / "notes.md"
        )
        eval_doc.parent.mkdir(parents=True)
        eval_doc.touch()

        needs, exceptions = categorize_files([eval_doc])
        assert eval_doc in exceptions
        assert eval_doc not in needs
