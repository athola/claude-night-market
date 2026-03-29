"""Tests for minister /update-labels command structure and validation.

This test suite follows TDD/BDD principles:
- Behavior-focused test names using `test_should_X_when_Y` pattern
- Given-When-Then structure in each test
- Tests command file structure, frontmatter, and integration
"""

import json
from pathlib import Path

import pytest


class TestUpdateLabelsCommand:
    """Test /update-labels command structure and content."""

    @pytest.fixture
    def command_file_path(self) -> Path:
        """Path to the update-labels command file."""
        return Path(__file__).parents[2] / "commands" / "update-labels.md"

    @pytest.fixture
    def command_content(self, command_file_path: Path) -> str:
        """Content of the update-labels command file."""
        return command_file_path.read_text()

    @pytest.fixture
    def plugin_json_path(self) -> Path:
        """Path to the plugin.json file."""
        return Path(__file__).parents[2] / ".claude-plugin" / "plugin.json"

    @pytest.fixture
    def plugin_json(self, plugin_json_path: Path) -> dict:
        """Parsed plugin.json content."""
        return json.loads(plugin_json_path.read_text())

    class TestCommandFileExists:
        """Test command file existence and basic structure."""

        def test_should_exist_when_command_file_path_resolved(
            self,
            command_file_path: Path,
        ) -> None:
            """Test that the command file exists.

            Given: The expected path to update-labels.md
            When: Checking if the file exists
            Then: The file should exist
            """
            # Given/When/Then
            assert command_file_path.exists(), (
                f"Command file should exist at {command_file_path}"
            )

        def test_should_be_markdown_when_checking_extension(
            self,
            command_file_path: Path,
        ) -> None:
            """Test that the command file has correct extension.

            Given: The command file path
            When: Checking the file extension
            Then: Should be .md
            """
            # Given/When/Then
            assert command_file_path.suffix == ".md", (
                "Command file should have .md extension"
            )

    class TestFrontmatter:
        """Test command file frontmatter structure."""

        def test_should_have_frontmatter_when_parsing_content(
            self,
            command_content: str,
        ) -> None:
            """Test that the command has valid frontmatter.

            Given: The command file content
            When: Checking for frontmatter delimiters
            Then: Should have opening and closing --- markers
            """
            # Given/When
            lines = command_content.split("\n")
            has_opening = lines[0].strip() == "---"
            closing_index = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    closing_index = i
                    break

            # Then
            assert has_opening, "Command should start with ---"
            assert closing_index > 0, "Command should have closing ---"

        def test_should_have_name_field_when_parsing_frontmatter(
            self,
            command_content: str,
        ) -> None:
            """Test that frontmatter contains name field.

            Given: The command file content
            When: Parsing frontmatter for name field
            Then: Should contain name: update-labels
            """
            # Given/When
            has_name = "name: update-labels" in command_content

            # Then
            assert has_name, "Frontmatter should contain name: update-labels"

        def test_should_have_description_field_when_parsing_frontmatter(
            self,
            command_content: str,
        ) -> None:
            """Test that frontmatter contains description field.

            Given: The command file content
            When: Parsing frontmatter for description field
            Then: Should contain description field
            """
            # Given/When
            has_description = "description:" in command_content

            # Then
            assert has_description, "Frontmatter should contain description field"

        def test_should_have_usage_field_when_parsing_frontmatter(
            self,
            command_content: str,
        ) -> None:
            """Test that frontmatter contains usage field.

            Given: The command file content
            When: Parsing frontmatter for usage field
            Then: Should contain usage field with /update-labels
            """
            # Given/When
            has_usage = (
                "usage:" in command_content and "/update-labels" in command_content
            )

            # Then
            assert has_usage, (
                "Frontmatter should contain usage field with /update-labels"
            )

    class TestLabelTaxonomy:
        """Test that command documents the correct label taxonomy."""

        @pytest.fixture
        def type_labels(self) -> list[str]:
            """Expected type labels."""
            return [
                "feature",
                "bugfix",
                "test",
                "docs",
                "refactor",
                "performance",
                "ci-cd",
                "research",
            ]

        @pytest.fixture
        def priority_labels(self) -> list[str]:
            """Expected priority labels."""
            return ["high-priority", "medium-priority", "low-priority"]

        @pytest.fixture
        def effort_labels(self) -> list[str]:
            """Expected effort labels."""
            return ["small-effort", "medium-effort", "large-effort"]

        def test_should_document_all_type_labels_when_checking_content(
            self,
            command_content: str,
            type_labels: list[str],
        ) -> None:
            """Test that all type labels are documented.

            Given: The command file content and expected type labels
            When: Checking for each type label
            Then: All type labels should be mentioned
            """
            # Given/When
            missing_labels = [
                label for label in type_labels if label not in command_content
            ]

            # Then
            assert len(missing_labels) == 0, (
                f"Command should document all type labels. Missing: {missing_labels}"
            )

        def test_should_document_all_priority_labels_when_checking_content(
            self,
            command_content: str,
            priority_labels: list[str],
        ) -> None:
            """Test that all priority labels are documented.

            Given: The command file content and expected priority labels
            When: Checking for each priority label
            Then: All priority labels should be mentioned
            """
            # Given/When
            missing_labels = [
                label for label in priority_labels if label not in command_content
            ]

            # Then
            assert len(missing_labels) == 0, (
                f"Command should document all priority labels. Missing: {missing_labels}"
            )

        def test_should_document_all_effort_labels_when_checking_content(
            self,
            command_content: str,
            effort_labels: list[str],
        ) -> None:
            """Test that all effort labels are documented.

            Given: The command file content and expected effort labels
            When: Checking for each effort label
            Then: All effort labels should be mentioned
            """
            # Given/When
            missing_labels = [
                label for label in effort_labels if label not in command_content
            ]

            # Then
            assert len(missing_labels) == 0, (
                f"Command should document all effort labels. Missing: {missing_labels}"
            )

    class TestCommandArguments:
        """Test that command documents its arguments."""

        @pytest.mark.parametrize(
            "argument",
            [
                "--repo",
                "--dry-run",
                "--preserve",
            ],
        )
        def test_should_document_argument_when_checking_content(
            self,
            command_content: str,
            argument: str,
        ) -> None:
            """Test that command arguments are documented.

            Given: The command file content and an expected argument
            When: Checking if the argument is documented
            Then: The argument should be present in the content
            """
            # Given/When/Then
            assert argument in command_content, (
                f"Command should document {argument} argument"
            )

    class TestWorkflowPhases:
        """Test that command documents workflow phases."""

        @pytest.mark.parametrize(
            "phase",
            [
                "Phase 1",
                "Phase 2",
                "Phase 3",
                "Phase 4",
                "Phase 5",
                "Phase 6",
            ],
        )
        def test_should_document_workflow_phase_when_checking_content(
            self,
            command_content: str,
            phase: str,
        ) -> None:
            """Test that workflow phases are documented.

            Given: The command file content and an expected phase
            When: Checking if the phase is documented
            Then: The phase should be present in the content
            """
            # Given/When/Then
            assert phase in command_content, f"Command should document {phase}"

    class TestPluginJsonIntegration:
        """Test that command is properly registered in plugin.json."""

        def test_should_be_listed_in_commands_when_checking_plugin_json(
            self,
            plugin_json: dict,
        ) -> None:
            """Test that command is registered in plugin.json.

            Given: The plugin.json content
            When: Checking the commands array
            Then: Should include update-labels.md
            """
            # Given/When
            commands = plugin_json.get("commands", [])
            has_command = any("update-labels.md" in cmd for cmd in commands)

            # Then
            assert has_command, "plugin.json should list update-labels.md in commands"

        def test_should_have_valid_path_when_checking_plugin_json(
            self,
            plugin_json: dict,
            command_file_path: Path,
        ) -> None:
            """Test that plugin.json path resolves correctly.

            Given: The plugin.json commands and actual file path
            When: Resolving the relative path from plugin.json
            Then: Should point to existing file
            """
            # Given
            commands = plugin_json.get("commands", [])
            update_labels_entry = next(
                (cmd for cmd in commands if "update-labels.md" in cmd), None
            )

            # When/Then
            assert update_labels_entry is not None, "Should find update-labels.md entry"
            # The path in plugin.json is relative to plugin root (parent of .claude-plugin/)
            plugin_root = command_file_path.parents[1]  # plugins/minister/
            resolved_path = (plugin_root / update_labels_entry).resolve()
            assert resolved_path.exists(), f"Resolved path {resolved_path} should exist"

    class TestExamplesSection:
        """Test that command has proper examples."""

        def test_should_have_examples_section_when_checking_content(
            self,
            command_content: str,
        ) -> None:
            """Test that command has examples section.

            Given: The command file content
            When: Checking for Examples section
            Then: Should have ## Examples or ### Example heading
            """
            # Given/When
            has_examples = (
                "## Example" in command_content or "### Example" in command_content
            )

            # Then
            assert has_examples, "Command should have examples section"

        def test_should_have_dry_run_example_when_checking_content(
            self,
            command_content: str,
        ) -> None:
            """Test that command has dry-run example.

            Given: The command file content
            When: Checking for dry-run example
            Then: Should demonstrate --dry-run usage
            """
            # Given/When
            has_dry_run_example = (
                "--dry-run" in command_content and "DRY RUN" in command_content
            )

            # Then
            assert has_dry_run_example, "Command should have dry-run example"

    class TestErrorHandling:
        """Test that command documents error handling."""

        def test_should_have_error_handling_section_when_checking_content(
            self,
            command_content: str,
        ) -> None:
            """Test that command documents error scenarios.

            Given: The command file content
            When: Checking for error handling documentation
            Then: Should have error handling section
            """
            # Given/When
            has_error_section = "Error" in command_content and (
                "Permission" in command_content or "Rate Limit" in command_content
            )

            # Then
            assert has_error_section, "Command should document error handling scenarios"

    class TestBestPractices:
        """Test that command documents best practices."""

        def test_should_have_best_practices_when_checking_content(
            self,
            command_content: str,
        ) -> None:
            """Test that command has best practices section.

            Given: The command file content
            When: Checking for best practices
            Then: Should have DO and DON'T guidelines
            """
            # Given/When
            has_do = "### DO:" in command_content or "DO:" in command_content
            has_dont = "### DON'T:" in command_content or "DON'T:" in command_content

            # Then
            assert has_do, "Command should have DO best practices"
            assert has_dont, "Command should have DON'T anti-patterns"
