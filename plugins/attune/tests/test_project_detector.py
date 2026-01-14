"""Test suite for project_detector module.

Following BDD principles with Given/When/Then structure.
"""

from pathlib import Path

import pytest
from project_detector import ProjectDetector


@pytest.mark.unit
class TestProjectDetectorInitialization:
    """Test ProjectDetector initialization behavior."""

    def test_initialization_with_valid_path(self, mock_project_path):
        """Given a valid project path, when initialized, then creates detector instance."""
        # When
        detector = ProjectDetector(mock_project_path)

        # Then
        assert detector.project_path == Path(mock_project_path)
        assert isinstance(detector.project_path, Path)

    def test_initialization_converts_string_to_path(self, tmp_path):
        """Given a string path, when initialized, then converts to Path object."""
        # Given
        path_str = str(tmp_path)

        # When
        detector = ProjectDetector(path_str)

        # Then
        assert isinstance(detector.project_path, Path)
        assert detector.project_path == Path(path_str)


@pytest.mark.unit
class TestLanguageDetection:
    """Test language detection behavior."""

    def test_detect_python_from_pyproject_toml(self, python_project):
        """Given a project with pyproject.toml, when detecting language, then returns 'python'."""
        # Given
        detector = ProjectDetector(python_project)

        # When
        language = detector.detect_language()

        # Then
        assert language == "python"

    def test_detect_python_from_setup_py(self, tmp_path):
        """Given a project with setup.py, when detecting language, then returns 'python'."""
        # Given
        project_dir = tmp_path / "python-setup"
        project_dir.mkdir()
        (project_dir / "setup.py").write_text("from setuptools import setup\n")

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "python"

    def test_detect_python_from_requirements_txt(self, tmp_path):
        """Given a project with requirements.txt, when detecting language, then returns 'python'."""
        # Given
        project_dir = tmp_path / "python-requirements"
        project_dir.mkdir()
        (project_dir / "requirements.txt").write_text("pytest>=8.0\n")

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "python"

    def test_detect_rust_from_cargo_toml(self, rust_project):
        """Given a project with Cargo.toml, when detecting language, then returns 'rust'."""
        # Given
        detector = ProjectDetector(rust_project)

        # When
        language = detector.detect_language()

        # Then
        assert language == "rust"

    def test_detect_typescript_from_tsconfig(self, typescript_project):
        """Given a project with tsconfig.json, when detecting language, then returns 'typescript'."""
        # Given
        detector = ProjectDetector(typescript_project)

        # When
        language = detector.detect_language()

        # Then
        assert language == "typescript"

    def test_detect_python_from_source_files(self, tmp_path):
        """Given a project with .py files in src/, when detecting language, then returns 'python'."""
        # Given
        project_dir = tmp_path / "python-src"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')\n")

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "python"

    def test_detect_rust_from_source_files(self, tmp_path):
        """Given a project with .rs files in src/, when detecting language, then returns 'rust'."""
        # Given
        project_dir = tmp_path / "rust-src"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("fn main() {}\n")

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "rust"

    def test_detect_typescript_from_source_files(self, tmp_path):
        """Given a project with .ts files in src/, when detecting language, then returns 'typescript'."""
        # Given
        project_dir = tmp_path / "ts-src"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text('export const hello = "world";\n')

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "typescript"

    def test_detect_typescript_from_tsx_files(self, tmp_path):
        """Given a project with .tsx files, when detecting language, then returns 'typescript'."""
        # Given
        project_dir = tmp_path / "tsx-src"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text('import React from "react";\n')

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "typescript"

    def test_returns_none_for_unknown_project(self, tmp_path):
        """Given an empty project, when detecting language, then returns None."""
        # Given
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        detector = ProjectDetector(empty_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language is None

    def test_python_takes_precedence_over_typescript(self, tmp_path):
        """Given a project with both Python and TS files, when detecting, then Python takes precedence."""
        # Given
        project_dir = tmp_path / "mixed"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\n")
        (project_dir / "package.json").write_text("{}\n")

        detector = ProjectDetector(project_dir)

        # When
        language = detector.detect_language()

        # Then
        assert language == "python"


@pytest.mark.unit
class TestGitDetection:
    """Test git repository detection behavior."""

    def test_detects_initialized_git_repo(self, git_project):
        """Given a project with .git directory, when checking git, then returns True."""
        # Given
        detector = ProjectDetector(git_project)

        # When
        is_git = detector.check_git_initialized()

        # Then
        assert is_git is True

    def test_detects_no_git_repo(self, mock_project_path):
        """Given a project without .git directory, when checking git, then returns False."""
        # Given
        detector = ProjectDetector(mock_project_path)

        # When
        is_git = detector.check_git_initialized()

        # Then
        assert is_git is False


@pytest.mark.unit
class TestExistingFilesCheck:
    """Test existing configuration files detection behavior."""

    def test_check_existing_files_all_present(self, python_project):
        """Given a project with some config files, when checking, then returns correct status."""
        # Given
        detector = ProjectDetector(python_project)

        # When
        existing = detector.check_existing_files()

        # Then
        assert isinstance(existing, dict)
        assert "pyproject.toml" in existing
        assert existing["pyproject.toml"] is True

    def test_check_existing_files_returns_false_for_missing(self, mock_project_path):
        """Given a project without config files, when checking, then returns all False."""
        # Given
        detector = ProjectDetector(mock_project_path)

        # When
        existing = detector.check_existing_files()

        # Then
        assert all(status is False for status in existing.values())

    def test_check_existing_files_includes_standard_files(self, mock_project_path):
        """Given any project, when checking files, then includes standard configuration files."""
        # Given
        detector = ProjectDetector(mock_project_path)

        # When
        existing = detector.check_existing_files()

        # Then
        expected_files = [
            ".gitignore",
            "Makefile",
            ".pre-commit-config.yaml",
            "pyproject.toml",
            "Cargo.toml",
            "package.json",
        ]
        for file in expected_files:
            assert file in existing

    def test_check_existing_files_includes_workflows(self, mock_project_path):
        """Given any project, when checking files, then includes workflow files."""
        # Given
        detector = ProjectDetector(mock_project_path)

        # When
        existing = detector.check_existing_files()

        # Then
        workflow_files = [
            ".github/workflows/test.yml",
            ".github/workflows/lint.yml",
            ".github/workflows/typecheck.yml",
        ]
        for file in workflow_files:
            assert file in existing


@pytest.mark.unit
class TestProjectInfo:
    """Verify project information gathering."""

    def test_get_project_info_returns_all_fields(self, python_project):
        """Given a Python project, when getting info, then returns all project fields."""
        # Given
        detector = ProjectDetector(python_project)

        # When
        info = detector.get_project_info()

        # Then
        assert "path" in info
        assert "language" in info
        assert "git_initialized" in info
        assert "existing_files" in info

    def test_get_project_info_path_is_string(self, python_project):
        """Given a project, when getting info, then path is returned as string."""
        # Given
        detector = ProjectDetector(python_project)

        # When
        info = detector.get_project_info()

        # Then
        assert isinstance(info["path"], str)
        assert info["path"] == str(python_project)

    def test_get_project_info_language_detected(self, rust_project):
        """Given a Rust project, when getting info, then language is correctly detected."""
        # Given
        detector = ProjectDetector(rust_project)

        # When
        info = detector.get_project_info()

        # Then
        assert info["language"] == "rust"

    def test_get_project_info_git_status(self, git_project):
        """Given a git project, when getting info, then git status is correct."""
        # Given
        detector = ProjectDetector(git_project)

        # When
        info = detector.get_project_info()

        # Then
        assert info["git_initialized"] is True

    def test_get_project_info_existing_files_dict(self, python_project):
        """Given a project, when getting info, then existing_files is a dictionary."""
        # Given
        detector = ProjectDetector(python_project)

        # When
        info = detector.get_project_info()

        # Then
        assert isinstance(info["existing_files"], dict)
        assert len(info["existing_files"]) > 0


@pytest.mark.unit
class TestMissingConfigurations:
    """Test missing configuration detection behavior."""

    def test_get_missing_configurations_python(self, tmp_path):
        """Given a Python project without configs, when checking missing, then returns Python files."""
        # Given
        project_dir = tmp_path / "python-minimal"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\n")
        detector = ProjectDetector(project_dir)

        # When
        missing = detector.get_missing_configurations("python")

        # Then
        assert ".gitignore" in missing
        assert "Makefile" in missing
        assert ".pre-commit-config.yaml" in missing
        assert ".github/workflows/test.yml" in missing

    def test_get_missing_configurations_rust(self, tmp_path):
        """Given a Rust project without configs, when checking missing, then returns Rust files."""
        # Given
        project_dir = tmp_path / "rust-minimal"
        project_dir.mkdir()
        (project_dir / "Cargo.toml").write_text("[package]\n")
        detector = ProjectDetector(project_dir)

        # When
        missing = detector.get_missing_configurations("rust")

        # Then
        assert ".gitignore" in missing
        assert "Makefile" in missing
        assert ".github/workflows/ci.yml" in missing

    def test_get_missing_configurations_typescript(self, tmp_path):
        """Given a TypeScript project without configs, when checking missing, then returns TS files."""
        # Given
        project_dir = tmp_path / "ts-minimal"
        project_dir.mkdir()
        (project_dir / "package.json").write_text("{}\n")
        detector = ProjectDetector(project_dir)

        # When
        missing = detector.get_missing_configurations("typescript")

        # Then
        assert ".gitignore" in missing
        assert "package.json" not in missing  # Already exists
        assert "tsconfig.json" in missing

    def test_get_missing_configurations_excludes_existing(self, python_project):
        """Given a project with some configs, when checking missing, then excludes existing files."""
        # Given
        detector = ProjectDetector(python_project)
        # Create Makefile
        (python_project / "Makefile").write_text("help:\n\t@echo help\n")

        # When
        missing = detector.get_missing_configurations("python")

        # Then
        assert "pyproject.toml" not in missing  # Already exists
        assert "Makefile" not in missing  # We just created it

    def test_get_missing_configurations_unknown_language(self, mock_project_path):
        """Given an unknown language, when checking missing, then returns empty list."""
        # Given
        detector = ProjectDetector(mock_project_path)

        # When
        missing = detector.get_missing_configurations("unknown")

        # Then
        assert missing == []


@pytest.mark.bdd
class TestProjectDetectorBehavior:
    """BDD-style tests for ProjectDetector workflows."""

    def test_scenario_new_python_project(self, tmp_path):
        """Scenario: Detecting a new Python project.

        Given a directory with a pyproject.toml file
        When I create a ProjectDetector
        Then it should detect the language as Python
        And it should detect git as not initialized
        And it should list missing configuration files
        """
        # Given
        project_dir = tmp_path / "new-python-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # When
        detector = ProjectDetector(project_dir)
        info = detector.get_project_info()
        missing = detector.get_missing_configurations("python")

        # Then
        assert info["language"] == "python"
        assert info["git_initialized"] is False
        assert len(missing) > 0
        assert ".gitignore" in missing

    def test_scenario_fully_configured_project(self, tmp_path):
        """Scenario: Detecting a fully configured project.

        Given a project with all configuration files
        When I check for missing configurations
        Then it should return an empty list
        """
        # Given
        project_dir = tmp_path / "complete-project"
        project_dir.mkdir()

        # Create all required files
        (project_dir / "pyproject.toml").write_text("[project]\n")
        (project_dir / ".gitignore").write_text("__pycache__/\n")
        (project_dir / "Makefile").write_text("help:\n")
        (project_dir / ".pre-commit-config.yaml").write_text("repos: []\n")

        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text("name: Test\n")
        (workflows_dir / "lint.yml").write_text("name: Lint\n")
        (workflows_dir / "typecheck.yml").write_text("name: TypeCheck\n")

        detector = ProjectDetector(project_dir)

        # When
        missing = detector.get_missing_configurations("python")

        # Then
        assert missing == []
