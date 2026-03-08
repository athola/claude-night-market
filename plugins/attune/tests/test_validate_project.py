"""Test suite for validate_project module.

Following BDD principles with Given/When/Then structure.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from validate_project import ProjectValidator, ValidationResult, main


@pytest.mark.unit
class TestValidationResultCreation:
    """Test ValidationResult creation behavior."""

    @pytest.mark.parametrize(
        ("name", "passed", "message", "category"),
        [
            ("test-check", True, "Test passed", "test"),
            ("test-check", False, "Test failed", "test"),
            ("git-init", True, "Git ready", "git"),
            ("pyproject", False, "Missing pyproject.toml", "build"),
        ],
        ids=["passed", "failed", "git-pass", "build-fail"],
    )
    def test_create_result_stores_all_attributes(
        self, name, passed, message, category
    ):
        """Given valid parameters, when creating result, then stores all attributes."""
        # When
        result = ValidationResult(name, passed, message, category)

        # Then
        assert result.name == name
        assert result.passed is passed
        assert result.message == message
        assert result.category == category


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

    @pytest.mark.parametrize(
        ("fixture_name", "language", "result_name"),
        [
            ("rust_project", "rust", "cargo-toml"),
            ("typescript_project", "typescript", "package-json"),
            ("typescript_project", "typescript", "tsconfig"),
        ],
        ids=["rust-cargo", "ts-package-json", "ts-tsconfig"],
    )
    def test_validate_build_config_present(
        self, fixture_name, language, result_name, request
    ):
        """Given a project with its config file, when validating build, then passes."""
        # Given
        project = request.getfixturevalue(fixture_name)
        validator = ProjectValidator(project)

        # When
        validator.validate_build_config(language)

        # Then
        matches = [r for r in validator.results if r.name == result_name]
        assert len(matches) == 1
        assert matches[0].passed is True

    @pytest.mark.parametrize(
        ("language", "result_name"),
        [
            ("rust", "cargo-toml"),
            ("typescript", "package-json"),
        ],
        ids=["rust-missing", "ts-missing"],
    )
    def test_validate_build_config_missing(
        self, tmp_path, language, result_name
    ):
        """Given a project without its config file, when validating build, then fails."""
        # Given
        project_dir = tmp_path / f"{language}-no-config"
        project_dir.mkdir()

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_build_config(language)

        # Then
        matches = [r for r in validator.results if r.name == result_name]
        assert len(matches) == 1
        assert matches[0].passed is False

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

    @pytest.mark.parametrize(
        ("language", "workflow_files", "expected_pass_names"),
        [
            ("rust", ["ci.yml"], ["workflow-ci.yml"]),
            (
                "typescript",
                ["test.yml", "lint.yml", "build.yml"],
                ["workflow-test.yml", "workflow-lint.yml", "workflow-build.yml"],
            ),
        ],
        ids=["rust-ci", "typescript-workflows"],
    )
    def test_validate_workflows_present_parametrized(
        self, tmp_path, language, workflow_files, expected_pass_names
    ):
        """Given a project with required workflows, when validating CI/CD, then passes."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        for wf in workflow_files:
            (workflows_dir / wf).write_text(f"name: {wf}\n")

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd(language)

        # Then
        for name in expected_pass_names:
            matches = [r for r in validator.results if r.name == name]
            assert len(matches) == 1, f"Expected result for {name}"
            assert matches[0].passed is True


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
        """Scenario: Validating a complete Python project.

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
        """Scenario: Validating a minimal project.

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


@pytest.mark.unit
class TestPrintReport:
    """Test print_report output covers all categories and score."""

    def test_print_report_shows_score_and_categories(
        self, python_project, capsys
    ):
        """Given results, when printing report, then includes score and category headers."""
        # Given
        (python_project / ".git").mkdir()
        (python_project / ".gitignore").write_text("*.pyc\n")
        (python_project / "Makefile").write_text("help:\n\t@echo help\n")
        validator = ProjectValidator(python_project)
        validator.run_validation("python")

        # When
        validator.print_report()

        # Then
        captured = capsys.readouterr().out
        assert "Project Validation Report" in captured
        assert "Score:" in captured
        assert "Git Configuration" in captured
        assert "Build Configuration" in captured

    def test_print_report_shows_recommendations_on_failures(
        self, mock_project_path, capsys
    ):
        """Given failed checks, when printing report, then shows recommendations."""
        # Given
        validator = ProjectValidator(mock_project_path)
        validator.results = [
            ValidationResult("git-init", False, "Git not initialized", "git"),
        ]

        # When
        validator.print_report()

        # Then
        captured = capsys.readouterr().out
        assert "Recommendations:" in captured
        assert "Git not initialized" in captured

    def test_print_report_shows_all_passed_when_no_failures(
        self, mock_project_path, capsys
    ):
        """Given all passed checks, when printing report, then shows all-passed message."""
        # Given
        validator = ProjectValidator(mock_project_path)
        validator.results = [
            ValidationResult("readme", True, "README.md present", "structure"),
        ]

        # When
        validator.print_report()

        # Then
        captured = capsys.readouterr().out
        assert "All checks passed" in captured


@pytest.mark.unit
class TestMainCLI:
    """Test the validate_project main() entry point."""

    def test_main_with_strict_flag_exits_on_failure(
        self, python_project
    ):
        """Given --strict and failing checks, when running main, then exits with 1."""
        with patch(
            "sys.argv",
            [
                "validate_project.py",
                "--path",
                str(python_project),
                "--lang",
                "python",
                "--strict",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code in (1, 2)

    def test_main_with_verbose_flag(self, python_project):
        """Given --verbose, when running main, then exits without error."""
        (python_project / ".git").mkdir()
        (python_project / ".gitignore").write_text("*.pyc\n")
        (python_project / "Makefile").write_text("help:\n\t@echo help\n")
        (python_project / ".pre-commit-config.yaml").write_text("repos: []\n")
        (python_project / "tests").mkdir()
        (python_project / "README.md").write_text("# Test\n")
        pyproject = python_project / "pyproject.toml"
        pyproject.write_text(
            "[project]\nname = 'test'\n\n[tool.mypy]\npython_version = '3.10'\n"
        )
        workflows = python_project / ".github" / "workflows"
        workflows.mkdir(parents=True)
        for wf in ["test.yml", "lint.yml", "typecheck.yml"]:
            (workflows / wf).write_text(f"name: {wf}\n")

        with patch(
            "sys.argv",
            [
                "validate_project.py",
                "--path",
                str(python_project),
                "--lang",
                "python",
                "-v",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_exits_with_normal_exit_code(
        self, mock_project_path
    ):
        """Given a project, when running main without --strict, then exits with validator code."""
        with patch(
            "sys.argv",
            [
                "validate_project.py",
                "--path",
                str(mock_project_path),
                "--lang",
                "python",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with 2 (critical: missing pyproject)
            assert exc_info.value.code == 2


@pytest.mark.unit
class TestCICDUnknownLanguage:
    """Test CI/CD validation with unknown language."""

    def test_validate_ci_cd_unknown_language_no_workflows(
        self, tmp_path
    ):
        """Given an unknown language, when validating CI/CD, then no workflow checks added."""
        # Given
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        validator = ProjectValidator(project_dir)

        # When
        validator.validate_ci_cd("go")

        # Then
        workflow_results = [
            r for r in validator.results if "workflow-" in r.name
        ]
        assert len(workflow_results) == 0
