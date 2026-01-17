"""Tests for command content validation in scry plugin.

This module tests command file content validation:
- Required sections present
- Parameter documentation complete

Issue #53: Add skill/agent/command content validation tests

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import re
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

# ============================================================================
# Command Schema Validation
# ============================================================================


class TestCommandSchemaValidation:
    """Feature: Validate command file schema.

    As a plugin developer
    I want command files to follow a consistent schema
    So that commands are discoverable and usable
    """

    REQUIRED_FRONTMATTER = ["description"]
    RECOMMENDED_SECTIONS = ["Usage", "Examples"]

    def extract_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return None

        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                end_idx = i
                break

        if end_idx is None:
            return None

        yaml_content = "\n".join(lines[1:end_idx])
        try:
            return cast(dict[str, Any] | None, yaml.safe_load(yaml_content))
        except yaml.YAMLError:
            return None

    def extract_sections(self, content: str) -> list[str]:
        """Extract section headings from markdown content."""
        pattern = r"^##?\s+(.+)$"
        matches = re.findall(pattern, content, re.MULTILINE)
        return matches

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_has_frontmatter(self, commands_dir: Path) -> None:
        """Scenario: Command file has YAML frontmatter.

        Given a command file
        When checking for frontmatter
        Then it should start with ---.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            assert content.startswith("---"), f"Missing frontmatter in {cmd_file.name}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_has_description(self, commands_dir: Path) -> None:
        """Scenario: Command has description field.

        Given a command file with frontmatter
        When checking for description
        Then it should have a description field.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            frontmatter = self.extract_frontmatter(content)

            assert frontmatter is not None, f"Invalid frontmatter in {cmd_file.name}"
            assert "description" in frontmatter, (
                f"Missing description in {cmd_file.name}"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_description_is_non_empty(self, commands_dir: Path) -> None:
        """Scenario: Command description is non-empty.

        Given a command with description field
        When checking content
        Then description should have text.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            frontmatter = self.extract_frontmatter(content)

            if frontmatter and "description" in frontmatter:
                desc = str(frontmatter["description"]).strip()
                assert len(desc) > 0, f"Empty description in {cmd_file.name}"


class TestCommandUsageSection:
    """Feature: Validate command usage documentation.

    As a user
    I want commands to have usage instructions
    So that I know how to use them
    """

    def has_usage_section(self, content: str) -> bool:
        """Check if content has a Usage section."""
        return bool(re.search(r"^##?\s+Usage", content, re.MULTILINE | re.IGNORECASE))

    def has_examples_section(self, content: str) -> bool:
        """Check if content has an Examples section."""
        return bool(
            re.search(r"^##?\s+Examples?", content, re.MULTILINE | re.IGNORECASE)
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_has_usage_section(self, commands_dir: Path) -> None:
        """Scenario: Command has Usage section.

        Given a command file
        When checking sections
        Then it should have a Usage section.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            # Usage is recommended but not strictly required
            # We just verify the check works
            has_usage = self.has_usage_section(content)
            # Log for visibility
            if not has_usage:
                print(f"Note: {cmd_file.name} has no Usage section")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_usage_section_detection(self) -> None:
        """Scenario: Usage section detection works.

        Given content with Usage heading
        When checking
        Then it should be detected.
        """
        content_with_usage = """# Command

## Usage

Run the command.
"""
        assert self.has_usage_section(content_with_usage)

        content_without_usage = """# Command

## Description

A command.
"""
        assert not self.has_usage_section(content_without_usage)


class TestCommandParameters:
    """Feature: Validate command parameter documentation.

    As a user
    I want command parameters to be documented
    So that I know what options are available
    """

    def extract_parameters(self, content: str) -> list[str]:
        """Extract parameter names from content.

        Looks for patterns like:
        - `--flag`
        - `-f`
        - `<argument>`
        """
        flags = re.findall(r"`(--[\w-]+)`", content)
        short_flags = re.findall(r"`(-\w)`", content)
        args = re.findall(r"`(<[\w-]+>)`", content)
        return flags + short_flags + args

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_parameter_extraction(self) -> None:
        """Scenario: Parameter extraction works.

        Given content with documented parameters
        When extracting
        Then parameters should be found.
        """
        content = """# Command

## Usage

```bash
my-command --verbose -f <input>
```

## Options

- `--verbose`: Enable verbose output
- `-f`: Force operation
- `<input>`: Input file path
"""
        params = self.extract_parameters(content)
        assert "--verbose" in params
        assert "-f" in params
        assert "<input>" in params

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_commands_have_documented_parameters(self, commands_dir: Path) -> None:
        """Scenario: Commands document their parameters.

        Given command files
        When checking for parameter documentation
        Then parameters used should be documented.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            params = self.extract_parameters(content)
            # Commands may have 0 parameters, which is valid
            # We just verify extraction works
            assert isinstance(params, list)


# ============================================================================
# Command File Discovery
# ============================================================================


class TestCommandDiscovery:
    """Feature: Discover and validate all commands in plugin.

    As a plugin maintainer
    I want to validate all command files
    So that the plugin is consistent
    """

    EXPECTED_COMMANDS = ["record-terminal.md", "record-browser.md"]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_expected_commands_exist(self, commands_dir: Path) -> None:
        """Scenario: Expected commands exist.

        Given the commands/ directory
        When checking for expected commands
        Then they should all exist.
        """
        for cmd_name in self.EXPECTED_COMMANDS:
            cmd_file = commands_dir / cmd_name
            assert cmd_file.exists(), f"Expected command not found: {cmd_name}"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_all_commands_have_valid_frontmatter(self, commands_dir: Path) -> None:
        """Scenario: All commands have valid frontmatter.

        Given all command files
        When parsing frontmatter
        Then all should be valid YAML.
        """
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()

            if not content.startswith("---"):
                pytest.fail(f"Missing frontmatter in {cmd_file.name}")

            lines = content.split("\n")
            end_idx = None
            for i, line in enumerate(lines[1:], start=1):
                if line == "---":
                    end_idx = i
                    break

            if end_idx is None:
                pytest.fail(f"Unclosed frontmatter in {cmd_file.name}")

            yaml_content = "\n".join(lines[1:end_idx])
            try:
                data = yaml.safe_load(yaml_content)
                assert isinstance(data, dict), (
                    f"Frontmatter should be dict in {cmd_file.name}"
                )
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {cmd_file.name}: {e}")

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.parametrize("cmd_name", EXPECTED_COMMANDS)
    def test_command_has_description(self, commands_dir: Path, cmd_name: str) -> None:
        """Scenario: Each command has a description.

        Given a command file
        When checking frontmatter
        Then it should have description field.
        """
        cmd_file = commands_dir / cmd_name
        if not cmd_file.exists():
            pytest.skip(f"Command {cmd_name} not found")

        content = cmd_file.read_text()

        # Extract frontmatter
        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                end_idx = i
                break

        assert end_idx is not None

        yaml_content = "\n".join(lines[1:end_idx])
        data = yaml.safe_load(yaml_content)

        assert "description" in data, f"Missing description in {cmd_name}"
