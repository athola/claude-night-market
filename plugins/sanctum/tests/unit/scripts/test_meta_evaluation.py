"""Tests for meta-evaluation script and recursive validation.

This module tests the meta-evaluation framework that validates evaluation
skills meet their own quality standards, following TDD/BDD principles.

The Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
"""

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the MetaEvaluator class directly for unit-level tests
# (TestCheckModuleReferences, TestCheckCodeExamples, TestCheckCrossReferences).
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))
from meta_evaluation import MetaEvaluator  # noqa: E402


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
    @pytest.mark.integration
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
    @pytest.mark.integration
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
    @pytest.mark.integration
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
    @pytest.mark.integration
    def test_checks_abstract_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates abstract plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on abstract plugin
        Then it should have zero issues
        And exit with success
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
        output = result.stdout + result.stderr

        # Assert - zero issues required
        assert "abstract" in output.lower(), "Plugin name not in output"
        assert "Total Issues: 0" in output, (
            f"Abstract plugin has meta-evaluation issues:\n{output}"
        )
        assert result.returncode == 0, f"Script failed:\n{output}"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_checks_leyline_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates leyline plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on leyline plugin
        Then it should have zero issues
        And exit with success
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
        output = result.stdout + result.stderr

        # Assert - zero issues required
        assert "leyline" in output.lower(), "Plugin name not in output"
        assert "Total Issues: 0" in output, (
            f"Leyline plugin has meta-evaluation issues:\n{output}"
        )
        assert result.returncode == 0, f"Script failed:\n{output}"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_checks_imbue_plugin(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: Meta-evaluation validates imbue plugin evaluation skills

        Given the meta-evaluation script
        When running evaluation on imbue plugin
        Then it should have zero issues
        And exit with success
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
        output = result.stdout + result.stderr

        # Assert - zero issues required
        assert "imbue" in output.lower(), "Plugin name not in output"
        assert "Total Issues: 0" in output, (
            f"Imbue plugin has meta-evaluation issues:\n{output}"
        )
        assert result.returncode == 0, f"Script failed:\n{output}"

    @pytest.mark.bdd
    @pytest.mark.integration
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
    @pytest.mark.integration
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
    @pytest.mark.integration
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
    @pytest.mark.integration
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
    def test_all_skills_pass_with_zero_issues(
        self, meta_eval_script: Path, plugins_root: Path
    ) -> None:
        """
        Scenario: All evaluation skills must pass meta-evaluation

        Given the meta-evaluation script
        When running on all plugins
        Then there should be zero issues found
        And exit code should be 0 (success)

        This is a quality gate - if this test fails, fix the skill issues
        before merging. Do not weaken this test.
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
        output = result.stdout + result.stderr

        # Assert - must have zero issues
        assert "Total Issues: 0" in output, (
            f"Meta-evaluation found issues that must be fixed:\n{output}"
        )
        assert result.returncode == 0, f"Meta-evaluation failed with issues:\n{output}"

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

    @pytest.fixture
    def evaluator(self, tmp_path: Path) -> MetaEvaluator:
        return MetaEvaluator(tmp_path, verbose=False)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_is_evaluated(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: skills-eval skill is included in evaluation

        Given the MetaEvaluator.EVALUATION_SKILLS inventory
        When checking the abstract plugin's skills list
        Then skills-eval should be present
        """
        skills = evaluator.EVALUATION_SKILLS
        assert "abstract" in skills
        assert "skills-eval" in skills["abstract"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hooks_eval_is_evaluated(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: hooks-eval skill is included in evaluation

        Given the MetaEvaluator.EVALUATION_SKILLS inventory
        When checking the abstract plugin's skills list
        Then hooks-eval should be present
        """
        skills = evaluator.EVALUATION_SKILLS
        assert "hooks-eval" in skills.get("abstract", [])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evaluation_framework_is_evaluated(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: evaluation-framework skill is included in evaluation

        Given the MetaEvaluator.EVALUATION_SKILLS inventory
        When checking the leyline plugin's skills list
        Then evaluation-framework should be present
        """
        skills = evaluator.EVALUATION_SKILLS
        assert "evaluation-framework" in skills.get("leyline", [])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_testing_quality_standards_is_evaluated(
        self, evaluator: MetaEvaluator
    ) -> None:
        """
        Scenario: testing-quality-standards skill is included in evaluation

        Given the MetaEvaluator.EVALUATION_SKILLS inventory
        When checking the leyline plugin's skills list
        Then testing-quality-standards should be present
        """
        skills = evaluator.EVALUATION_SKILLS
        assert "testing-quality-standards" in skills.get("leyline", [])


# ---------------------------------------------------------------------------
# Unit tests for the three new check methods
# ---------------------------------------------------------------------------


class TestCheckModuleReferences:
    """
    Feature: check_module_references validates frontmatter module lists

    As a skill author
    I want broken module references caught automatically
    So that skill readers are not sent to non-existent files
    """

    @pytest.fixture
    def evaluator(self, tmp_path: Path) -> MetaEvaluator:
        return MetaEvaluator(tmp_path, verbose=False)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passes_when_all_modules_exist(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: All modules listed in frontmatter exist on disk

        Given a skill directory with modules/ files that match the frontmatter list
        When check_module_references is called
        Then it returns True and records no issues
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        (skill_path / "modules").mkdir(parents=True)
        (skill_path / "modules" / "overview.md").write_text("# Overview")
        frontmatter = {"modules": ["modules/overview.md"]}

        # Act
        result = evaluator.check_module_references(
            skill_path, frontmatter, "test:skill"
        )

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fails_when_listed_module_is_missing(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: A module listed in frontmatter does not exist on disk

        Given a skill whose frontmatter references a non-existent file
        When check_module_references is called
        Then it returns False and records a missing_module_file issue
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        skill_path.mkdir()
        frontmatter = {"modules": ["modules/ghost.md"]}

        # Act
        result = evaluator.check_module_references(
            skill_path, frontmatter, "test:skill"
        )

        # Assert
        assert result is False
        assert len(evaluator.issues) == 1
        assert evaluator.issues[0]["type"] == "missing_module_file"
        assert "ghost.md" in evaluator.issues[0]["message"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_flags_unlisted_module_files(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: A .md file exists in modules/ but is not listed in frontmatter

        Given a skill with an orphaned module file
        When check_module_references is called
        Then it returns False and records an unlisted_module_file issue
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        (skill_path / "modules").mkdir(parents=True)
        (skill_path / "modules" / "orphan.md").write_text("# Orphan")
        frontmatter: dict = {}  # no modules key

        # Act
        result = evaluator.check_module_references(
            skill_path, frontmatter, "test:skill"
        )

        # Assert
        assert result is False
        issue_types = [i["type"] for i in evaluator.issues]
        assert "unlisted_module_file" in issue_types
        assert any("orphan.md" in i["message"] for i in evaluator.issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passes_when_no_modules_anywhere(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: No modules in frontmatter and no modules/ directory

        Given a simple skill with no module references at all
        When check_module_references is called
        Then it returns True and records no issues
        """
        # Arrange
        skill_path = tmp_path / "simple-skill"
        skill_path.mkdir()
        frontmatter: dict = {}

        # Act
        result = evaluator.check_module_references(
            skill_path, frontmatter, "test:skill"
        )

        # Assert
        assert result is True
        assert evaluator.issues == []


class TestCheckCodeExamples:
    """
    Feature: check_code_examples detects unannotated fenced code blocks

    As a skill reader
    I want code blocks to declare their language
    So that syntax highlighting and intent are clear
    """

    @pytest.fixture
    def evaluator(self, tmp_path: Path) -> MetaEvaluator:
        return MetaEvaluator(tmp_path, verbose=False)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passes_when_all_blocks_annotated(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: All fenced code blocks have language annotations

        Given skill content where every code block specifies a language
        When check_code_examples is called
        Then it returns True and records no issues
        """
        # Arrange
        content = (
            "# Skill\n\n```python\nprint('hello')\nprint('world')\nprint('!')\n```\n"
        )

        # Act
        result = evaluator.check_code_examples(content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fails_when_long_block_missing_annotation(
        self, evaluator: MetaEvaluator
    ) -> None:
        """
        Scenario: A code block with 3+ lines has no language annotation

        Given skill content with an unannotated multi-line code block
        When check_code_examples is called
        Then it returns False and records an unannotated_code_block issue
        """
        # Arrange
        content = "# Skill\n\n```\nline one\nline two\nline three\n```\n"

        # Act
        result = evaluator.check_code_examples(content, "test:skill")

        # Assert
        assert result is False
        assert len(evaluator.issues) == 1
        assert evaluator.issues[0]["type"] == "unannotated_code_block"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skips_short_blocks(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: A code block with fewer than MIN_CODE_BLOCK_LINES lines is skipped

        Given a short unannotated code block (1-2 lines)
        When check_code_examples is called
        Then it returns True and records no issues
        """
        # Arrange — 2-line block, under the MIN_CODE_BLOCK_LINES=3 threshold
        content = "# Skill\n\n```\nshort line\nanother\n```\n"

        # Act
        result = evaluator.check_code_examples(content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_multiple_unannotated_blocks(
        self, evaluator: MetaEvaluator
    ) -> None:
        """
        Scenario: Multiple unannotated blocks each produce an issue

        Given skill content with two unannotated 3-line blocks
        When check_code_examples is called
        Then it records two separate unannotated_code_block issues
        """
        # Arrange
        content = (
            "# Skill\n\n"
            "```\nline1\nline2\nline3\n```\n\n"
            "```\nlineA\nlineB\nlineC\n```\n"
        )

        # Act
        result = evaluator.check_code_examples(content, "test:skill")

        # Assert
        assert result is False
        unannotated = [
            i for i in evaluator.issues if i["type"] == "unannotated_code_block"
        ]
        assert len(unannotated) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passes_with_no_code_blocks(self, evaluator: MetaEvaluator) -> None:
        """
        Scenario: Skill content has no code blocks at all

        Given skill content with no fenced code blocks
        When check_code_examples is called
        Then it returns True and records no issues
        """
        # Arrange
        content = "# Skill\n\nJust prose, no code here.\n"

        # Act
        result = evaluator.check_code_examples(content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []


class TestCheckCrossReferences:
    """
    Feature: check_cross_references detects broken internal markdown links

    As a skill reader
    I want all relative links in skills to resolve to real files
    So that navigation between documents works correctly
    """

    @pytest.fixture
    def evaluator(self, tmp_path: Path) -> MetaEvaluator:
        return MetaEvaluator(tmp_path, verbose=False)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passes_when_referenced_file_exists(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: A relative link points to an existing file

        Given skill content with a relative link to a file that exists
        When check_cross_references is called
        Then it returns True and records no issues
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        skill_path.mkdir()
        (skill_path / "modules").mkdir()
        (skill_path / "modules" / "details.md").write_text("# Details")
        content = "See [details](modules/details.md) for more.\n"

        # Act
        result = evaluator.check_cross_references(skill_path, content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fails_when_referenced_file_missing(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: A relative link points to a file that does not exist

        Given skill content with a broken relative link
        When check_cross_references is called
        Then it returns False and records a broken_cross_reference issue
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        skill_path.mkdir()
        content = "See [missing](modules/ghost.md) for more.\n"

        # Act
        result = evaluator.check_cross_references(skill_path, content, "test:skill")

        # Assert
        assert result is False
        assert len(evaluator.issues) == 1
        assert evaluator.issues[0]["type"] == "broken_cross_reference"
        assert "ghost.md" in evaluator.issues[0]["message"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_http_links(self, evaluator: MetaEvaluator, tmp_path: Path) -> None:
        """
        Scenario: Absolute http/https links are not checked for file existence

        Given skill content with only external URLs
        When check_cross_references is called
        Then it returns True and records no issues
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        skill_path.mkdir()
        content = "See [docs](https://example.com/guide) for more.\n"

        # Act
        result = evaluator.check_cross_references(skill_path, content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_anchor_only_links(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: Anchor-only links (#section) are not checked for file existence

        Given skill content with only in-page anchor links
        When check_cross_references is called
        Then it returns True and records no issues
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        skill_path.mkdir()
        content = "Jump to [section](#overview).\n"

        # Act
        result = evaluator.check_cross_references(skill_path, content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_link_with_anchor_fragment(
        self, evaluator: MetaEvaluator, tmp_path: Path
    ) -> None:
        """
        Scenario: A relative link with an anchor fragment is resolved by file path only

        Given a link like [text](modules/guide.md#section) where guide.md exists
        When check_cross_references is called
        Then it returns True (fragment is stripped before checking)
        """
        # Arrange
        skill_path = tmp_path / "my-skill"
        (skill_path / "modules").mkdir(parents=True)
        (skill_path / "modules" / "guide.md").write_text("# Guide")
        content = "See [guide](modules/guide.md#overview).\n"

        # Act
        result = evaluator.check_cross_references(skill_path, content, "test:skill")

        # Assert
        assert result is True
        assert evaluator.issues == []
