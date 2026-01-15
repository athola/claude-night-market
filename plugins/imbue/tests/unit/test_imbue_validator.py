"""Tests for imbue plugin validation logic.

This module tests the core validation functionality of the imbue validator,
following TDD/BDD principles and testing all business logic scenarios.
"""

import json
import logging
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the validator - handle both development and test environments
try:
    from scripts.imbue_validator import (
        ImbueValidationResult,
        ImbueValidator,
    )
    from scripts.imbue_validator import (
        main as imbue_main,
    )
except ImportError:
    # For testing before module exists
    ImbueValidator = None
    ImbueValidationResult = None
    imbue_main = None


class TestImbueValidator:
    """Feature: Imbue plugin validates review workflow infrastructure.

    As a plugin developer
    I want validation to validate review workflows are properly structured
    So that evidence logging and structured outputs work correctly
    """

    @pytest.fixture
    def mock_plugin_structure(self, tmp_path):
        """Create a mock plugin structure for testing."""
        plugin_root = tmp_path / "test-plugin"
        plugin_root.mkdir()

        # Create plugin.json
        plugin_config = {
            "name": "imbue",
            "version": "2.0.0",
            "skills": [
                {"name": "review-core", "file": "skills/review-core/SKILL.md"},
                {
                    "name": "evidence-logging",
                    "file": "skills/evidence-logging/SKILL.md",
                },
            ],
        }
        (plugin_root / "plugin.json").write_text(json.dumps(plugin_config))

        # Create skill directories and files
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        # review-core skill
        review_core_dir = skills_dir / "review-core"
        review_core_dir.mkdir()
        (review_core_dir / "SKILL.md").write_text("""---

name: review-core
description: Foundational workflow scaffolding
---

# Review Core

This skill provides checklist and deliverable functionality.

## Evidence
Evidence logging is important for reviews.

## Structured Output
We generate structured output for reviews.
""")

        # evidence-logging skill
        evidence_log_dir = skills_dir / "evidence-logging"
        evidence_log_dir.mkdir()
        (evidence_log_dir / "SKILL.md").write_text("""---

name: evidence-logging
description: Evidence capture workflow
---

# Evidence Logging

This skill tracks and logs evidence for reviews.

## Documentation
We document all commands and outputs.
""")

        # non-review skill
        other_dir = skills_dir / "other-skill"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("""---

name: other-skill
description: Non-review skill
---

# Other Skill

This skill doesn't do reviews.
""")

        return plugin_root

    @pytest.mark.unit
    def test_validator_initialization(self, mock_plugin_structure) -> None:
        """Scenario: Validator initializes with plugin structure.

        Given a valid plugin directory
        When initializing ImbueValidator
        Then it should load skill files and configuration.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange & Act
        validator = ImbueValidator(mock_plugin_structure)

        # Assert
        assert validator.plugin_root == mock_plugin_structure
        assert len(validator.skill_files) == 3
        assert validator.plugin_config == mock_plugin_structure / "plugin.json"

    @pytest.mark.unit
    def test_validator_initialization_with_nonexistent_directory(self) -> None:
        """Scenario: Validator handles non-existent directory gracefully.

        Given a non-existent plugin directory
        When initializing ImbueValidator
        Then it should initialize with empty skill list.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange & Act
        validator = ImbueValidator(Path("/nonexistent/directory"))

        # Assert
        assert validator.plugin_root == Path("/nonexistent/directory")
        assert len(validator.skill_files) == 0

    @pytest.mark.unit
    def test_validator_notifies_when_plugin_root_not_exists(self, caplog) -> None:
        """Scenario: Validator notifies when plugin root doesn't exist.

        Given a non-existent plugin directory
        When initializing ImbueValidator
        Then it should log a warning about the missing directory.

        Addresses issue #34.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange & Act
        with caplog.at_level(logging.WARNING):
            validator = ImbueValidator(Path("/nonexistent/plugin/directory"))

        # Assert - should have logged a warning
        assert any(
            "not found" in record.message.lower()
            or "does not exist" in record.message.lower()
            for record in caplog.records
        ), (
            f"Expected warning about missing directory, got: {[r.message for r in caplog.records]}"
        )
        assert validator.root_exists is False

    @pytest.mark.unit
    def test_validator_notifies_when_plugin_root_empty(self, tmp_path, caplog) -> None:
        """Scenario: Validator notifies when plugin root exists but is empty.

        Given an empty plugin directory
        When initializing ImbueValidator
        Then it should log a warning about the empty directory.

        Addresses issue #34.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create empty directory
        empty_dir = tmp_path / "empty-plugin"
        empty_dir.mkdir()

        # Act
        with caplog.at_level(logging.WARNING):
            validator = ImbueValidator(empty_dir)

        # Assert - should have logged a warning about empty directory
        assert any("empty" in record.message.lower() for record in caplog.records), (
            f"Expected warning about empty directory, got: {[r.message for r in caplog.records]}"
        )
        assert validator.root_empty is True

    @pytest.mark.unit
    def test_validator_notifies_when_plugin_lacks_structure(
        self, tmp_path, caplog
    ) -> None:
        """Scenario: Validator notifies when plugin root lacks expected structure.

        Given a plugin directory without skills/ or plugin.json
        When initializing ImbueValidator
        Then it should log a warning about missing structure.

        Addresses issue #34.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create directory with some files but no plugin structure
        malformed_dir = tmp_path / "malformed-plugin"
        malformed_dir.mkdir()
        (malformed_dir / "random.txt").write_text("not a plugin")

        # Act
        with caplog.at_level(logging.WARNING):
            validator = ImbueValidator(malformed_dir)

        # Assert - should have logged a warning about missing structure
        assert any(
            "structure" in record.message.lower()
            or "skills" in record.message.lower()
            or "plugin.json" in record.message.lower()
            for record in caplog.records
        ), (
            f"Expected warning about missing structure, got: {[r.message for r in caplog.records]}"
        )
        assert validator.has_valid_structure is False

    @pytest.mark.unit
    def test_validator_root_status_properties(self, mock_plugin_structure) -> None:
        """Scenario: Validator exposes root status properties.

        Given a valid plugin structure
        When initializing ImbueValidator
        Then it should have correct status properties.

        Addresses issue #34.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange & Act
        validator = ImbueValidator(mock_plugin_structure)

        # Assert - valid structure should have all good status
        assert validator.root_exists is True
        assert validator.root_empty is False
        assert validator.has_valid_structure is True

    @pytest.mark.unit
    def test_scan_review_workflows_finds_review_skills(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan identifies all review workflow skills.

        Given a plugin with review and non-review skills
        When scanning for review workflows
        Then it should identify review-pattern skills
        And ignore non-review skills.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert result["skills_found"] == {
            "review-core",
            "evidence-logging",
            "other-skill",
        }
        assert "review-core" in result["review_workflow_skills"]
        assert "evidence-logging" in result["review_workflow_skills"]
        assert "other-skill" not in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_scan_review_workflows_detects_patterns(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan detects various review workflow patterns.

        Given skills with different review-related keywords
        When scanning for review workflows
        Then it should match multiple patterns
        And categorize appropriately.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - add a skill with workflow keyword
        workflow_dir = mock_plugin_structure / "skills" / "workflow-skill"
        workflow_dir.mkdir()
        (workflow_dir / "SKILL.md").write_text("""---

name: workflow-skill
description: Workflow orchestration
---

# Workflow Skill

This provides workflow orchestration.
""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert "workflow-skill" in result["review_workflow_skills"]
        assert len(result["review_workflow_skills"]) >= 3

    @pytest.mark.unit
    def test_scan_review_workflows_loads_plugin_config(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan loads plugin configuration successfully.

        Given a valid plugin.json file
        When scanning for review workflows
        Then it should add evidence logging patterns
        And parse JSON without errors.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert "review-workflows" in result["evidence_logging_patterns"]
        assert "evidence-logging" in result["evidence_logging_patterns"]
        assert "structured-output" in result["evidence_logging_patterns"]
        assert "workflow-orchestration" in result["evidence_logging_patterns"]
        assert len(result["issues"]) == 0

    @pytest.mark.unit
    def test_scan_review_workflows_handles_invalid_json(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan handles invalid plugin.json gracefully.

        Given an invalid plugin.json file
        When scanning for review workflows
        Then it should record error in issues
        And continue processing skills.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - write invalid JSON
        (mock_plugin_structure / "plugin.json").write_text("invalid json content")
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert result["issues"][0].startswith("Invalid plugin.json at line 1:")
        assert len(result["issues"]) == 1

    @pytest.mark.unit
    def test_scan_review_workflows_handles_plugin_config_read_error(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan handles plugin.json read errors gracefully.

        Given a plugin.json file that cannot be decoded as text
        When scanning for review workflows
        Then it should record an issue instead of crashing
        And continue processing skills.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - write bytes that are invalid UTF-8
        (mock_plugin_structure / "plugin.json").write_bytes(b"\xff")
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert any("Unable to read plugin.json" in issue for issue in result["issues"])
        assert result["skills_found"] == {
            "review-core",
            "evidence-logging",
            "other-skill",
        }

    @pytest.mark.unit
    def test_scan_review_workflows_handles_skill_file_read_error(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Scan handles skill file read errors gracefully.

        Given a SKILL.md file that cannot be decoded as text
        When scanning for review workflows
        Then it should record an issue instead of crashing
        And continue processing other skills.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - make one skill file invalid UTF-8
        (mock_plugin_structure / "skills" / "other-skill" / "SKILL.md").write_bytes(
            b"\xff"
        )
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert any("other-skill: Unable to read" in issue for issue in result["issues"])
        assert "review-core" in result["skills_found"]
        assert "evidence-logging" in result["skills_found"]

    @pytest.mark.unit
    def test_validate_review_workflows_review_core_components(
        self,
        mock_plugin_structure,
    ) -> None:
        """Scenario: Validation checks review-core skill components.

        Given a review-core skill missing components
        When validating review workflows
        Then it should identify missing components
        And report specific issues.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create review-core skill missing deliverable component
        review_core_dir = mock_plugin_structure / "skills" / "review-core"
        (review_core_dir / "SKILL.md").write_text("""---

name: review-core
description: Incomplete review skill
---

# Review Core

This skill has checklist but no deliverable section.

## Checklist
- Item 1
- Item 2
""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        issues = validator.validate_review_workflows()

        # Assert
        review_core_issues = [
            issue for issue in issues if issue.startswith("review-core:")
        ]
        assert len(review_core_issues) > 0
        assert any("Missing review components" in issue for issue in review_core_issues)

    @pytest.mark.unit
    def test_validate_review_workflows_evidence_patterns(
        self, mock_plugin_structure
    ) -> None:
        """Scenario: Validation checks for evidence logging patterns.

        Given skills without evidence logging patterns
        When validating review workflows
        Then it should flag missing evidence patterns
        Except for review-core skill.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create skill without evidence patterns
        no_evidence_dir = mock_plugin_structure / "skills" / "no-audit"
        no_evidence_dir.mkdir()
        (no_evidence_dir / "SKILL.md").write_text("""---

	name: no-audit
	description: Skill without audit patterns
	---

	# No Audit Skill

	This skill omits traceability details.
	""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        issues = validator.validate_review_workflows()

        # Assert
        evidence_issues = [
            issue for issue in issues if "evidence logging patterns" in issue
        ]
        assert any("no-audit" in issue for issue in evidence_issues)

    @pytest.mark.unit
    def test_validate_review_workflows_excludes_review_core_from_evidence_check(
        self,
        mock_plugin_structure,
    ) -> None:
        """Scenario: Validation excludes review-core from evidence pattern requirement.

        Given a review-core skill without evidence keywords
        When validating review workflows
        Then it should not flag review-core for missing evidence patterns.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - review-core skill without explicit evidence keywords
        review_core_dir = mock_plugin_structure / "skills" / "review-core"
        (review_core_dir / "SKILL.md").write_text("""---

name: review-core
description: Core review workflow
---

# Review Core

This skill provides review scaffolding with checklist and deliverables.
""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        issues = validator.validate_review_workflows()

        # Assert
        review_core_issues = [issue for issue in issues if "review-core:" in issue]
        evidence_issues = [
            issue
            for issue in review_core_issues
            if "evidence logging patterns" in issue
        ]
        assert len(evidence_issues) == 0

    @pytest.mark.unit
    def test_generate_report_includes_all_sections(self, mock_plugin_structure) -> None:
        """Scenario: Report generation includes all required sections.

        Given a plugin with various validation results
        When generating a report
        Then it should include all sections with appropriate content.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        report = validator.generate_report()

        # Assert
        assert "Imbue Plugin Review Workflow Report" in report
        assert f"Plugin Root: {mock_plugin_structure}" in report
        assert "Skill Files: 3" in report
        assert "Review Workflow Skills:" in report
        assert "Evidence Logging Patterns:" in report
        assert "review-workflows" in report
        assert "evidence-logging" in report

    @pytest.mark.unit
    def test_generate_report_shows_issues(self, mock_plugin_structure) -> None:
        """Scenario: Report displays validation issues.

        Given validation with issues found
        When generating a report
        Then it should list all issues with numbering.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create issues
        (mock_plugin_structure / "plugin.json").write_text("invalid json")

        no_evidence_dir = mock_plugin_structure / "skills" / "no-evidence"
        no_evidence_dir.mkdir()
        (no_evidence_dir / "SKILL.md").write_text("No traceability patterns")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        report = validator.generate_report()

        # Assert
        assert "Issues Found" in report
        assert "Invalid plugin.json at line 1:" in report
        assert "no-evidence: Should have evidence logging patterns" in report

    @pytest.mark.unit
    def test_generate_report_success_message(self, mock_plugin_structure) -> None:
        """Scenario: Report shows success when no issues found.

        Given validation without issues
        When generating a report
        Then it should display success message.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - validate all skills have proper patterns
        for skill_file in mock_plugin_structure.glob("skills/*/SKILL.md"):
            content = skill_file.read_text()
            if "evidence" not in content.lower():
                content += "\n\n## Evidence\nThis skill logs evidence."
                skill_file.write_text(content)

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        report = validator.generate_report()

        # Assert
        assert "All review workflow skills validated successfully!" in report
        assert "Issues Found" not in report

    @pytest.mark.unit
    def test_pattern_matching_case_insensitive(self, mock_plugin_structure) -> None:
        """Scenario: Pattern matching is case insensitive.

        Given skills with mixed case keywords
        When scanning for review workflows
        Then it should match patterns regardless of case.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create skill with uppercase patterns
        mixed_case_dir = mock_plugin_structure / "skills" / "mixed-case"
        mixed_case_dir.mkdir()
        (mixed_case_dir / "SKILL.md").write_text("""---

name: mixed-case
description: Mixed case REVIEW and WORKFLOW
---

# Mixed Case

This skill has REVIEW and WORKFLOW in uppercase.
Also includes EVIDENCE logging.
""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert "mixed-case" in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_empty_plugin_directory(self, tmp_path) -> None:
        """Scenario: Validation handles empty plugin directory.

        Given an empty plugin directory
        When scanning for review workflows
        Then it should return empty results.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange
        empty_dir = tmp_path / "empty-plugin"
        empty_dir.mkdir()
        validator = ImbueValidator(empty_dir)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert len(result["skills_found"]) == 0
        assert len(result["review_workflow_skills"]) == 0
        assert len(result["issues"]) == 0

    @pytest.mark.unit
    def test_missing_plugin_json(self, mock_plugin_structure) -> None:
        """Scenario: Validation handles missing plugin.json.

        Given a plugin directory without plugin.json
        When scanning for review workflows
        Then it should continue processing skills.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - remove plugin.json
        (mock_plugin_structure / "plugin.json").unlink()
        validator = ImbueValidator(mock_plugin_structure)

        # Act
        result = validator.scan_review_workflows()

        # Assert
        assert len(result["skills_found"]) == 3  # Still finds skills
        assert len(result["review_workflow_skills"]) >= 2  # Still finds review patterns
        # No evidence patterns added without plugin.json
        assert len(result["evidence_logging_patterns"]) == 0

    @pytest.mark.unit
    def test_cli_scan_exits_nonzero_when_issues(
        self, mock_plugin_structure, capsys
    ) -> None:
        """Scenario: CLI scan exits non-zero when issues exist."""
        if imbue_main is None:
            pytest.skip("imbue_main not available")

        with patch.object(
            sys,
            "argv",
            ["prog", "--root", str(mock_plugin_structure), "--scan"],
        ):
            with pytest.raises(SystemExit) as exc:
                imbue_main()
            assert exc.value.code == 1

        out = capsys.readouterr().out
        assert "skills_found:" in out
        assert "Issues:" in out

    @pytest.mark.unit
    def test_cli_scan_success_outputs_no_issues(
        self, mock_plugin_structure, capsys
    ) -> None:
        """Scenario: CLI scan prints results and exits cleanly when no issues."""
        if imbue_main is None:
            pytest.skip("imbue_main not available")

        # validate all skills mention evidence so validation passes.
        for skill_file in mock_plugin_structure.glob("skills/*/SKILL.md"):
            content = skill_file.read_text(errors="ignore")
            if "evidence" not in content.lower():
                skill_file.write_text(content + "\n\n## Evidence\nWe capture evidence.")

        with patch.object(
            sys,
            "argv",
            ["prog", "--root", str(mock_plugin_structure), "--scan"],
        ):
            imbue_main()

        out = capsys.readouterr().out
        assert "skills_found:" in out
        assert "review_workflow_skills:" in out
        assert "evidence_logging_patterns:" in out
        assert "Issues:" not in out

    @pytest.mark.unit
    def test_cli_report_outputs_report(self, mock_plugin_structure, capsys) -> None:
        """Scenario: CLI report prints a full report."""
        if imbue_main is None:
            pytest.skip("imbue_main not available")

        with patch.object(
            sys,
            "argv",
            ["prog", "--root", str(mock_plugin_structure), "--report"],
        ):
            imbue_main()

        out = capsys.readouterr().out
        assert "Imbue Plugin Review Workflow Report" in out


class TestImbueValidatorIntegration:
    """Feature: Imbue validator integration with real file system.

    As a validation tool
    I want to work with real file system operations
    So that validation accurately reflects plugin structure
    """

    @pytest.mark.integration
    def test_real_plugin_validation(self, imbue_plugin_root) -> None:
        """Scenario: Validate real imbue plugin structure.

        Given the actual imbue plugin directory
        When running validation
        Then it should process actual skills and configuration.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange & Act
        validator = ImbueValidator(imbue_plugin_root)
        result = validator.scan_review_workflows()
        issues = validator.validate_review_workflows()
        report = validator.generate_report()

        # Assert - these tests adapt to the actual plugin structure
        assert isinstance(result, dict)
        assert "skills_found" in result
        assert "review_workflow_skills" in result
        assert "evidence_logging_patterns" in result
        assert "issues" in result
        assert isinstance(issues, list)
        assert isinstance(report, str)
        assert len(report) > 0

    @pytest.mark.integration
    def test_file_permissions_handling(self, tmp_path) -> None:
        """Scenario: Validation handles file permission issues.

        Given files with permission restrictions
        When running validation
        Then it should handle permissions gracefully.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        plugin_root = tmp_path / "permission-test"
        plugin_root.mkdir()

        # Create a skill file
        skill_dir = plugin_root / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Test content")

        # Make the file unreadable to simulate a permission error.
        skill_file.chmod(0)

        validator = ImbueValidator(plugin_root)
        issues = validator.validate_review_workflows()
        assert any("Unable to read" in issue for issue in issues)


@pytest.mark.skipif(ImbueValidator is None, reason="ImbueValidator not available")
class TestImbueValidatorPerformance:
    """Feature: Imbue validator performance with large plugins.

    As a validation tool
    I want to handle large plugin structures efficiently
    So that validation completes in reasonable time
    """

    @pytest.mark.performance
    def test_large_plugin_validation_performance(self, tmp_path) -> None:
        """Scenario: Validation performance with many skills.

        Given a plugin with many skill files
        When running validation
        Then it should complete within reasonable time.
        """
        # Arrange - create many skills
        plugin_root = tmp_path / "large-plugin"
        plugin_root.mkdir()
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        # Create 100 skill files
        for i in range(100):
            skill_dir = skills_dir / f"skill-{i:03d}"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(f"""---

name: skill-{i:03d}
description: Test skill {i}
---

# Skill {i}

This is test skill number {i} with review workflow patterns.
""")

        # Act
        validator = ImbueValidator(plugin_root)

        start_time = time.time()
        result = validator.scan_review_workflows()
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(result["skills_found"]) == 100

    @pytest.mark.performance
    def test_memory_usage_large_plugin(self, tmp_path) -> None:
        """Scenario: Memory usage with large plugin structures.

        Given a plugin with large skill files
        When running validation
        Then memory usage should remain reasonable.
        """
        # This is a placeholder for memory testing
        # In practice, you'd use memory profiling tools
        plugin_root = tmp_path / "memory-test"
        plugin_root.mkdir()
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        # Create large skill files
        for i in range(10):
            skill_dir = skills_dir / f"large-skill-{i}"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            # Create a large content file
            large_content = "# Large Skill\n\n" + "This is repeated content.\n" * 10000
            skill_file.write_text(large_content)

        validator = ImbueValidator(plugin_root)

        # The test passes if it doesn't crash with memory issues
        result = validator.scan_review_workflows()
        assert len(result["skills_found"]) == 10


class TestImbueValidatorEdgeCases:
    """Feature: Imbue validator handles edge cases robustly.

    As a validation tool
    I want to handle all edge cases gracefully
    So that the validator never crashes unexpectedly
    """

    @pytest.mark.unit
    def test_cli_default_prints_help(self, capsys) -> None:
        """Scenario: CLI prints help when no arguments provided.

        Given no command line arguments
        When running main()
        Then it should print help information.
        """
        if imbue_main is None:
            pytest.skip("imbue_main not available")

        with patch.object(sys, "argv", ["prog"]):
            imbue_main()

        out = capsys.readouterr().out
        assert "usage:" in out.lower() or "--root" in out or "--report" in out

    @pytest.mark.unit
    def test_directory_read_oserror_handling(self, tmp_path, caplog) -> None:
        """Scenario: Validator handles OSError when reading directory.

        Given a directory that raises OSError when iterating
        When initializing ImbueValidator
        Then it should handle the error gracefully and log a warning.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Create a directory
        test_dir = tmp_path / "test-plugin"
        test_dir.mkdir()
        # Put a file in it so it's not empty
        (test_dir / "dummy.txt").write_text("dummy")

        # Mock iterdir to raise OSError
        with patch.object(Path, "iterdir", side_effect=OSError("Permission denied")):
            with caplog.at_level(logging.WARNING):
                validator = ImbueValidator(test_dir)

        # Should have handled the error
        assert validator.root_empty is True
        assert any("Unable to read" in record.message for record in caplog.records)

    @pytest.mark.unit
    def test_frontmatter_without_review_patterns(self, tmp_path) -> None:
        """Scenario: Skills with frontmatter but no review patterns are excluded.

        Given a skill with valid frontmatter but no review-related content
        When scanning for review workflows
        Then it should not be classified as a review workflow skill.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Create plugin structure
        plugin_root = tmp_path / "test-plugin"
        skills_dir = plugin_root / "skills" / "non-review"
        skills_dir.mkdir(parents=True)

        # Create skill with frontmatter but no review patterns
        # IMPORTANT: Content must NOT contain any of these words:
        # workflow, evidence, structured, output, orchestrat, checklist, deliverable
        (skills_dir / "SKILL.md").write_text("""---
name: non-review-skill
description: A skill that does something else
category: utilities
tags:
  - helper
  - utility
---

# Non-Review Skill

This skill helps with general utilities.
It provides helper functions for common tasks.
Just plain utility operations.
""")

        validator = ImbueValidator(plugin_root)
        result = validator.scan_review_workflows()

        # Skill should be found but NOT classified as review workflow
        assert "non-review" in result["skills_found"]
        assert "non-review" not in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_frontmatter_with_review_category_in_frontmatter(self, tmp_path) -> None:
        """Scenario: Skills with review-patterns category are classified correctly.

        Given a skill with category: review-patterns in frontmatter
        When scanning for review workflows
        Then it should be classified as a review workflow skill via frontmatter.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        plugin_root = tmp_path / "test-plugin"
        skills_dir = plugin_root / "skills" / "categorized-review"
        skills_dir.mkdir(parents=True)

        # Create skill with review-patterns category
        (skills_dir / "SKILL.md").write_text("""---
name: categorized-review
description: A skill with review category
category: review-patterns
---

# Categorized Review Skill

This skill is categorized as review-patterns.
No keywords needed in the body.
""")

        validator = ImbueValidator(plugin_root)
        result = validator.scan_review_workflows()

        assert "categorized-review" in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_frontmatter_with_review_workflow_usage(self, tmp_path) -> None:
        """Scenario: Skills with review-workflow usage pattern are classified.

        Given a skill with - review-workflow in usage patterns
        When scanning for review workflows
        Then it should be classified as a review workflow skill.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        plugin_root = tmp_path / "test-plugin"
        skills_dir = plugin_root / "skills" / "usage-review"
        skills_dir.mkdir(parents=True)

        (skills_dir / "SKILL.md").write_text("""---
name: usage-review
description: A skill with review-workflow usage
usage_patterns:
  - review-workflow
  - evidence-capture
---

# Usage Review Skill

This skill uses review-workflow pattern.
No keywords needed in the body.
""")

        validator = ImbueValidator(plugin_root)
        result = validator.scan_review_workflows()

        assert "usage-review" in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_incomplete_frontmatter_falls_through_to_content_scan(
        self, tmp_path
    ) -> None:
        """Scenario: Skills with incomplete frontmatter fall through to content scan.

        Given a skill that starts with '---' but has no closing '---'
        When scanning for review workflows
        Then it should skip frontmatter parsing and check content patterns.

        This covers branch 133->136 where frontmatter remains None.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        plugin_root = tmp_path / "test-plugin"
        skills_dir = plugin_root / "skills" / "incomplete-fm"
        skills_dir.mkdir(parents=True)

        # Create skill with incomplete frontmatter (starts with --- but no closing ---)
        # This causes split("---", 2) to produce fewer than 3 parts
        (skills_dir / "SKILL.md").write_text("""---
name: incomplete-frontmatter
This file starts with --- but never closes the frontmatter.
It contains workflow patterns in the content.
""")

        validator = ImbueValidator(plugin_root)
        result = validator.scan_review_workflows()

        # Skill should be found
        assert "incomplete-fm" in result["skills_found"]
        # Should match via content pattern ("workflow" keyword), not frontmatter
        assert "incomplete-fm" in result["review_workflow_skills"]

    @pytest.mark.unit
    def test_incomplete_frontmatter_no_patterns(self, tmp_path) -> None:
        """Scenario: Incomplete frontmatter with no patterns is excluded.

        Given a skill with incomplete frontmatter and no review patterns
        When scanning for review workflows
        Then it should not be classified as a review workflow skill.

        This also covers branch 133->136.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        plugin_root = tmp_path / "test-plugin"
        skills_dir = plugin_root / "skills" / "broken-fm"
        skills_dir.mkdir(parents=True)

        # Incomplete frontmatter with no review-related keywords
        (skills_dir / "SKILL.md").write_text("""---
name: broken-frontmatter
This file has incomplete frontmatter.
It does not contain any review-related keywords.
Just some generic text here.
""")

        validator = ImbueValidator(plugin_root)
        result = validator.scan_review_workflows()

        assert "broken-fm" in result["skills_found"]
        assert "broken-fm" not in result["review_workflow_skills"]
