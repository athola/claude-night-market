"""Tests for safe_replacer.py - dependency reference updater.

Tests follow BDD patterns with Given/When/Then structure.
"""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from safe_replacer import (
    SafeDependencyUpdater,
    main,
    output_error,
    output_result,
)


class TestSafeDependencyUpdater:
    """Feature: Safe dependency reference updates in skill files.

    As a plugin maintainer
    I want to safely update dependency references
    So that old references are migrated without creating duplicates
    """

    @pytest.fixture
    def updater(self) -> SafeDependencyUpdater:
        """Create a fresh updater instance."""
        return SafeDependencyUpdater()

    @pytest.fixture
    def skill_dir(self, tmp_path: Path) -> Path:
        """Create a temporary skill directory structure."""
        skill_path = tmp_path / "skills" / "test-skill"
        skill_path.mkdir(parents=True)
        return skill_path

    @pytest.mark.unit
    def test_updater_initialization(self, updater: SafeDependencyUpdater) -> None:
        """Scenario: Updater initializes with correct patterns.

        Given a new SafeDependencyUpdater
        When initialized
        Then it should have patterns for standalone and wrong prefix references.
        """
        assert "standalone_git_review" in updater.patterns
        assert "standalone_review_core" in updater.patterns
        assert "wrong_workspace_prefix" in updater.patterns
        assert "wrong_workflow_prefix" in updater.patterns
        assert "old_skill_paths" in updater.patterns

        assert (
            updater.replacements["standalone_git_review"]
            == "sanctum:git-workspace-review"
        )
        assert updater.replacements["standalone_review_core"] == "imbue:review-core"

    @pytest.mark.unit
    def test_update_file_nonexistent(
        self, updater: SafeDependencyUpdater, tmp_path: Path
    ) -> None:
        """Scenario: Update file that doesn't exist.

        Given a path to a non-existent file
        When update_file is called
        Then it should return False with 0 changes.
        """
        result = updater.update_file(tmp_path / "nonexistent.md")
        assert result == (False, 0)

    @pytest.mark.unit
    def test_update_file_no_changes_needed(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: File with no problematic references.

        Given a skill file with correct references
        When update_file is called
        Then it should return False with 0 changes.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "# Test Skill\n\nUses sanctum:git-workspace-review correctly."
        )

        result = updater.update_file(skill_file)
        assert result == (False, 0)

    @pytest.mark.unit
    def test_update_file_standalone_reference(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: File with standalone reference needing prefix.

        Given a skill file with standalone git-workspace-review reference
        When update_file is called
        Then it should add the sanctum: prefix.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "# Test Skill\n\nUses git-workspace-review for workspace."
        )

        updated, changes = updater.update_file(skill_file)

        assert updated is True
        assert changes >= 1
        content = skill_file.read_text()
        assert "sanctum:git-workspace-review" in content

    @pytest.mark.unit
    def test_update_file_wrong_prefix(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: File with wrong plugin prefix.

        Given a skill file with workspace-utils:git-workspace-review
        When update_file is called
        Then it should replace with sanctum:git-workspace-review.

        Note: The current implementation replaces the full pattern
        workspace-utils:git-workspace-review -> sanctum:git-workspace-review
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Uses workspace-utils:git-workspace-review here.")

        updated, changes = updater.update_file(skill_file)

        assert updated is True
        assert changes >= 1
        content = skill_file.read_text()
        # The replacement should produce the correct reference
        assert "sanctum:git-workspace-review" in content

    @pytest.mark.unit
    def test_update_file_review_core_reference(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: File with review-core reference.

        Given a skill file with standalone review-core reference
        When update_file is called
        Then it should add the imbue: prefix.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill\n\nInvoke review-core for reviews.")

        updated, changes = updater.update_file(skill_file)

        assert updated is True
        content = skill_file.read_text()
        assert "imbue:review-core" in content

    @pytest.mark.unit
    def test_validate_references_clean(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: Validate file with no issues.

        Given a skill file with correct references
        When validate_references is called
        Then it should return an empty list.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Clean Skill\n\nNo problematic references here.")

        issues = updater.validate_references(skill_file)
        assert issues == []

    @pytest.mark.unit
    def test_validate_references_old_prefixes(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: Validate file with old plugin prefixes.

        Given a skill file with workspace-utils: references
        When validate_references is called
        Then it should report the issue.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Uses workspace-utils:something and workflow-utils:other")

        issues = updater.validate_references(skill_file)

        assert len(issues) == 2
        assert any("workspace-utils:" in issue for issue in issues)
        assert any("workflow-utils:" in issue for issue in issues)

    @pytest.mark.unit
    def test_validate_references_old_paths(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: Validate file with old skill paths.

        Given a skill file with ~/.claude/skills/ references
        When validate_references is called
        Then it should report the issue.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Load from ~/.claude/skills/old-skill")

        issues = updater.validate_references(skill_file)

        assert len(issues) == 1
        assert "old skill paths" in issues[0].lower()

    @pytest.mark.unit
    def test_validate_references_duplicates(
        self, updater: SafeDependencyUpdater, skill_dir: Path
    ) -> None:
        """Scenario: Validate file with duplicate prefixes.

        Given a skill file with sanctum:sanctum: prefix
        When validate_references is called
        Then it should report the duplicate issue.
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Uses sanctum:sanctum:git-workspace-review")

        issues = updater.validate_references(skill_file)

        assert len(issues) == 1
        assert "duplicate sanctum:" in issues[0].lower()

    @pytest.mark.unit
    def test_update_directory(
        self, updater: SafeDependencyUpdater, tmp_path: Path
    ) -> None:
        """Scenario: Update all skill files in directory.

        Given a directory with multiple skill files
        When update_directory is called
        Then it should update all files with issues.
        """
        # Create multiple skill files
        skill1 = tmp_path / "skill1" / "SKILL.md"
        skill1.parent.mkdir(parents=True)
        skill1.write_text("Uses git-workspace-review standalone.")

        skill2 = tmp_path / "skill2" / "SKILL.md"
        skill2.parent.mkdir(parents=True)
        skill2.write_text("Uses review-core for reviews.")

        skill3 = tmp_path / "skill3" / "SKILL.md"
        skill3.parent.mkdir(parents=True)
        skill3.write_text("# Clean skill\nNo changes needed.")

        files_updated, total_changes = updater.update_directory(tmp_path)

        assert files_updated == 2
        assert total_changes >= 2


class TestOutputFunctions:
    """Feature: Output formatting for CLI results."""

    @pytest.mark.unit
    def test_output_result_text_format(self, capsys) -> None:
        """Scenario: Output result in text format.

        Given a result dict and args without output_json
        When output_result is called
        Then it should print human-readable text.
        """
        result = {"files_updated": 5, "total_changes": 10, "issues_found": []}
        args = argparse.Namespace(output_json=False)

        output_result(result, args)

        captured = capsys.readouterr()
        assert "Files updated: 5" in captured.out
        assert "Total changes: 10" in captured.out

    @pytest.mark.unit
    def test_output_result_json_format(self, capsys) -> None:
        """Scenario: Output result in JSON format.

        Given a result dict and args with output_json=True
        When output_result is called
        Then it should print valid JSON.
        """
        result = {"files_updated": 3, "total_changes": 7}
        args = argparse.Namespace(output_json=True)

        output_result(result, args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["data"]["files_updated"] == 3

    @pytest.mark.unit
    def test_output_result_with_issues(self, capsys) -> None:
        """Scenario: Output result with issues in text format.

        Given a result with issues_found
        When output_result is called
        Then it should list the issues.
        """
        result = {
            "files_updated": 1,
            "total_changes": 1,
            "issues_found": [{"file": "test.md", "issue": "Found old reference"}],
        }
        args = argparse.Namespace(output_json=False)

        output_result(result, args)

        captured = capsys.readouterr()
        assert "Issues found:" in captured.out

    @pytest.mark.unit
    def test_output_error_text_format(self, capsys) -> None:
        """Scenario: Output error in text format.

        Given an error message and args without output_json
        When output_error is called
        Then it should print to stderr.
        """
        args = argparse.Namespace(output_json=False)

        output_error("Something went wrong", args)

        captured = capsys.readouterr()
        assert "Error: Something went wrong" in captured.err

    @pytest.mark.unit
    def test_output_error_json_format(self, capsys) -> None:
        """Scenario: Output error in JSON format.

        Given an error message and args with output_json=True
        When output_error is called
        Then it should print valid JSON with success=False.
        """
        args = argparse.Namespace(output_json=True)

        output_error("Something went wrong", args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is False
        assert "Something went wrong" in data["error"]


class TestMainCLI:
    """Feature: CLI interface for safe_replacer."""

    @pytest.fixture
    def skill_tree(self, tmp_path: Path) -> Path:
        """Create a skill tree for testing."""
        skill = tmp_path / "skills" / "test" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("Uses git-workspace-review here.")
        return tmp_path

    @pytest.mark.integration
    def test_main_update_mode(self, skill_tree: Path, capsys) -> None:
        """Scenario: Run main in update mode.

        Given a directory with skill files needing updates
        When main is called with --path
        Then it should update the files and report results.
        """
        with patch.object(sys, "argv", ["safe_replacer", "--path", str(skill_tree)]):
            main()

        captured = capsys.readouterr()
        assert "Files updated:" in captured.out

    @pytest.mark.integration
    def test_main_validate_only(self, skill_tree: Path, capsys) -> None:
        """Scenario: Run main in validate-only mode.

        Given a directory with skill files
        When main is called with --validate-only
        Then it should report issues without making changes.
        """
        original_content = (skill_tree / "skills" / "test" / "SKILL.md").read_text()

        with patch.object(
            sys, "argv", ["safe_replacer", "--path", str(skill_tree), "--validate-only"]
        ):
            main()

        # File should be unchanged
        new_content = (skill_tree / "skills" / "test" / "SKILL.md").read_text()
        assert new_content == original_content

        captured = capsys.readouterr()
        assert (
            "Files updated:" in captured.out or "files_scanned" in captured.out.lower()
        )

    @pytest.mark.integration
    def test_main_json_output(self, skill_tree: Path, capsys) -> None:
        """Scenario: Run main with JSON output.

        Given a directory with skill files
        When main is called with --output-json
        Then it should output valid JSON.
        """
        with patch.object(
            sys, "argv", ["safe_replacer", "--path", str(skill_tree), "--output-json"]
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "success" in data
        assert data["success"] is True

    @pytest.mark.integration
    def test_main_nonexistent_path(self, tmp_path: Path, capsys) -> None:
        """Scenario: Run main with non-existent path.

        Given a path that doesn't exist
        When main is called
        Then it should output an error.
        """
        fake_path = tmp_path / "nonexistent"
        with patch.object(sys, "argv", ["safe_replacer", "--path", str(fake_path)]):
            main()

        captured = capsys.readouterr()
        assert "Error" in captured.err or "Path not found" in captured.err

    @pytest.mark.integration
    def test_main_nonexistent_path_json(self, tmp_path: Path, capsys) -> None:
        """Scenario: Run main with non-existent path in JSON mode.

        Given a path that doesn't exist
        When main is called with --output-json
        Then it should output JSON error.
        """
        fake_path = tmp_path / "nonexistent"
        with patch.object(
            sys,
            "argv",
            ["safe_replacer", "--path", str(fake_path), "--output-json"],
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.integration
    def test_main_validate_only_json(self, skill_tree: Path, capsys) -> None:
        """Scenario: Validate-only mode with JSON output.

        Given a directory with skill files
        When main is called with --validate-only --output-json
        Then it should output JSON with validate_only flag.
        """
        with patch.object(
            sys,
            "argv",
            [
                "safe_replacer",
                "--path",
                str(skill_tree),
                "--validate-only",
                "--output-json",
            ],
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["data"]["validate_only"] is True


class TestEdgeCases:
    """Feature: Edge case handling for safe_replacer."""

    @pytest.fixture
    def updater(self) -> SafeDependencyUpdater:
        """Create a fresh updater instance."""
        return SafeDependencyUpdater()

    @pytest.mark.unit
    def test_multiple_references_same_line(
        self, updater: SafeDependencyUpdater, tmp_path: Path
    ) -> None:
        """Scenario: Multiple references on same line.

        Given a file with multiple standalone references on one line
        When update_file is called
        Then it should update all of them.
        """
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("Uses git-workspace-review and review-core together.")

        updated, changes = updater.update_file(skill_file)

        assert updated is True
        content = skill_file.read_text()
        assert "sanctum:git-workspace-review" in content
        assert "imbue:review-core" in content

    @pytest.mark.unit
    def test_already_correct_not_duplicated(
        self, updater: SafeDependencyUpdater, tmp_path: Path
    ) -> None:
        """Scenario: Already correct reference not duplicated.

        Given a file with correct sanctum:git-workspace-review
        When update_file is called
        Then it should not create sanctum:sanctum:git-workspace-review.
        """
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("Uses sanctum:git-workspace-review correctly.")

        updated, changes = updater.update_file(skill_file)

        assert updated is False
        content = skill_file.read_text()
        assert "sanctum:sanctum:" not in content

    @pytest.mark.unit
    def test_empty_directory(
        self, updater: SafeDependencyUpdater, tmp_path: Path
    ) -> None:
        """Scenario: Empty directory with no skill files.

        Given an empty directory
        When update_directory is called
        Then it should return 0 files updated.
        """
        files_updated, total_changes = updater.update_directory(tmp_path)

        assert files_updated == 0
        assert total_changes == 0
