"""Test suite for attune_upgrade module.

Following BDD principles with Given/When/Then structure.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from attune_upgrade
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from attune_upgrade import ProjectUpgrader, main


@pytest.mark.unit
class TestGetMissingFiles:
    """Test ProjectUpgrader.get_missing_files method."""

    def test_get_missing_files_returns_empty_when_all_exist(self, python_project):
        """Given all files exist, when checking for missing, then returns empty list."""
        # Given
        upgrader = ProjectUpgrader(python_project, "python")
        (python_project / ".gitignore").touch()
        (python_project / "Makefile").touch()
        (python_project / ".pre-commit-config.yaml").touch()
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").touch()
        (workflows_dir / "lint.yml").touch()
        (workflows_dir / "typecheck.yml").touch()

        # When
        missing = upgrader.get_missing_files("all")

        # Then
        assert missing == []

    def test_get_missing_files_returns_missing_gitignore(self, mock_project_path):
        """Given no .gitignore, when checking gitignore component, then returns it."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        missing = upgrader.get_missing_files("gitignore")

        # Then
        assert ".gitignore" in missing

    def test_get_missing_files_returns_missing_makefile(self, mock_project_path):
        """Given no Makefile, when checking makefile component, then returns it."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        missing = upgrader.get_missing_files("makefile")

        # Then
        assert "Makefile" in missing

    def test_get_missing_files_handles_python_workflows(self, mock_project_path):
        """Given Python project, when checking workflows, then includes typecheck."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        missing = upgrader.get_missing_files("workflows")

        # Then
        assert ".github/workflows/test.yml" in missing
        assert ".github/workflows/lint.yml" in missing
        assert ".github/workflows/typecheck.yml" in missing

    def test_get_missing_files_handles_rust_workflows(self, mock_project_path):
        """Given Rust project, when checking workflows, then includes ci.yml."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "rust")

        # When
        missing = upgrader.get_missing_files("workflows")

        # Then
        assert ".github/workflows/ci.yml" in missing

    def test_get_missing_files_handles_typescript_build(self, mock_project_path):
        """Given TypeScript project, when checking build, then includes package.json and tsconfig."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "typescript")

        # When
        missing = upgrader.get_missing_files("build")

        # Then
        assert "package.json" in missing
        assert "tsconfig.json" in missing

    def test_get_missing_files_returns_empty_for_unknown_component(
        self, mock_project_path, capsys
    ):
        """Given unknown component, when checking, then returns empty and warns."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        missing = upgrader.get_missing_files("unknown")

        # Then
        assert missing == []
        captured = capsys.readouterr()
        assert "Unknown component 'unknown'" in captured.err


@pytest.mark.unit
class TestGetOutdatedFiles:
    """Test ProjectUpgrader.get_outdated_files method."""

    def test_get_outdated_files_detects_missing_help_command(self, python_project):
        """Given Makefile without help, when checking outdated, then flags it."""
        # Given
        makefile = python_project / "Makefile"
        makefile.write_text(
            """
.PHONY: test
test:
\tpytest
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert "Makefile" in outdated
        assert "Missing help command" in outdated["Makefile"]

    def test_get_outdated_files_accepts_makefile_with_help(self, python_project):
        """Given Makefile with help, when checking outdated, then passes."""
        # Given
        makefile = python_project / "Makefile"
        makefile.write_text(
            """
.PHONY: help
help: ## Show this help
\t@echo "Usage: make [target]"
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert "Makefile" not in outdated

    def test_get_outdated_files_detects_old_checkout_v2(self, python_project):
        """Given workflow with checkout v2, when checking outdated, then flags it."""
        # Given
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text(
            """
name: Test
jobs:
  test:
    steps:
      - uses: actions/checkout@v2
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert ".github/workflows/test.yml" in outdated
        assert "outdated GitHub Actions" in outdated[".github/workflows/test.yml"]

    def test_get_outdated_files_detects_old_checkout_v3(self, python_project):
        """Given workflow with checkout v3, when checking outdated, then flags it."""
        # Given
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            """
name: CI
jobs:
  build:
    steps:
      - uses: actions/checkout@v3
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert ".github/workflows/ci.yml" in outdated

    def test_get_outdated_files_accepts_checkout_v4(self, python_project):
        """Given workflow with checkout v4, when checking outdated, then passes."""
        # Given
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text(
            """
name: Test
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert ".github/workflows/test.yml" not in outdated

    def test_get_outdated_files_handles_no_workflows_dir(self, mock_project_path):
        """Given no workflows directory, when checking outdated, then handles gracefully."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        outdated = upgrader.get_outdated_files()

        # Then
        assert isinstance(outdated, dict)


@pytest.mark.unit
class TestShowStatus:
    """Test ProjectUpgrader.show_status method."""

    def test_show_status_prints_project_info(self, python_project, capsys):
        """Given a project, when showing status, then prints project info."""
        # Given
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        upgrader.show_status()

        # Then
        captured = capsys.readouterr()
        assert "Attune Upgrade Status" in captured.out
        assert "python" in captured.out

    def test_show_status_shows_missing_files(self, mock_project_path, capsys):
        """Given project with missing files, when showing status, then lists them."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        upgrader.show_status()

        # Then
        captured = capsys.readouterr()
        assert "Missing:" in captured.out

    def test_show_status_shows_outdated_files(self, python_project, capsys):
        """Given project with outdated files, when showing status, then lists them."""
        # Given
        makefile = python_project / "Makefile"
        makefile.write_text(".PHONY: test\ntest:\n\tpytest\n")
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        upgrader.show_status()

        # Then
        captured = capsys.readouterr()
        assert "Outdated:" in captured.out

    def test_show_status_shows_all_up_to_date_message(self, python_project, capsys):
        """Given project with all configs, when showing status, then shows success."""
        # Given
        (python_project / ".gitignore").touch()
        makefile = python_project / "Makefile"
        makefile.write_text(".PHONY: help\nhelp: ## Show this help\n\t@echo help\n")
        (python_project / ".pre-commit-config.yaml").touch()
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text("steps:\n  - uses: actions/checkout@v4")
        (workflows_dir / "lint.yml").touch()
        (workflows_dir / "typecheck.yml").touch()
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        upgrader.show_status()

        # Then
        captured = capsys.readouterr()
        assert "All configurations up-to-date" in captured.out


@pytest.mark.unit
class TestUpgrade:
    """Test ProjectUpgrader.upgrade method."""

    def test_upgrade_dry_run_shows_preview(self, mock_project_path, capsys):
        """Given dry_run=True, when upgrading, then only shows preview."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        result = upgrader.upgrade(dry_run=True)

        # Then
        captured = capsys.readouterr()
        assert "Dry Run" in captured.out
        assert "Would add" in captured.out
        assert result == []

    @patch("attune_init.copy_templates")
    def test_upgrade_calls_copy_templates_with_missing(
        self, mock_copy_templates, mock_project_path
    ):
        """Given missing files, when upgrading, then copies templates."""
        # Given
        mock_copy_templates.return_value = [".gitignore", "Makefile"]
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        result = upgrader.upgrade()

        # Then
        mock_copy_templates.assert_called_once()
        assert ".gitignore" in result or "Makefile" in result

    def test_upgrade_skips_when_no_missing_files(self, python_project):
        """Given all files exist, when upgrading, then skips copy."""
        # Given
        (python_project / ".gitignore").touch()
        (python_project / "Makefile").touch()
        (python_project / ".pre-commit-config.yaml").touch()
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").touch()
        (workflows_dir / "lint.yml").touch()
        (workflows_dir / "typecheck.yml").touch()
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        result = upgrader.upgrade()

        # Then - Returns empty list when nothing is missing
        assert result == []


@pytest.mark.unit
class TestInferVariables:
    """Test ProjectUpgrader._infer_variables method."""

    def test_infer_variables_extracts_from_pyproject(self, python_project):
        """Given pyproject.toml with metadata, when inferring, then extracts values."""
        # Given
        pyproject = python_project / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-cool-project"
version = "1.0.0"
requires-python = ">=3.11"
"""
        )
        upgrader = ProjectUpgrader(python_project, "python")

        # When
        variables = upgrader._infer_variables()

        # Then
        assert variables["PROJECT_NAME"] == "my-cool-project"
        assert "3.11" in str(variables)

    def test_infer_variables_uses_fallback_for_missing_pyproject(
        self, mock_project_path
    ):
        """Given no pyproject.toml, when inferring, then uses fallback."""
        # Given
        upgrader = ProjectUpgrader(mock_project_path, "python")

        # When
        variables = upgrader._infer_variables()

        # Then
        assert variables["PROJECT_NAME"] == mock_project_path.name

    def test_infer_variables_uses_fallback_for_rust(self, rust_project):
        """Given Rust project, when inferring, then uses project path name."""
        # Given
        upgrader = ProjectUpgrader(rust_project, "rust")

        # When
        variables = upgrader._infer_variables()

        # Then
        assert "PROJECT_NAME" in variables


@pytest.mark.unit
class TestMain:
    """Test the main() CLI entry point."""

    @patch("attune_upgrade.ProjectUpgrader")
    @patch("attune_upgrade.ProjectDetector")
    def test_main_status_flag_shows_status_only(
        self, mock_detector_cls, mock_upgrader_cls, mock_project_path
    ):
        """Given --status flag, when running main, then shows status and exits."""
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector_cls.return_value = mock_detector

        mock_upgrader = Mock()
        mock_upgrader_cls.return_value = mock_upgrader

        with patch(
            "sys.argv",
            ["attune_upgrade.py", "--path", str(mock_project_path), "--status"],
        ):
            # When/Then
            with pytest.raises(SystemExit) as excinfo:
                main()

            # Then
            assert excinfo.value.code == 0
            mock_upgrader.show_status.assert_called_once_with(verbose=True)

    @patch("attune_upgrade.ProjectDetector")
    def test_main_exits_when_language_not_detected(
        self, mock_detector_cls, mock_project_path, capsys
    ):
        """Given no detected language and no --lang, when running main, then exits with error."""
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = None
        mock_detector_cls.return_value = mock_detector

        with patch("sys.argv", ["attune_upgrade.py", "--path", str(mock_project_path)]):
            # When/Then
            with pytest.raises(SystemExit) as excinfo:
                main()

            # Then
            assert excinfo.value.code == 1
            captured = capsys.readouterr()
            assert "Could not detect project language" in captured.err

    @patch("attune_upgrade.ProjectUpgrader")
    @patch("attune_upgrade.ProjectDetector")
    @patch("builtins.input", return_value="n")
    def test_main_dry_run_skips_prompt(
        self, mock_input, mock_detector_cls, mock_upgrader_cls, mock_project_path
    ):
        """Given --dry-run flag, when running main, then skips confirmation prompt."""
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector_cls.return_value = mock_detector

        mock_upgrader = Mock()
        mock_upgrader.upgrade.return_value = []
        mock_upgrader_cls.return_value = mock_upgrader

        with patch(
            "sys.argv",
            ["attune_upgrade.py", "--path", str(mock_project_path), "--dry-run"],
        ):
            # When
            main()

            # Then
            mock_upgrader.upgrade.assert_called_once()
            call_kwargs = mock_upgrader.upgrade.call_args[1]
            assert call_kwargs["dry_run"] is True


@pytest.mark.unit
class TestProjectUpgraderBehavior:
    """BDD-style tests for ProjectUpgrader behavior scenarios."""

    def test_scenario_detect_missing_and_outdated_in_python_project(
        self, python_project
    ):
        """
        Given a Python project with some missing and outdated configs
        When checking upgrade status
        Then identifies both missing and outdated files
        """
        # Given - Python project with outdated Makefile and missing pre-commit
        makefile = python_project / "Makefile"
        makefile.write_text(".PHONY: test\ntest:\n\tpytest\n")
        (python_project / ".gitignore").touch()

        upgrader = ProjectUpgrader(python_project, "python")

        # When
        missing = upgrader.get_missing_files("all")
        outdated = upgrader.get_outdated_files()

        # Then
        assert ".pre-commit-config.yaml" in missing
        assert "Makefile" in outdated

    def test_scenario_complete_python_project_no_upgrades_needed(self, python_project):
        """
        Given a Python project with all modern configs
        When checking upgrade status
        Then reports no upgrades needed
        """
        # Given - Complete modern Python project
        (python_project / ".gitignore").touch()
        (python_project / "Makefile").write_text(
            ".PHONY: help\nhelp: ## Show this help\n\t@echo help\n"
        )
        (python_project / ".pre-commit-config.yaml").touch()
        workflows_dir = python_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text("- uses: actions/checkout@v4")
        (workflows_dir / "lint.yml").touch()
        (workflows_dir / "typecheck.yml").touch()

        upgrader = ProjectUpgrader(python_project, "python")

        # When
        missing = upgrader.get_missing_files("all")
        outdated = upgrader.get_outdated_files()

        # Then
        assert missing == []
        assert outdated == {}
