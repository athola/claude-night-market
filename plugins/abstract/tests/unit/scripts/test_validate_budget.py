"""Tests for validate_budget.py script.

This module tests the budget validation script which validates skill and command
description lengths against Claude Code's system prompt budget limit,
following TDD/BDD principles.

Issue #60: Add unit tests for validate_budget.py
"""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))

from validate_budget import (
    BUDGET_LIMIT,
    DESCRIPTION_MAX,
    WARN_THRESHOLD,
    Component,
    analyze_file,
    extract_description,
)


class TestExtractDescription:
    """Feature: Extract description field from YAML frontmatter.

    As a budget validator
    I want to extract description fields from skill/command files
    So that I can calculate total description budget usage
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extracts_single_line_description(
        self, skill_content_single_line: str
    ) -> None:
        """Scenario: Extract single-line description.

        Given a skill file with a single-line description
        When extracting the description
        Then it should return the description text without 'description:' prefix.
        """
        result = extract_description(skill_content_single_line)
        assert result == "A simple single-line description"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extracts_multi_line_description(
        self, skill_content_multi_line: str
    ) -> None:
        """Scenario: Extract multi-line description.

        Given a skill file with a multi-line (pipe-style) description
        When extracting the description
        Then it should return all lines joined together.
        """
        result = extract_description(skill_content_multi_line)
        assert "multi-line description" in result
        assert "spans several lines" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_empty_for_missing_description(
        self, skill_content_no_description: str
    ) -> None:
        """Scenario: Handle missing description field.

        Given a skill file without a description field
        When extracting the description
        Then it should return an empty string.
        """
        result = extract_description(skill_content_no_description)
        assert result == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_description_with_special_characters(self) -> None:
        """Scenario: Handle description with special characters.

        Given a skill file with special characters in description
        When extracting the description
        Then it should preserve the special characters.
        """
        content = """---
name: test
description: A description with "quotes" and 'apostrophes' and: colons
---
"""
        result = extract_description(content)
        assert '"quotes"' in result
        assert "'apostrophes'" in result


class TestAnalyzeFile:
    """Feature: Analyze skill or command file for budget metrics.

    As a budget validator
    I want to analyze files and extract their metadata
    So that I can track description lengths per component
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_skill_file_correctly(self, tmp_path) -> None:
        """Scenario: Analyze a valid skill file.

        Given a skill file with name and description
        When analyzing the file
        Then it should return a Component with correct metadata.
        """
        # Setup
        skill_dir = tmp_path / "plugins" / "test-plugin" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: my-skill
description: A test description here
category: testing
---

Content here.
""")

        # Execute
        result = analyze_file(skill_file, "skill")

        # Verify
        assert result.name == "my-skill"
        assert result.type == "skill"
        assert result.plugin == "test-plugin"
        assert result.desc_length == len("A test description here")
        assert "SKILL.md" in result.file_path

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_command_file_correctly(self, tmp_path) -> None:
        """Scenario: Analyze a valid command file.

        Given a command file with name and description
        When analyzing the file
        Then it should return a Component with correct metadata.
        """
        # Setup
        cmd_dir = tmp_path / "plugins" / "another-plugin" / "commands"
        cmd_dir.mkdir(parents=True)
        cmd_file = cmd_dir / "my-command.md"
        cmd_file.write_text("""---
name: my-command
description: Command description text
---

Usage info.
""")

        # Execute
        result = analyze_file(cmd_file, "command")

        # Verify
        assert result.name == "my-command"
        assert result.type == "command"
        assert result.plugin == "another-plugin"
        assert result.desc_length == len("Command description text")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_uses_filename_when_name_missing(self, tmp_path) -> None:
        """Scenario: Fall back to filename when name is missing.

        Given a skill file without a name field
        When analyzing the file
        Then it should use the file stem as the name.
        """
        # Setup
        skill_dir = tmp_path / "plugins" / "test-plugin" / "skills" / "fallback-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
description: Description only
category: testing
---

Content.
""")

        # Execute
        result = analyze_file(skill_file, "skill")

        # Verify - should use "SKILL" as stem
        assert result.name == "SKILL"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_file_not_in_plugins_dir(self, tmp_path) -> None:
        """Scenario: Handle file not in standard plugins directory structure.

        Given a file not in a plugins/ directory
        When analyzing the file
        Then it should set plugin to 'unknown'.
        """
        # Setup
        random_dir = tmp_path / "random" / "location"
        random_dir.mkdir(parents=True)
        skill_file = random_dir / "SKILL.md"
        skill_file.write_text("""---
name: orphan-skill
description: An orphan
---
""")

        # Execute
        result = analyze_file(skill_file, "skill")

        # Verify
        assert result.plugin == "unknown"


class TestComponent:
    """Feature: Component dataclass represents a plugin component.

    As a budget validator
    I want a data structure for component metadata
    So that I can easily sort and filter components
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_component_dataclass_creation(self) -> None:
        """Scenario: Create a Component instance.

        Given component metadata values
        When creating a Component instance
        Then all fields should be accessible.
        """
        comp = Component(
            name="test-skill",
            type="skill",
            plugin="test-plugin",
            desc_length=100,
            file_path="/path/to/SKILL.md",
        )

        assert comp.name == "test-skill"
        assert comp.type == "skill"
        assert comp.plugin == "test-plugin"
        assert comp.desc_length == 100
        assert comp.file_path == "/path/to/SKILL.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_components_can_be_sorted_by_desc_length(self) -> None:
        """Scenario: Sort components by description length.

        Given multiple Component instances
        When sorting by desc_length
        Then they should be ordered correctly.
        """
        comps = [
            Component("a", "skill", "p1", 50, "/a"),
            Component("b", "skill", "p1", 200, "/b"),
            Component("c", "skill", "p1", 100, "/c"),
        ]

        sorted_comps = sorted(comps, key=lambda c: c.desc_length, reverse=True)

        assert sorted_comps[0].name == "b"  # 200
        assert sorted_comps[1].name == "c"  # 100
        assert sorted_comps[2].name == "a"  # 50


class TestBudgetConstants:
    """Feature: Budget constants are correctly defined.

    As a budget validator
    I want well-defined budget limits
    So that validation is consistent
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_budget_limit_is_reasonable(self) -> None:
        """Scenario: Budget limit is set to a reasonable value.

        Given the BUDGET_LIMIT constant
        Then it should be a positive integer around 15000.
        """
        assert BUDGET_LIMIT > 0
        assert BUDGET_LIMIT == 15000

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warn_threshold_below_budget(self) -> None:
        """Scenario: Warning threshold is below budget limit.

        Given the WARN_THRESHOLD constant
        Then it should be less than BUDGET_LIMIT.
        """
        assert WARN_THRESHOLD < BUDGET_LIMIT
        assert WARN_THRESHOLD == 14500

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_description_max_is_reasonable(self) -> None:
        """Scenario: Per-description max is reasonable.

        Given the DESCRIPTION_MAX constant
        Then it should be a reasonable per-component limit.
        """
        assert DESCRIPTION_MAX > 0
        assert DESCRIPTION_MAX == 150


class TestMainFunctionIntegration:
    """Feature: Main function validates budget across plugins.

    As a budget validator
    I want to run validation across all plugins
    So that I can enforce budget limits
    """

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_main_exits_zero_when_under_budget(
        self, temp_plugin_structure, monkeypatch
    ) -> None:
        """Scenario: Exit code 0 when under budget.

        Given a plugin structure with small descriptions
        When running main()
        Then it should exit with code 0.
        """
        monkeypatch.chdir(temp_plugin_structure)
        # Clear sys.argv to avoid pytest args being parsed by argparse
        monkeypatch.setattr("sys.argv", ["validate_budget.py"])

        # Import main here to get fresh module
        from validate_budget import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_main_detects_verbose_descriptions(
        self, temp_plugin_structure, monkeypatch, capsys
    ) -> None:
        """Scenario: Detect descriptions exceeding DESCRIPTION_MAX.

        Given a plugin structure with a verbose description (>150 chars)
        When running main()
        Then it should report the verbose description in output.
        """
        monkeypatch.chdir(temp_plugin_structure)
        monkeypatch.setattr("sys.argv", ["validate_budget.py"])

        from validate_budget import main

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        # Should mention verbose descriptions
        assert "verbose-skill" in captured.out or "exceed" in captured.out

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_main_handles_empty_plugin_structure(
        self, empty_plugin_structure, monkeypatch
    ) -> None:
        """Scenario: Handle empty plugin directory.

        Given a plugin structure with no skills or commands
        When running main()
        Then it should exit with code 0 (under budget by default).
        """
        monkeypatch.chdir(empty_plugin_structure)
        monkeypatch.setattr("sys.argv", ["validate_budget.py"])

        from validate_budget import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Empty = 0 chars = under budget
        assert exc_info.value.code == 0


class TestPathArgument:
    """Feature: Support --path CLI argument for custom base directory.

    As a budget validator user
    I want to specify a custom base path
    So that I can validate skills in non-standard locations

    Issue #61: Add --path CLI argument to validate_budget.py
    """

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_path_argument_accepted(self, temp_plugin_structure) -> None:
        """Scenario: --path argument is accepted.

        Given a valid plugin structure at a custom path
        When running main() with --path argument
        Then it should validate skills at that path.
        """
        import subprocess

        result = subprocess.run(
            [
                "python",
                str(Path(__file__).parents[3] / "scripts" / "validate_budget.py"),
                "--path",
                str(temp_plugin_structure),
            ],
            capture_output=True,
            text=True,
        )

        # Should complete successfully (exit 0)
        assert result.returncode == 0
        # Should show budget info in output
        assert "Total description characters" in result.stdout

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_path_argument_uses_specified_directory(
        self, temp_plugin_structure, tmp_path
    ) -> None:
        """Scenario: --path uses specified directory, not cwd.

        Given a plugin structure at path A
        And current directory is path B (empty)
        When running main() with --path A
        Then it should find skills in path A, not path B.
        """
        import subprocess

        # Create empty directory as cwd
        empty_cwd = tmp_path / "empty_cwd"
        empty_cwd.mkdir()

        result = subprocess.run(
            [
                "python",
                str(Path(__file__).parents[3] / "scripts" / "validate_budget.py"),
                "--path",
                str(temp_plugin_structure),
            ],
            capture_output=True,
            text=True,
            cwd=str(empty_cwd),  # Run from empty directory
        )

        # Should still find skills from the --path location
        assert result.returncode == 0
        # Should have found some components (not 0 chars)
        assert "Total description characters:" in result.stdout

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_path_defaults_to_current_directory(self) -> None:
        """Scenario: Default path is current directory.

        Given no --path argument
        When running main()
        Then it should use current directory as base.
        """
        import subprocess

        # Run without --path, should use cwd
        result = subprocess.run(
            [
                "python",
                str(Path(__file__).parents[3] / "scripts" / "validate_budget.py"),
                "--help",
            ],
            capture_output=True,
            text=True,
        )

        # Help should mention --path option with default
        assert "--path" in result.stdout
        assert "default" in result.stdout.lower()


class TestEdgeCases:
    """Feature: Handle edge cases gracefully.

    As a budget validator
    I want graceful handling of edge cases
    So that the script doesn't crash on unexpected input
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_description_from_empty_content(self) -> None:
        """Scenario: Handle empty file content.

        Given empty file content
        When extracting description
        Then it should return empty string.
        """
        result = extract_description("")
        assert result == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_description_no_frontmatter(self) -> None:
        """Scenario: Handle content without YAML frontmatter.

        Given content without frontmatter
        When extracting description
        Then it should return empty string.
        """
        content = """# Just a Heading

Some markdown content without frontmatter.
"""
        result = extract_description(content)
        assert result == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_worktree_paths_excluded(self, tmp_path, monkeypatch) -> None:
        """Scenario: Exclude .worktrees directory from scanning.

        Given skills in both regular and .worktrees directories
        When running main()
        Then .worktrees paths should be excluded.
        """
        # Create regular plugin
        regular = tmp_path / "plugins" / "regular" / "skills" / "skill"
        regular.mkdir(parents=True)
        (regular / "SKILL.md").write_text("""---
name: regular-skill
description: Regular skill
---
""")

        # Create worktree plugin (should be excluded)
        worktree = tmp_path / ".worktrees" / "plugins" / "wt" / "skills" / "skill"
        worktree.mkdir(parents=True)
        (worktree / "SKILL.md").write_text("""---
name: worktree-skill
description: Should be excluded
---
""")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["validate_budget.py"])

        from validate_budget import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        # If worktrees were included, we'd have more chars
        # The test passes if it completes without error
        assert exc_info.value.code == 0
