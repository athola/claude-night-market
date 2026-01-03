"""Test suite for validate_project module.

Following BDD principles with Given/When/Then structure.
"""

from pathlib import Path

import pytest
from validate_project import ProjectValidator, ValidationResult


@pytest.mark.unit
class TestValidationResultCreation:
    """Test ValidationResult creation behavior."""

    def test_create_passed_result(self):
        """Given valid parameters, when creating passed result, then stores all attributes."""
        # When
        result = ValidationResult("test-check", True, "Test passed", "test")

        # Then
        assert result.name == "test-check"
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.category == "test"

    def test_create_failed_result(self):
        """Given valid parameters, when creating failed result, then stores all attributes."""
        # When
        result = ValidationResult("test-check", False, "Test failed", "test")

        # Then
        assert result.name == "test-check"
        assert result.passed is False
        assert result.message == "Test failed"


@pytest.mark.unit
class TestProjectValidatorInitialization:
    """Test ProjectValidator initialization behavior."""

    def test_initialization_with_path(self, mock_project_path):
        """Given a project path, when initializing validator, then creates instance."""
        # When
        validator = ProjectValidator(mock_project_path)

        # Then
        assert validator.project_path == mock_project_path
        assert validator.results == []

    def test_initialization_creates_detector(self, mock_project_path):
        """Given a project path, when initializing validator, then creates detector."""
        # When
        validator = ProjectValidator(mock_project_path)

        # Then
        assert validator.detector is not None
        assert validator.detector.project_path == mock_project_path


@pytest.mark.unit
class TestGitValidation:
    """Test git configuration validation behavior."""

    def test_validate_git_initialized(self, git_project):
        """Given a git project, when validating git, then passes git-init check."""
        # Given
        validator = ProjectValidator(git_project)

        # When
        validator.validate_git()

        # Then
        git_init_results = [r for r in validator.results if r.name == "git-init"]
        assert len(git_init_results) == 1
        assert git_init_results[0].passed is True

    def test_validate_git_not_initialized(self, mock_project_path):
        """Given a non-git project, when validating git, then fails git-init check."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_git()

        # Then
        git_init_results = [r for r in validator.results if r.name == "git-init"]
        assert len(git_init_results) == 1
        assert git_init_results[0].passed is False

    def test_validate_gitignore_exists(self, tmp_path):
        """Given a project with .gitignore, when validating git, then passes gitignore check."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_git()

        # Then
        gitignore_results = [r for r in validator.results if r.name == "gitignore"]
        assert len(gitignore_results) == 1
        assert gitignore_results[0].passed is True
        assert "patterns" in gitignore_results[0].message

    def test_validate_gitignore_missing(self, mock_project_path):
        """Given a project without .gitignore, when validating git, then fails gitignore check."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_git()

        # Then
        gitignore_results = [r for r in validator.results if r.name == "gitignore"]
        assert len(gitignore_results) == 1
        assert gitignore_results[0].passed is False


@pytest.mark.unit
class TestBuildConfigValidation:
    """Test build configuration validation behavior."""

    def test_validate_python_pyproject_exists(self, python_project):
        """Given a Python project with pyproject.toml, when validating build, then passes."""
        # Given
        validator = ProjectValidator(python_project)

        # When
        validator.validate_build_config("python")

        # Then
        pyproject_results = [r for r in validator.results if r.name == "pyproject"]
        assert len(pyproject_results) == 1
        assert pyproject_results[0].passed is True

    def test_validate_python_pyproject_missing(self, tmp_path):
        """Given a Python project without pyproject.toml, when validating build, then fails."""
        # Given
        project_dir = tmp_path / "python-no-config"
        project_dir.mkdir()

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_build_config("python")

        # Then
        pyproject_results = [r for r in validator.results if r.name == "pyproject"]
        assert len(pyproject_results) == 1
        assert pyproject_results[0].passed is False

    def test_validate_rust_cargo_toml_exists(self, rust_project):
        """Given a Rust project with Cargo.toml, when validating build, then passes."""
        # Given
        validator = ProjectValidator(rust_project)

        # When
        validator.validate_build_config("rust")

        # Then
        cargo_results = [r for r in validator.results if r.name == "cargo-toml"]
        assert len(cargo_results) == 1
        assert cargo_results[0].passed is True

    def test_validate_rust_cargo_toml_missing(self, tmp_path):
        """Given a Rust project without Cargo.toml, when validating build, then fails."""
        # Given
        project_dir = tmp_path / "rust-no-config"
        project_dir.mkdir()

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_build_config("rust")

        # Then
        cargo_results = [r for r in validator.results if r.name == "cargo-toml"]
        assert len(cargo_results) == 1
        assert cargo_results[0].passed is False

    def test_validate_typescript_package_json_exists(self, typescript_project):
        """Given a TypeScript project with package.json, when validating build, then passes."""
        # Given
        validator = ProjectValidator(typescript_project)

        # When
        validator.validate_build_config("typescript")

        # Then
        package_results = [r for r in validator.results if r.name == "package-json"]
        assert len(package_results) == 1
        assert package_results[0].passed is True

    def test_validate_typescript_tsconfig_exists(self, typescript_project):
        """Given a TypeScript project with tsconfig.json, when validating build, then passes."""
        # Given
        validator = ProjectValidator(typescript_project)

        # When
        validator.validate_build_config("typescript")

        # Then
        tsconfig_results = [r for r in validator.results if r.name == "tsconfig"]
        assert len(tsconfig_results) == 1
        assert tsconfig_results[0].passed is True

    def test_validate_makefile_exists(self, tmp_path):
        """Given a project with Makefile, when validating build, then passes and counts targets."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "Makefile").write_text("""help:
\t@echo help

test:
\tpytest

build:
\tmake install
""")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_build_config("python")

        # Then
        makefile_results = [r for r in validator.results if r.name == "makefile"]
        assert len(makefile_results) == 1
        assert makefile_results[0].passed is True
        assert "targets" in makefile_results[0].message

    def test_validate_makefile_missing(self, mock_project_path):
        """Given a project without Makefile, when validating build, then fails."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_build_config("python")

        # Then
        makefile_results = [r for r in validator.results if r.name == "makefile"]
        assert len(makefile_results) == 1
        assert makefile_results[0].passed is False


@pytest.mark.unit
class TestCodeQualityValidation:
    """Test code quality tools validation behavior."""

    def test_validate_precommit_exists(self, tmp_path):
        """Given a project with pre-commit config, when validating quality, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".pre-commit-config.yaml").write_text("""repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
""")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_code_quality("python")

        # Then
        precommit_results = [r for r in validator.results if r.name == "pre-commit"]
        assert len(precommit_results) == 1
        assert precommit_results[0].passed is True
        assert "hooks" in precommit_results[0].message

    def test_validate_precommit_missing(self, mock_project_path):
        """Given a project without pre-commit config, when validating quality, then fails."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_code_quality("python")

        # Then
        precommit_results = [r for r in validator.results if r.name == "pre-commit"]
        assert len(precommit_results) == 1
        assert precommit_results[0].passed is False

    def test_validate_python_type_checking_configured(self, tmp_path):
        """Given a Python project with mypy config, when validating quality, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
""")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_code_quality("python")

        # Then
        typecheck_results = [r for r in validator.results if r.name == "type-checking"]
        assert len(typecheck_results) == 1
        assert typecheck_results[0].passed is True

    def test_validate_python_type_checking_missing(self, python_project):
        """Given a Python project without mypy config, when validating quality, then fails."""
        # Given - python_project has pyproject.toml but no mypy config
        validator = ProjectValidator(python_project)

        # When
        validator.validate_code_quality("python")

        # Then
        typecheck_results = [r for r in validator.results if r.name == "type-checking"]
        assert len(typecheck_results) == 1
        assert typecheck_results[0].passed is False


@pytest.mark.unit
class TestCICDValidation:
    """Test CI/CD workflow validation behavior."""

    def test_validate_workflows_directory_exists(self, tmp_path):
        """Given a project with .github/workflows/, when validating CI/CD, then checks workflows."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "test.yml").write_text("name: Test\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd("python")

        # Then
        # Should have results for required workflows
        workflow_results = [r for r in validator.results if "workflow-" in r.name]
        assert len(workflow_results) > 0

    def test_validate_workflows_directory_missing(self, mock_project_path):
        """Given a project without workflows directory, when validating CI/CD, then fails."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_ci_cd("python")

        # Then
        workflows_dir_results = [
            r for r in validator.results if r.name == "workflows-dir"
        ]
        assert len(workflows_dir_results) == 1
        assert workflows_dir_results[0].passed is False

    def test_validate_python_workflows_present(self, tmp_path):
        """Given a Python project with all workflows, when validating CI/CD, then all pass."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        for workflow in ["test.yml", "lint.yml", "typecheck.yml"]:
            (workflows_dir / workflow).write_text(f"name: {workflow}\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd("python")

        # Then
        test_result = [r for r in validator.results if r.name == "workflow-test.yml"]
        lint_result = [r for r in validator.results if r.name == "workflow-lint.yml"]
        typecheck_result = [
            r for r in validator.results if r.name == "workflow-typecheck.yml"
        ]

        assert all(
            len(r) == 1 and r[0].passed
            for r in [test_result, lint_result, typecheck_result]
        )

    def test_validate_rust_workflows_present(self, tmp_path):
        """Given a Rust project with ci.yml, when validating CI/CD, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd("rust")

        # Then
        ci_result = [r for r in validator.results if r.name == "workflow-ci.yml"]
        assert len(ci_result) == 1
        assert ci_result[0].passed is True

    def test_validate_typescript_workflows_present(self, tmp_path):
        """Given a TypeScript project with workflows, when validating CI/CD, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        for workflow in ["test.yml", "lint.yml", "build.yml"]:
            (workflows_dir / workflow).write_text(f"name: {workflow}\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd("typescript")

        # Then
        workflow_results = [r for r in validator.results if "workflow-" in r.name]
        assert all(r.passed for r in workflow_results)


@pytest.mark.unit
class TestStructureValidation:
    """Test project structure validation behavior."""

    def test_validate_src_directory_exists(self, python_project):
        """Given a project with src/ directory, when validating structure, then passes."""
        # Given
        validator = ProjectValidator(python_project)

        # When
        validator.validate_structure("python")

        # Then
        src_results = [r for r in validator.results if r.name == "src-dir"]
        assert len(src_results) == 1
        assert src_results[0].passed is True

    def test_validate_src_directory_missing(self, mock_project_path):
        """Given a project without src/ directory, when validating structure, then fails."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_structure("python")

        # Then
        src_results = [r for r in validator.results if r.name == "src-dir"]
        assert len(src_results) == 1
        assert src_results[0].passed is False

    def test_validate_tests_directory_exists(self, tmp_path):
        """Given a project with tests/ directory, when validating structure, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "tests").mkdir()

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_structure("python")

        # Then
        test_results = [r for r in validator.results if r.name == "test-dir"]
        assert len(test_results) == 1
        assert test_results[0].passed is True

    def test_validate_test_directory_exists(self, tmp_path):
        """Given a project with test/ directory (singular), when validating structure, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "test").mkdir()

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_structure("python")

        # Then
        test_results = [r for r in validator.results if r.name == "test-dir"]
        assert len(test_results) == 1
        assert test_results[0].passed is True

    def test_validate_readme_exists(self, tmp_path):
        """Given a project with README.md, when validating structure, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("# Project\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_structure("python")

        # Then
        readme_results = [r for r in validator.results if r.name == "readme"]
        assert len(readme_results) == 1
        assert readme_results[0].passed is True

    def test_validate_readme_missing(self, mock_project_path):
        """Given a project without README.md, when validating structure, then fails."""
        # Given
        validator = ProjectValidator(mock_project_path)

        # When
        validator.validate_structure("python")

        # Then
        readme_results = [r for r in validator.results if r.name == "readme"]
        assert len(readme_results) == 1
        assert readme_results[0].passed is False


@pytest.mark.unit
class TestRunValidation:
    """Test full validation run behavior."""

    def test_run_validation_with_language(self, python_project):
        """Given a language parameter, when running validation, then uses provided language."""
        # Given
        validator = ProjectValidator(python_project)

        # When
        results = validator.run_validation("python")

        # Then
        assert len(results) > 0
        assert validator.results == results

    def test_run_validation_auto_detect_language(self, python_project):
        """Given no language parameter, when running validation, then auto-detects language."""
        # Given
        validator = ProjectValidator(python_project)

        # When
        results = validator.run_validation()

        # Then
        assert len(results) > 0

    def test_run_validation_all_categories(self, python_project):
        """Given a project, when running validation, then checks all categories."""
        # Given
        validator = ProjectValidator(python_project)

        # When
        validator.run_validation("python")

        # Then
        categories = {r.category for r in validator.results}
        expected_categories = {"git", "build", "quality", "ci-cd", "structure"}
        assert expected_categories.issubset(categories)


@pytest.mark.unit
class TestGetExitCode:
    """Test exit code generation behavior."""

    def test_get_exit_code_all_passed(self, python_project):
        """Given all checks passed, when getting exit code, then returns 0."""
        # Given
        validator = ProjectValidator(python_project)
        # Add only passing results
        validator.results = [ValidationResult("test", True, "Passed", "test")]

        # When
        exit_code = validator.get_exit_code()

        # Then
        assert exit_code == 0

    def test_get_exit_code_non_critical_failures(self):
        """Given non-critical failures, when getting exit code, then returns 1."""
        # Given
        validator = ProjectValidator(Path("/tmp"))
        validator.results = [
            ValidationResult("pre-commit", False, "Failed", "quality"),
            ValidationResult("readme", True, "Passed", "structure"),
        ]

        # When
        exit_code = validator.get_exit_code()

        # Then
        assert exit_code == 1

    def test_get_exit_code_critical_failures(self):
        """Given critical failures, when getting exit code, then returns 2."""
        # Given
        validator = ProjectValidator(Path("/tmp"))
        validator.results = [
            ValidationResult("git-init", False, "Failed", "git"),
            ValidationResult("pyproject", False, "Failed", "build"),
        ]

        # When
        exit_code = validator.get_exit_code()

        # Then
        assert exit_code == 2


@pytest.mark.bdd
class TestProjectValidatorBehavior:
    """BDD-style tests for ProjectValidator workflows."""

    def test_scenario_validate_complete_python_project(self, tmp_path):
        """
        Scenario: Validating a complete Python project.

        Given a fully configured Python project
        When I run validation
        Then all checks should pass
        And the exit code should be 0
        """
        # Given
        project_dir = tmp_path / "complete-project"
        project_dir.mkdir()

        # Create all required files and directories
        (project_dir / ".git").mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test"

[tool.mypy]
python_version = "3.10"
""")
        (project_dir / ".gitignore").write_text("__pycache__/\n")
        (project_dir / "Makefile").write_text("help:\n\t@echo help\n")
        (project_dir / ".pre-commit-config.yaml").write_text("repos: []\n")
        (project_dir / "README.md").write_text("# Project\n")

        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        for workflow in ["test.yml", "lint.yml", "typecheck.yml"]:
            (workflows_dir / workflow).write_text(f"name: {workflow}\n")

        # When
        validator = ProjectValidator(project_dir)
        validator.run_validation("python")

        # Then
        failed = [r for r in validator.results if not r.passed]
        assert len(failed) == 0
        assert validator.get_exit_code() == 0

    def test_scenario_validate_minimal_project(self, tmp_path):
        """
        Scenario: Validating a minimal project.

        Given a minimal project with only basic files
        When I run validation
        Then it should identify missing configurations
        And provide recommendations
        """
        # Given
        project_dir = tmp_path / "minimal-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # When
        validator = ProjectValidator(project_dir)
        validator.run_validation("python")

        # Then
        failed = [r for r in validator.results if not r.passed]
        assert len(failed) > 0
        assert any("git" in r.message.lower() for r in failed)
        assert any("makefile" in r.message.lower() for r in failed)
