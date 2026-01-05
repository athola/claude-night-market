"""Test suite for sync_templates module.

Following BDD principles with Given/When/Then structure.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import functions from sync_templates
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sync_templates import TemplateSynchronizer, main


@pytest.mark.unit
class TestCheckReferenceProjects:
    """Test TemplateSynchronizer.check_reference_projects method."""

    def test_returns_false_for_missing_projects(self, tmp_path):
        """Given non-existent reference projects, when checking, then returns False."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        # Override references to point to non-existent paths
        syncer.references = {
            "python": {"project": tmp_path / "nonexistent", "files": {}},
        }

        # When
        available = syncer.check_reference_projects()

        # Then
        assert available["python"] is False

    def test_returns_true_for_existing_projects(self, tmp_path):
        """Given existing reference project, when checking, then returns True."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {"project": ref_project, "files": {}},
        }

        # When
        available = syncer.check_reference_projects()

        # Then
        assert available["python"] is True

    def test_checks_all_configured_languages(self, tmp_path):
        """Given multiple languages configured, when checking, then checks all."""
        # Given
        python_ref = tmp_path / "python-ref"
        python_ref.mkdir()
        rust_ref = tmp_path / "rust-ref"  # Not created

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {"project": python_ref, "files": {}},
            "rust": {"project": rust_ref, "files": {}},
        }

        # When
        available = syncer.check_reference_projects()

        # Then
        assert "python" in available
        assert "rust" in available
        assert available["python"] is True
        assert available["rust"] is False


@pytest.mark.unit
class TestExtractTemplateVariables:
    """Test TemplateSynchronizer.extract_template_variables method."""

    def test_extracts_python_project_name(self, tmp_path):
        """Given Python pyproject.toml content, when extracting, then replaces project name."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = '[project]\nname = "simple-resume"\nversion = "1.0.0"'

        # When
        result = syncer.extract_template_variables(content, "python")

        # Then
        assert "{{PROJECT_NAME}}" in result

    def test_extracts_python_description(self, tmp_path):
        """Given Python content with description, when extracting, then replaces it."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = 'description = "A resume builder"'

        # When
        result = syncer.extract_template_variables(content, "python")

        # Then
        assert "{{PROJECT_DESCRIPTION}}" in result

    def test_extracts_python_version(self, tmp_path):
        """Given Python content with requires-python, when extracting, then replaces it."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = 'requires-python = ">=3.11"'

        # When
        result = syncer.extract_template_variables(content, "python")

        # Then
        assert "{{PYTHON_VERSION}}" in result

    def test_extracts_rust_project_name(self, tmp_path):
        """Given Rust Cargo.toml content, when extracting, then replaces project name."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = '[package]\nname = "my-rust-project"\nversion = "0.1.0"'

        # When
        result = syncer.extract_template_variables(content, "rust")

        # Then
        assert "{{PROJECT_NAME}}" in result

    def test_extracts_rust_edition(self, tmp_path):
        """Given Rust Cargo.toml with edition, when extracting, then replaces it."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = 'edition = "2021"'

        # When
        result = syncer.extract_template_variables(content, "rust")

        # Then
        assert "{{RUST_EDITION}}" in result

    def test_handles_unknown_language(self, tmp_path):
        """Given unknown language, when extracting, then returns content unchanged."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        content = "some content"

        # When
        result = syncer.extract_template_variables(content, "unknown")

        # Then
        assert result == content


@pytest.mark.unit
class TestSyncLanguageTemplates:
    """Test TemplateSynchronizer.sync_language_templates method."""

    def test_returns_empty_for_unknown_language(self, tmp_path, capsys):
        """Given unknown language, when syncing, then returns empty list and prints error."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {}

        # When
        result = syncer.sync_language_templates("unknown")

        # Then
        assert result == []
        captured = capsys.readouterr()
        assert "No reference project configured" in captured.out

    def test_returns_empty_when_project_not_found(self, tmp_path, capsys):
        """Given missing reference project, when syncing, then returns empty list."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {"project": tmp_path / "nonexistent", "files": {}},
        }

        # When
        result = syncer.sync_language_templates("python")

        # Then
        assert result == []
        captured = capsys.readouterr()
        assert "Reference project not found" in captured.out

    def test_dry_run_does_not_create_files(self, tmp_path, capsys):
        """Given dry_run=True, when syncing, then only prints what would be done."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        (ref_project / ".gitignore").write_text("*.pyc\n")

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".gitignore": ".gitignore.template"},
            },
        }

        # When
        result = syncer.sync_language_templates("python", dry_run=True)

        # Then
        assert result == []  # Dry run doesn't return synced files
        captured = capsys.readouterr()
        assert "Would sync" in captured.out

        # Template file should not exist
        template_path = tmp_path / "templates" / "python" / ".gitignore.template"
        assert not template_path.exists()

    def test_creates_template_with_force(self, tmp_path, capsys):
        """Given force=True, when syncing, then overwrites without prompt."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        (ref_project / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".gitignore": ".gitignore.template"},
            },
        }

        # When
        result = syncer.sync_language_templates("python", force=True)

        # Then
        assert len(result) == 1
        captured = capsys.readouterr()
        assert "Synced" in captured.out

        # Template file should exist
        template_path = tmp_path / "templates" / "python" / ".gitignore.template"
        assert template_path.exists()

    def test_skips_missing_source_files(self, tmp_path, capsys):
        """Given source file not in reference, when syncing, then skips it."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        # Don't create the .gitignore file

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".gitignore": ".gitignore.template"},
            },
        }

        # When
        result = syncer.sync_language_templates("python", force=True)

        # Then
        assert result == []
        captured = capsys.readouterr()
        assert "not found in reference project" in captured.out

    def test_creates_nested_template_directories(self, tmp_path):
        """Given nested template path, when syncing, then creates parent directories."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        workflow_dir = ref_project / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "test.yml").write_text("name: Test\non: [push]")

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".github/workflows/test.yml": "workflows/test.yml.template"},
            },
        }

        # When
        syncer.sync_language_templates("python", force=True)

        # Then
        template_path = (
            tmp_path / "templates" / "python" / "workflows" / "test.yml.template"
        )
        assert template_path.exists()


@pytest.mark.unit
class TestSyncAll:
    """Test TemplateSynchronizer.sync_all method."""

    def test_syncs_all_available_languages(self, tmp_path, capsys):
        """Given multiple languages, when syncing all, then syncs available ones."""
        # Given
        python_ref = tmp_path / "python-ref"
        python_ref.mkdir()
        (python_ref / ".gitignore").write_text("*.pyc\n")

        rust_ref = tmp_path / "rust-ref"  # Not created - should be skipped

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": python_ref,
                "files": {".gitignore": ".gitignore.template"},
            },
            "rust": {"project": rust_ref, "files": {}},
        }

        # When
        result = syncer.sync_all(force=True)

        # Then
        assert "python" in result
        captured = capsys.readouterr()
        assert "Skipping rust" in captured.out

    def test_returns_empty_dict_when_no_languages_available(self, tmp_path, capsys):
        """Given no available projects, when syncing all, then returns empty dict."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {"project": tmp_path / "nonexistent", "files": {}},
        }

        # When
        result = syncer.sync_all()

        # Then
        assert "python" not in result


@pytest.mark.unit
class TestShowStatus:
    """Test TemplateSynchronizer.show_status method."""

    def test_shows_status_header(self, tmp_path, capsys):
        """Given syncer, when showing status, then prints header."""
        # Given
        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {}

        # When
        syncer.show_status()

        # Then
        captured = capsys.readouterr()
        assert "Template Synchronization Status" in captured.out

    def test_shows_available_reference_projects(self, tmp_path, capsys):
        """Given available project, when showing status, then marks as available."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {"project": ref_project, "files": {}},
        }

        # When
        syncer.show_status()

        # Then
        captured = capsys.readouterr()
        assert "Python:" in captured.out
        assert str(ref_project) in captured.out

    def test_shows_outdated_templates(self, tmp_path, capsys):
        """Given outdated template, when showing status, then marks as outdated."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        source_file = ref_project / ".gitignore"
        source_file.write_text("*.pyc\n")

        # Create template directory and file
        templates_dir = tmp_path / "templates" / "python"
        templates_dir.mkdir(parents=True)
        template_file = templates_dir / ".gitignore.template"
        template_file.write_text("old content")

        # Make source newer than template (touch source after template)
        import os
        import time

        # Set template mtime to past
        past_time = time.time() - 3600
        os.utime(template_file, (past_time, past_time))

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".gitignore": ".gitignore.template"},
            },
        }

        # When
        syncer.show_status()

        # Then
        captured = capsys.readouterr()
        assert "outdated" in captured.out or "up-to-date" in captured.out

    def test_shows_not_synced_templates(self, tmp_path, capsys):
        """Given missing template, when showing status, then marks as not synced."""
        # Given
        ref_project = tmp_path / "reference"
        ref_project.mkdir()
        (ref_project / ".gitignore").write_text("*.pyc\n")

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {".gitignore": ".gitignore.template"},
            },
        }

        # When
        syncer.show_status()

        # Then
        captured = capsys.readouterr()
        assert "not synced" in captured.out


@pytest.mark.unit
class TestMain:
    """Test the main() CLI entry point."""

    @patch("sync_templates.TemplateSynchronizer.show_status")
    def test_main_status_flag_shows_status(self, mock_show_status):
        """Given --status flag, when running main, then shows status."""
        # Given
        with patch("sys.argv", ["sync_templates.py", "--status"]):
            # When
            main()

            # Then
            mock_show_status.assert_called_once()

    @patch("sync_templates.TemplateSynchronizer.sync_all")
    def test_main_syncs_all_by_default(self, mock_sync_all):
        """Given no language flag, when running main, then syncs all."""
        # Given
        mock_sync_all.return_value = {}
        with patch("sys.argv", ["sync_templates.py", "--dry-run"]):
            # When
            main()

            # Then
            mock_sync_all.assert_called_once()

    @patch("sync_templates.TemplateSynchronizer.sync_language_templates")
    def test_main_syncs_specific_language(self, mock_sync_lang):
        """Given --language flag, when running main, then syncs that language."""
        # Given
        mock_sync_lang.return_value = []
        with patch(
            "sys.argv", ["sync_templates.py", "--language", "python", "--dry-run"]
        ):
            # When
            main()

            # Then
            mock_sync_lang.assert_called_once()
            assert mock_sync_lang.call_args[0][0] == "python"

    @patch("sync_templates.TemplateSynchronizer.sync_language_templates")
    def test_main_passes_force_flag(self, mock_sync_lang):
        """Given --force flag, when running main, then passes force=True."""
        # Given
        mock_sync_lang.return_value = []
        with patch("sys.argv", ["sync_templates.py", "-l", "python", "-f"]):
            # When
            main()

            # Then
            call_kwargs = mock_sync_lang.call_args[1]
            assert call_kwargs["force"] is True


@pytest.mark.unit
class TestTemplateSynchronizerBehavior:
    """BDD-style tests for TemplateSynchronizer behavior."""

    def test_scenario_sync_python_templates_from_reference(self, tmp_path):
        """Given a Python reference project with config files
        When syncing Python templates
        Then creates templates with variable placeholders
        """
        # Given - Reference project with files
        ref_project = tmp_path / "python-ref"
        ref_project.mkdir()

        (ref_project / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        (ref_project / "pyproject.toml").write_text(
            '[project]\nname = "simple-resume"\ndescription = "A resume tool"'
        )

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {
                    ".gitignore": ".gitignore.template",
                    "pyproject.toml": "pyproject.toml.template",
                },
            },
        }

        # When
        result = syncer.sync_language_templates("python", force=True)

        # Then - Templates created
        assert len(result) == 2

        # Then - Variables extracted in pyproject.toml
        pyproject_template = (
            tmp_path / "templates" / "python" / "pyproject.toml.template"
        )
        content = pyproject_template.read_text()
        assert "{{PROJECT_NAME}}" in content
        assert "{{PROJECT_DESCRIPTION}}" in content

    def test_scenario_dry_run_reports_without_changes(self, tmp_path, capsys):
        """Given a reference project with files
        When running dry-run sync
        Then reports what would be done without creating files
        """
        # Given
        ref_project = tmp_path / "python-ref"
        ref_project.mkdir()
        (ref_project / ".gitignore").write_text("*.pyc\n")
        (ref_project / "Makefile").write_text(".PHONY: test\ntest:\n\tpytest")

        syncer = TemplateSynchronizer(tmp_path)
        syncer.references = {
            "python": {
                "project": ref_project,
                "files": {
                    ".gitignore": ".gitignore.template",
                    "Makefile": "Makefile.template",
                },
            },
        }

        # When
        result = syncer.sync_language_templates("python", dry_run=True)

        # Then - No files created
        assert result == []
        templates_dir = tmp_path / "templates" / "python"
        assert not templates_dir.exists() or not any(templates_dir.iterdir())

        # Then - Reports what would be done
        captured = capsys.readouterr()
        assert "Would sync" in captured.out
        assert ".gitignore" in captured.out
        assert "Makefile" in captured.out
