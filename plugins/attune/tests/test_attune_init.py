"""Test suite for attune_init module.

Following BDD principles with Given/When/Then structure.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import functions from attune_init
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from attune_init import (
    copy_templates,
    create_project_structure,
    initialize_git,
)


@pytest.mark.unit
class TestInitializeGit:
    """Test git initialization behavior."""

    @patch("subprocess.run")
    def test_initialize_git_creates_repository(self, mock_run, mock_project_path):
        """Given a project without git, when initializing git, then runs git init."""
        # Given
        mock_run.return_value = Mock(returncode=0)

        # When
        result = initialize_git(mock_project_path)

        # Then
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["git", "init"]
        assert call_args[1]["cwd"] == mock_project_path

    @patch("subprocess.run")
    def test_initialize_git_skips_if_exists(self, mock_run, git_project):
        """Given a project with git initialized, when initializing git, then skips."""
        # When
        result = initialize_git(git_project)

        # Then
        assert result is True
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_initialize_git_force_reinitializes(self, mock_run, git_project):
        """Given a project with git and force=True, when initializing git, then reinitializes."""
        # Given
        mock_run.return_value = Mock(returncode=0)

        # When
        result = initialize_git(git_project, force=True)

        # Then
        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_initialize_git_handles_failure(self, mock_run, mock_project_path):
        """Given git init fails, when initializing git, then returns False."""
        # Given
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "init"])

        # When
        result = initialize_git(mock_project_path)

        # Then
        assert result is False

    @patch("subprocess.run")
    def test_initialize_git_captures_output(self, mock_run, mock_project_path):
        """When initializing git, then captures output."""
        # Given
        mock_run.return_value = Mock(returncode=0)

        # When
        initialize_git(mock_project_path)

        # Then
        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is True


@pytest.mark.unit
class TestCopyTemplates:
    """Test template copying behavior."""

    def test_copy_templates_processes_template_files(
        self, tmp_path, sample_template_variables
    ):
        """Given template files, when copying templates, then creates output files."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)

        # Create a template file
        (python_dir / "test.txt.template").write_text("Project: {{PROJECT_NAME}}")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
        )

        # Then
        assert len(created) > 0
        output_file = project_dir / "test.txt"
        assert output_file.exists()
        assert "test-project" in output_file.read_text()

    def test_copy_templates_handles_workflow_paths(
        self, tmp_path, sample_template_variables
    ):
        """Given workflow templates, when copying, then creates .github/workflows structure."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        workflows_dir = python_dir / "workflows"
        workflows_dir.mkdir(parents=True)

        # Create a workflow template
        (workflows_dir / "test.yml.template").write_text("name: Test")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
        )

        # Then
        workflow_file = project_dir / ".github" / "workflows" / "test.yml"
        assert workflow_file.exists()
        assert str(workflow_file) in created

    def test_copy_templates_removes_template_extension(
        self, tmp_path, sample_template_variables
    ):
        """Given .template files, when copying, then removes .template extension."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)

        (python_dir / "Makefile.template").write_text("help:\n\t@echo help")

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
        )

        # Then
        makefile = project_dir / "Makefile"
        assert makefile.exists()
        assert not (project_dir / "Makefile.template").exists()

    def test_copy_templates_returns_empty_for_missing_language(
        self, tmp_path, sample_template_variables
    ):
        """Given non-existent language templates, when copying, then returns empty list."""
        # Given
        templates_root = tmp_path / "templates"
        templates_root.mkdir()

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="nonexistent",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
        )

        # Then
        assert created == []

    @patch("builtins.input", return_value="n")
    def test_copy_templates_prompts_for_overwrite(
        self, mock_input, tmp_path, sample_template_variables
    ):
        """Given existing file and no force, when copying, then prompts for overwrite."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "test.txt.template").write_text("New content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "test.txt").write_text("Old content")

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=False,
        )

        # Then
        mock_input.assert_called_once()
        assert len(created) == 0  # User said no to overwrite

    def test_copy_templates_force_overwrites_existing(
        self, tmp_path, sample_template_variables
    ):
        """Given existing file and force=True, when copying, then overwrites without prompt."""
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)
        (python_dir / "test.txt.template").write_text("New content")

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "test.txt").write_text("Old content")

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
        )

        # Then
        assert len(created) > 0
        assert (project_dir / "test.txt").read_text() == "New content"


@pytest.mark.unit
class TestCreateProjectStructure:
    """Test project structure creation behavior."""

    def test_create_python_project_structure(self, tmp_path):
        """Given Python language, when creating structure, then creates Python directories."""
        # Given
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "python", "test_module", "test-project")

        # Then
        src_dir = project_dir / "src" / "test_module"
        assert src_dir.exists()
        assert (src_dir / "__init__.py").exists()

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

    def test_create_python_project_creates_readme(self, tmp_path):
        """Given Python language, when creating structure, then creates README.md."""
        # Given
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "python", "test_module", "my-project")

        # Then
        readme = project_dir / "README.md"
        assert readme.exists()
        assert "my-project" in readme.read_text()

    def test_create_rust_project_structure(self, tmp_path):
        """Given Rust language, when creating structure, then creates Rust directories."""
        # Given
        project_dir = tmp_path / "rust-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "rust", "test_module", "test-project")

        # Then
        src_dir = project_dir / "src"
        assert src_dir.exists()
        assert (src_dir / "main.rs").exists()
        assert (src_dir / "lib.rs").exists()

    def test_create_rust_project_creates_readme(self, tmp_path):
        """Given Rust language, when creating structure, then creates README.md."""
        # Given
        project_dir = tmp_path / "rust-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "rust", "test_module", "rust-project")

        # Then
        readme = project_dir / "README.md"
        assert readme.exists()
        assert "rust-project" in readme.read_text()

    def test_create_typescript_project_structure(self, tmp_path):
        """Given TypeScript language, when creating structure, then creates TypeScript directories."""
        # Given
        project_dir = tmp_path / "ts-project"
        project_dir.mkdir()

        # When
        create_project_structure(project_dir, "typescript", "test_module", "ts-project")

        # Then
        src_dir = project_dir / "src"
        assert src_dir.exists()
        assert (src_dir / "index.ts").exists()
        assert (src_dir / "App.tsx").exists()

    def test_create_typescript_project_creates_readme(self, tmp_path):
        """Given TypeScript language, when creating structure, then creates README.md."""
        # Given
        project_dir = tmp_path / "ts-project"
        project_dir.mkdir()

        # When
        create_project_structure(
            project_dir, "typescript", "test_module", "my-ts-project"
        )

        # Then
        readme = project_dir / "README.md"
        assert readme.exists()
        assert "my-ts-project" in readme.read_text()

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
        """Given Python language, when creating structure, then __init__.py includes version."""
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
class TestAttuneInitBehavior:
    """BDD-style tests for attune_init workflows."""

    @patch("subprocess.run")
    def test_scenario_initialize_new_project_with_git(self, mock_run, tmp_path):
        """
        Scenario: Initializing a new project with git.

        Given a new project directory
        When I initialize the project
        Then it should create a git repository
        """
        # Given
        project_dir = tmp_path / "new-project"
        project_dir.mkdir()
        mock_run.return_value = Mock(returncode=0)

        # When
        result = initialize_git(project_dir)

        # Then
        assert result is True
        mock_run.assert_called_once_with(
            ["git", "init"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

    def test_scenario_create_complete_python_project(self, tmp_path):
        """
        Scenario: Creating a complete Python project structure.

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

    def test_scenario_copy_and_render_templates(
        self, tmp_path, sample_template_variables
    ):
        """
        Scenario: Copying and rendering project templates.

        Given template files with variables
        When I copy templates to the project
        Then they should be rendered with actual values
        And placed in the correct locations
        """
        # Given
        templates_root = tmp_path / "templates"
        python_dir = templates_root / "python"
        python_dir.mkdir(parents=True)

        (python_dir / "Makefile.template").write_text(
            "# {{PROJECT_NAME}}\nhelp:\n\t@echo {{PROJECT_DESCRIPTION}}"
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # When
        created = copy_templates(
            language="python",
            project_path=project_dir,
            variables=sample_template_variables,
            templates_root=templates_root,
            force=True,
        )

        # Then
        makefile = project_dir / "Makefile"
        assert makefile.exists()
        content = makefile.read_text()
        assert "test-project" in content
        assert "A test project for unit testing" in content


# Import the main function for testing
from attune_init import main


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
        # Given
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
            # When
            main()

            # Then
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
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = []

        with patch("sys.argv", ["attune_init.py", "--path", str(python_project)]):
            # When
            main()

            # Then
            mock_detector.detect_language.assert_called_once()
            mock_copy_templates.assert_called_once()

    @patch("attune_init.ProjectDetector")
    def test_main_exits_when_language_not_detected(
        self, mock_detector_cls, mock_project_path, capsys
    ):
        """Given no language detected and no --lang, when running main, then exits with error."""
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = None
        mock_detector_cls.return_value = mock_detector

        with patch("sys.argv", ["attune_init.py", "--path", str(mock_project_path)]):
            # When/Then
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
        # Given
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
            # When
            main()

            # Then
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
        # Given
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
            # When
            main()

            # Then
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
        # Given
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
            # When
            main()

            # Then
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
        # Given
        mock_detector = Mock()
        mock_detector.detect_language.return_value = "python"
        mock_detector.check_git_initialized.return_value = True
        mock_detector_cls.return_value = mock_detector
        mock_copy_templates.return_value = ["file1", "file2"]

        with patch(
            "sys.argv",
            ["attune_init.py", "--lang", "python", "--path", str(mock_project_path)],
        ):
            # When
            main()

            # Then
            captured = capsys.readouterr()
            assert "Project initialized successfully" in captured.out
            assert "Created 2 files" in captured.out
            assert "Next steps" in captured.out
