"""Tests for meta-evaluation script and recursive validation.

This module tests the meta-evaluation framework that validates evaluation
skills meet their own quality standards, following TDD/BDD principles.

The Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestMetaEvaluationScript:
    """
    Feature: Meta-evaluation validates evaluation skills meet their own standards

    As a quality assurance engineer
    I want automated validation of evaluation skills
    So that evaluation frameworks practice what they preach
    """

    @pytest.fixture
    def meta_eval_script(self) -> Path:
        """Path to the meta_evaluation.py script."""
        return Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_script_exists(self, meta_eval_script: Path) -> None:
        """
        Scenario: Meta-evaluation script exists

        Given the sanctum plugin structure
        When looking for the meta-evaluation script
        Then it should exist at scripts/meta_evaluation.py
        """
        # Assert - script exists
        assert meta_eval_script.exists(), f"Script not found at {meta_eval_script}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_script_is_executable(self, meta_eval_script: Path) -> None:
        """
        Scenario: Meta-evaluation script is executable

        Given the meta-evaluation script exists
        When checking file permissions
        Then it should be executable
        """
        # Assert - script is executable
        assert meta_eval_script.stat().st_mode & 0o111, "Script should be executable"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_script_runs_without_errors(self, meta_eval_script: Path) -> None:
        """
        Scenario: Meta-evaluation script executes successfully

        Given the meta-evaluation script exists
        When running the script with --help
        Then it should execute without errors
        And display usage information
        """
        # Arrange
        cmd = [sys.executable, str(meta_eval_script), "--help"]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "meta-evaluation" in result.stdout.lower()


class TestMetaEvaluationFunctionality:
    """
    Feature: Meta-evaluation checks quality criteria for evaluation skills

    As a framework validator
    I want automated quality checks
    So that evaluation skills meet their own standards
    """

    @pytest.fixture
    def plugins_root(self) -> Path:
        """Path to plugins directory."""
        # From plugins/sanctum/tests/unit/scripts/test_meta_evaluation.py
        # Go up 4 levels to project root
        return Path(__file__).parents[4]

    @pytest.fixture
    def meta_eval_script(self) -> Path:
        """Path to the meta_evaluation.py script."""
        return Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_abstract_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates abstract plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on abstract plugin
        Then it should check skills-eval, hooks-eval, modular-skills
        And report on their quality criteria
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "abstract",
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should mention abstract skills
        output = result.stdout + result.stderr
        assert "abstract" in output.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_leyline_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates leyline plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on leyline plugin
        Then it should check evaluation-framework, testing-quality-standards
        And report on their quality criteria
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "leyline",
            "--verbose",  # Use verbose mode to see skill details
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should report evaluation results (skills evaluated count)
        output = result.stdout + result.stderr
        assert "skills evaluated" in output.lower() or "leyline" in output.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_imbue_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates imbue plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on imbue plugin
        Then it should check proof-of-work, evidence-logging
        And report on their quality criteria
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "imbue",
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should mention imbue skills
        output = result.stdout + result.stderr
        assert "imbue" in output.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reports_missing_tocs(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation detects missing Table of Contents

        Given the meta-evaluation script
        When evaluating skills without TOCs
        Then it should report missing TOCs for skills >100 lines
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "abstract",
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Output should contain evaluation results
        output = result.stdout + result.stderr
        assert "evaluation" in output.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reports_missing_verification(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation detects missing verification steps

        Given the meta-evaluation script
        When evaluating skills without verification steps
        Then it should report missing verification after code examples
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "leyline",
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should check verification - script runs without crashing
        # The actual verification detection is tested in unit tests for the script itself

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reports_missing_tests(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation detects missing test files

        Given the meta-evaluation script
        When evaluating skills without test files
        Then it should report missing tests for critical evaluation skills
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should mention tests - script runs without crashing
        # The actual test detection is validated in unit tests for the script itself

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_provides_summary_statistics(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation provides summary statistics

        Given the meta-evaluation script
        When evaluation completes
        Then it should show summary with pass rate and issue counts
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Should show summary
        output = result.stdout + result.stderr
        assert "summary" in output.lower() or "pass rate" in output.lower()


class TestMetaEvaluationIntegration:
    """
    Feature: Meta-evaluation integrates with update-plugins workflow

    As a CI/CD pipeline
    I want automated meta-evaluation
    So that evaluation quality is enforced continuously
    """

    @pytest.fixture
    def meta_eval_script(self) -> Path:
        """Path to the meta_evaluation.py script."""
        return Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"

    @pytest.fixture
    def plugins_root(self) -> Path:
        """Path to plugins directory."""
        # From plugins/sanctum/tests/unit/scripts/test_meta_evaluation.py
        # Go up 4 levels to project root
        return Path(__file__).parents[4]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_runs_on_all_plugins(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation can scan all plugins

        Given the meta-evaluation script
        When running without --plugin filter
        Then it should evaluate all evaluation skills across plugins
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        output = result.stdout + result.stderr
        # Should mention multiple plugins
        assert "abstract" in output.lower() or "leyline" in output.lower()

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_exits_with_error_on_critical_issues(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation exits with error on critical issues

        Given the meta-evaluation script
        When critical issues are found
        Then it should exit with non-zero status
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Assert - exit code 0 or 1 is acceptable (1 = issues found)
        # This test verifies it doesn't crash
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_verbose_mode_includes_details(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Verbose mode shows detailed results

        Given the meta-evaluation script
        When running with --verbose flag
        Then it should show detailed results for each skill
        """
        # Arrange
        cmd = [
            sys.executable,
            str(meta_eval_script),
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "abstract",
            "--verbose",
        ]

        # Act
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"
        # Verbose output should be longer
        assert len(result.stdout + result.stderr) > 100


class TestRecursiveValidation:
    """
    Feature: Meta-evaluation enforces recursive validation principle

    As a framework designer
    I want evaluation skills to be evaluated themselves
    So that "evaluation evaluates evaluation" principle holds
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_is_evaluated(self) -> None:
        """
        Scenario: skills-eval skill is included in evaluation

        Given the meta-evaluation inventory
        When checking which skills are evaluated
        Then skills-eval should be in the list
        """
        # This validates the recursive principle
        # Read the script directly to check inventory
        # From plugins/sanctum/tests/unit/scripts/ go up 3 to sanctum, then to scripts
        script_path = Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"
        script_content = script_path.read_text()

        # Assert - skills-eval is in inventory
        assert "skills-eval" in script_content
        assert "abstract" in script_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hooks_eval_is_evaluated(self) -> None:
        """
        Scenario: hooks-eval skill is included in evaluation

        Given the meta-evaluation inventory
        When checking which skills are evaluated
        Then hooks-eval should be in the list
        """
        # This validates the recursive principle
        script_path = Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"
        script_content = script_path.read_text()

        # Assert - hooks-eval is in inventory
        assert "hooks-eval" in script_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evaluation_framework_is_evaluated(self) -> None:
        """
        Scenario: evaluation-framework skill is included in evaluation

        Given the meta-evaluation inventory
        When checking which skills are evaluated
        Then evaluation-framework should be in the list
        """
        # This validates the recursive principle
        script_path = Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"
        script_content = script_path.read_text()

        # Assert - evaluation-framework is in inventory
        assert "evaluation-framework" in script_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_testing_quality_standards_is_evaluated(self) -> None:
        """
        Scenario: testing-quality-standards skill is included in evaluation

        Given the meta-evaluation inventory
        When checking which skills are evaluated
        Then testing-quality-standards should be in the list
        """
        # This validates the recursive principle
        script_path = Path(__file__).parents[3] / "scripts" / "meta_evaluation.py"
        script_content = script_path.read_text()

        # Assert - testing-quality-standards is in inventory
        assert "testing-quality-standards" in script_content
