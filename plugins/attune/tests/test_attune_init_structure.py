"""Tests for attune_init project structure creation, dry-run, and backup.

Covers:
- TestCreateProjectStructure
- TestMain (CLI entry point)
- TestCopyTemplatesDryRun
- TestCopyTemplatesBackup
- TestCreateProjectStructureDryRun
- TestMainDryRunAndBackupFlags
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from attune_init import (
    copy_templates,
    create_project_structure,
    main,
)


@pytest.mark.unit
class TestCreateProjectStructure:
    """Test project structure creation behavior."""

    @pytest.mark.parametrize(
        ("language", "expected_files"),
        [
            ("python", ["src/test_module/__init__.py"]),
            ("rust", ["src/main.rs", "src/lib.rs"]),
            ("typescript", ["src/index.ts", "src/App.tsx"]),
        ],
        ids=["python-dirs", "rust-dirs", "typescript-dirs"],
    )
    def test_create_project_structure_creates_expected_files(
        self, tmp_path, language, expected_files
    ):
        """Given a language, when creating structure, then expected files exist."""
        # Given
        project_dir = tmp_path / f"{language}-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, language, "test_module", "test-project")

        # Then
        for rel_path in expected_files:
            assert (project_dir / rel_path).exists(), f"Missing {rel_path}"

    @pytest.mark.parametrize(
        ("language", "project_name"),
        [
            ("python", "my-project"),
            ("rust", "rust-project"),
            ("typescript", "my-ts-project"),
        ],
        ids=["python-readme", "rust-readme", "typescript-readme"],
    )
    def test_create_project_creates_readme_with_name(
        self, tmp_path, language, project_name
    ):
        """Given a language, when creating structure, then README.md contains
        the project name.
        """
        # Given
        project_dir = tmp_path / f"{language}-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, language, "test_module", project_name)

        # Then
        readme = project_dir / "README.md"
        assert readme.exists()
        assert project_name in readme.read_text()

    def test_create_python_project_creates_tests_directory(self, tmp_path):
        """Given Python language, when creating structure, then creates tests directory."""
        # Given
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "python", "test_module", "test-project")

        # Then
        tests_dir = project_dir / "tests"
        assert tests_dir.exists()
        assert (tests_dir / "__init__.py").exists()

    def test_create_project_structure_skips_existing_files(self, tmp_path):
        """Given existing files, when creating structure, then skips existing files."""
        # Given
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()
        src_dir = project_dir / "src" / "test_module"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text("# Existing content")

        # When
        create_project_structure(project_dir, "python", "test_module", "test-project")

        # Then
        # Existing content should be preserved
        assert init_file.read_text() == "# Existing content"

    def test_create_python_init_includes_version(self, tmp_path):
        """Given Python language, when creating structure, then __init__.py
        includes version.
        """
        # Given
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "python", "test_module", "test-project")

        # Then
        init_file = project_dir / "src" / "test_module" / "__init__.py"
        content = init_file.read_text()
        assert '__version__ = "0.1.0"' in content


@pytest.mark.bdd
class TestAttuneInitScenario:
    """BDD scenario: creating a complete Python project structure."""

    def test_scenario_create_complete_python_project(self, tmp_path):
        """Scenario: Creating a complete Python project structure.

        Given a project directory
        When I create the project structure
        Then it should have src, tests, and README
        """
        # Given
        project_dir = tmp_path / "complete-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "python", "myproject", "my-project")

        # Then
        assert (project_dir / "src" / "myproject" / "__init__.py").exists()
        assert (project_dir / "tests" / "__init__.py").exists()
        assert (project_dir / "README.md").exists()


@pytest.mark.unit
class TestMain:
    """Test the main() CLI entry point for attune_init."""

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_with_python_language(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --lang python, when running main, then initializes Python project."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = False
        mock_detector_cls.return_value = mock_detector
        mock_init_git.return_value = True
        mock_copy_templates.return_value = ["file1", "file2"]

        with patch(
            "sys.argv",
            ["attune_init.py", "--lang", "python", "--path", str(mock_project_path)],
        ):
            main()

            mock_copy_templates.assert_called_once()
            call_kwargs = mock_copy_templates.call_args[1]
            assert call_kwargs["language"] == "python"

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_detects_language_when_not_specified(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        python_project,
    ):
        """Given no --lang but Python project, when running main, then detects Python."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch("sys.argv", ["attune_init.py", "--path", str(python_project)]):
            main()

            mock_detector.detect_language.assert_called_once()
            mock_copy_templates.assert_called_once()

    @patch("attune_init.ProjectDetector")
    def test_main_exits_when_language_not_detected(
        self, mock_detector_cls, mock_project_path, capsys
    ):
        """Given no language detected and no --lang, when running main, then
        exits with error.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = None
        mock_detector_cls.return_value = mock_detector

        with patch("sys.argv", ["attune_init.py", "--path", str(mock_project_path)]):
            with pytest.raises(SystemExit) as excinfo:
                main()

            assert excinfo.value.code == 1
            captured = capsys.readouterr()
            assert "Could not detect project language" in captured.err

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_skips_git_with_no_git_flag(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --no-git flag, when running main, then skips git initialization."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = False
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--no-git",
            ],
        ):
            main()

            mock_init_git.assert_not_called()

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_uses_custom_project_name(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --name argument, when running main, then uses custom name."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--name",
                "custom-name",
            ],
        ):
            main()

            mock_create_structure.assert_called_once()
            call_args = mock_create_structure.call_args[0]
            assert call_args[3] == "custom-name"  # project_name is 4th arg

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_passes_force_flag(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --force flag, when running main, then passes force=True."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "rust"
        mock_detector.check_git_initialized.return_value = False
        mock_detector_cls.return_value = mock_detector
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "rust",
                "--path",
                str(mock_project_path),
                "--force",
            ],
        ):
            main()

            mock_init_git.assert_called_once_with(mock_project_path, force=True)
            call_kwargs = mock_copy_templates.call_args[1]
            assert call_kwargs["force"] is True

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_main_prints_success_message(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
        capsys,
    ):
        """When project initialized successfully, then prints success message."""
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = ["file1", "file2"]

        with patch(
            "sys.argv",
            ["attune_init.py", "--lang", "python", "--path", str(mock_project_path)],
        ):
            main()

            captured = capsys.readouterr()
            assert "Project initialized successfully" in captured.out
            assert "Created 2 files" in captured.out
            assert "Next steps" in captured.out


@pytest.mark.unit
class TestCopyTemplatesDryRun:
    """Test copy_templates() dry-run behavior."""

    def test_dry_run_returns_file_list_without_writing(
        self, tmp_path, sample_template_variables
    ):
        """Given dry_run=True, when copying templates, then no files written."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "test.txt.template").write_text("Project: {{PROJECT_NAME}}")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
        )

        # Then
        assert len(created) == 1
        assert not (project_dir / "test.txt").exists()

    def test_dry_run_returns_correct_output_paths(
        self, tmp_path, sample_template_variables
    ):
        """Given dry_run=True, when copying, then returned paths match expected output."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "Makefile.template").write_text("help:")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
        )

        # Then
        assert str(project_dir / "Makefile") in created

    def test_dry_run_prints_would_create_for_new_file(
        self, tmp_path, sample_template_variables, capsys
    ):
        """Given dry_run=True and no existing file, when copying, then prints
        [DRY RUN] Would create.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "new.txt.template").write_text("content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
        )

        # Then
        captured = capsys.readouterr()
        assert "[DRY RUN] Would create:" in captured.out

    def test_dry_run_prints_would_overwrite_for_existing_file(
        self, tmp_path, sample_template_variables, capsys
    ):
        """Given dry_run=True and an existing file, when copying, then prints
        [DRY RUN] Would overwrite.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "existing.txt.template").write_text("new content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "existing.txt").write_text("old content")

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
        )

        # Then
        captured = capsys.readouterr()
        assert "[DRY RUN] Would overwrite:" in captured.out
        # Existing file must not be changed
        assert (project_dir / "existing.txt").read_text() == "old content"

    def test_dry_run_handles_multiple_templates(
        self, tmp_path, sample_template_variables
    ):
        """Given multiple templates, when dry_run=True, then all appear in result
        with no files written.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "a.txt.template").write_text("a")
        (python_dir / "b.txt.template").write_text("b")
        (python_dir / "c.txt.template").write_text("c")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
        )

        # Then
        assert len(created) == 3
        # No files should exist in the output directory
        assert list(project_dir.iterdir()) == []

    def test_dry_run_does_not_create_backup_dir(
        self, tmp_path, sample_template_variables
    ):
        """Given dry_run=True with backup=True, when copying, then no output
        files are written.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "test.txt.template").write_text("content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            dry_run=True,
            backup=True,
        )

        # Then - output file must not exist
        assert not (project_dir / "test.txt").exists()


@pytest.mark.unit
class TestCopyTemplatesBackup:
    """Test copy_templates() backup behavior."""

    def test_backup_creates_backup_directory(self, tmp_path, sample_template_variables):
        """Given backup=True, when copying, then .backup directory is created."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "test.txt.template").write_text("new content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "test.txt").write_text("old content")

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        backup_root = project_dir / ".backup"
        assert backup_root.exists()
        assert backup_root.is_dir()

    def test_backup_preserves_existing_file_content(
        self, tmp_path, sample_template_variables
    ):
        """Given an existing file and backup=True, when copying, then the original
        content is preserved in the backup directory.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "config.txt.template").write_text("new content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        original_content = "original file content"
        (project_dir / "config.txt").write_text(original_content)

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        backup_root = project_dir / ".backup"
        timestamp_dirs = list(backup_root.iterdir())
        assert len(timestamp_dirs) == 1
        backup_file = timestamp_dirs[0] / "config.txt"
        assert backup_file.exists()
        assert backup_file.read_text() == original_content

    def test_backup_overwrites_file_with_rendered_template(
        self, tmp_path, sample_template_variables
    ):
        """Given backup=True and force=True, when copying, then output file
        contains rendered template content.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "readme.txt.template").write_text("# {{PROJECT_NAME}}")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "readme.txt").write_text("old readme")

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        assert "test-project" in (project_dir / "readme.txt").read_text()

    def test_backup_only_backs_up_files_that_exist(
        self, tmp_path, sample_template_variables
    ):
        """Given a mix of new and existing files, when backup=True, then only
        pre-existing files appear in the backup directory.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "existing.txt.template").write_text("updated")
        (python_dir / "new.txt.template").write_text("brand new")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "existing.txt").write_text("pre-existing")

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        backup_root = project_dir / ".backup"
        timestamp_dirs = list(backup_root.iterdir())
        assert len(timestamp_dirs) == 1
        backed_up = list(timestamp_dirs[0].rglob("*"))
        backed_up_names = [p.name for p in backed_up if p.is_file()]
        assert "existing.txt" in backed_up_names
        assert "new.txt" not in backed_up_names

    def test_backup_creates_timestamped_subdirectory(
        self, tmp_path, sample_template_variables
    ):
        """Given backup=True, when copying, then backup subdir name matches
        YYYYMMDD_HHMMSS timestamp pattern.
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "file.txt.template").write_text("content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "file.txt").write_text("original")

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        backup_root = project_dir / ".backup"
        timestamp_dirs = list(backup_root.iterdir())
        assert len(timestamp_dirs) == 1
        pattern = re.compile(r"^\d{8}_\d{6}$")
        assert pattern.match(timestamp_dirs[0].name)

    def test_backup_prints_backup_directory_path(
        self, tmp_path, sample_template_variables, capsys
    ):
        """Given backup=True, when copying, then prints the backup directory path."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "file.txt.template").write_text("content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
            backup=True,
        )

        # Then
        captured = capsys.readouterr()
        assert "Backup directory:" in captured.out


@pytest.mark.unit
class TestCreateProjectStructureDryRun:
    """Test create_project_structure() dry-run behavior."""

    def test_python_dry_run_creates_no_directories(self, tmp_path):
        """Given dry_run=True for Python, when creating structure, then no dirs
        are created.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "python", "my_module", "my-project", dry_run=True
        )

        assert not (project_dir / "src").exists()
        assert not (project_dir / "tests").exists()

    def test_python_dry_run_creates_no_files(self, tmp_path):
        """Given dry_run=True for Python, when creating structure, then no files
        are written.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "python", "my_module", "my-project", dry_run=True
        )

        assert not (project_dir / "src" / "my_module" / "__init__.py").exists()
        assert not (project_dir / "tests" / "__init__.py").exists()
        assert not (project_dir / "README.md").exists()

    def test_python_dry_run_prints_would_create_messages(self, tmp_path, capsys):
        """Given dry_run=True for Python, when creating structure, then each
        planned action is printed.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "python", "my_module", "my-project", dry_run=True
        )

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "my_module" in captured.out

    def test_rust_dry_run_creates_no_files(self, tmp_path):
        """Given dry_run=True for Rust, when creating structure, then no files
        are written.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "rust", "my_crate", "my-project", dry_run=True
        )

        assert not (project_dir / "src").exists()
        assert not (project_dir / "README.md").exists()

    def test_rust_dry_run_prints_would_create_messages(self, tmp_path, capsys):
        """Given dry_run=True for Rust, when creating structure, then planned
        file paths are printed.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "rust", "my_crate", "my-project", dry_run=True
        )

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "main.rs" in captured.out

    def test_typescript_dry_run_creates_no_files(self, tmp_path):
        """Given dry_run=True for TypeScript, when creating structure, then no
        files are written.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "typescript", "my_app", "my-project", dry_run=True
        )

        assert not (project_dir / "src").exists()
        assert not (project_dir / "README.md").exists()

    def test_typescript_dry_run_prints_would_create_messages(self, tmp_path, capsys):
        """Given dry_run=True for TypeScript, when creating structure, then planned
        file paths are printed.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        create_project_structure(
            project_dir, "typescript", "my_app", "my-project", dry_run=True
        )

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "index.ts" in captured.out

    def test_dry_run_skips_message_for_already_existing_files(self, tmp_path, capsys):
        """Given an already-existing __init__.py, when dry_run=True, then the
        would-create message for that file is suppressed.
        """
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        src_dir = project_dir / "src" / "my_module"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# existing")

        create_project_structure(
            project_dir, "python", "my_module", "my-project", dry_run=True
        )

        assert (src_dir / "__init__.py").read_text() == "# existing"
        captured = capsys.readouterr()
        assert "Would create: " + str(src_dir / "__init__.py") not in captured.out


@pytest.mark.unit
class TestMainDryRunAndBackupFlags:
    """Test CLI integration for --dry-run, --backup, and combined flags."""

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_dry_run_flag_passed_to_copy_templates(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --dry-run flag, when running main, then copy_templates receives
        dry_run=True.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--dry-run",
            ],
        ):
            main()

        call_kwargs = mock_copy_templates.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_dry_run_flag_passed_to_create_project_structure(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --dry-run flag, when running main, then create_project_structure
        receives dry_run=True.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--dry-run",
            ],
        ):
            main()

        call_kwargs = mock_create_structure.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_backup_flag_passed_to_copy_templates(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --backup flag, when running main, then copy_templates receives
        backup=True.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--backup",
            ],
        ):
            main()

        call_kwargs = mock_copy_templates.call_args[1]
        assert call_kwargs["backup"] is True

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_backup_and_force_flags_both_passed(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given --backup --force flags, when running main, then copy_templates
        receives both backup=True and force=True.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = False
        mock_detector_cls.return_value = mock_detector
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            [
                "attune_init.py",
                "--lang",
                "python",
                "--path",
                str(mock_project_path),
                "--backup",
                "--force",
            ],
        ):
            main()

        call_kwargs = mock_copy_templates.call_args[1]
        assert call_kwargs["backup"] is True
        assert call_kwargs["force"] is True

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_no_dry_run_flag_defaults_to_false(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given no --dry-run flag, when running main, then dry_run defaults to
        False.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            ["attune_init.py", "--lang", "python", "--path", str(mock_project_path)],
        ):
            main()

        copy_kwargs = mock_copy_templates.call_args[1]
        structure_kwargs = mock_create_structure.call_args[1]
        assert copy_kwargs["dry_run"] is False
        assert structure_kwargs["dry_run"] is False

    @patch("attune_init.copy_templates")
    @patch("attune_init.create_project_structure")
    @patch("attune_init.initialize_git")
    @patch("attune_init.ProjectDetector")
    def test_no_backup_flag_defaults_to_false(
        self,
        mock_detector_cls,
        mock_init_git,
        mock_create_structure,
        mock_copy_templates,
        mock_project_path,
    ):
        """Given no --backup flag, when running main, then backup defaults to
        False.
        """
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch(
            "sys.argv",
            ["attune_init.py", "--lang", "python", "--path", str(mock_project_path)],
        ):
            main()

        call_kwargs = mock_copy_templates.call_args[1]
        assert call_kwargs["backup"] is False
