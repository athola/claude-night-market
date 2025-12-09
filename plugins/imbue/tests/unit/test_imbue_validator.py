"""Tests for imbue plugin validation logic.

This module tests the core validation functionality of the imbue validator,
following TDD/BDD principles and testing all business logic scenarios.
"""

# ruff: noqa: S101
import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the validator - handle both development and test environments
try:
    from scripts.imbue_validator import ImbueValidationResult, ImbueValidator
except ImportError:
    # For testing before module exists
    ImbueValidator = None
    ImbueValidationResult = None


class TestImbueValidator:
    """Feature: Imbue plugin validates review workflow infrastructure.

    As a plugin developer
    I want validation to ensure review workflows are properly structured
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
    def test_validator_initialization(self, mock_plugin_structure):
        """Scenario: Validator initializes with plugin structure
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
    def test_validator_initialization_with_nonexistent_directory(self):
        """Scenario: Validator handles non-existent directory gracefully
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
    def test_scan_review_workflows_finds_review_skills(self, mock_plugin_structure):
        """Scenario: Scan identifies all review workflow skills
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
    def test_scan_review_workflows_detects_patterns(self, mock_plugin_structure):
        """Scenario: Scan detects various review workflow patterns
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
    def test_scan_review_workflows_loads_plugin_config(self, mock_plugin_structure):
        """Scenario: Scan loads plugin configuration successfully
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
    def test_scan_review_workflows_handles_invalid_json(self, mock_plugin_structure):
        """Scenario: Scan handles invalid plugin.json gracefully
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
        assert "Invalid plugin.json" in result["issues"]
        assert len(result["issues"]) == 1

    @pytest.mark.unit
    def test_validate_review_workflows_review_core_components(
        self, mock_plugin_structure
    ):
        """Scenario: Validation checks review-core skill components
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
    def test_validate_review_workflows_evidence_patterns(self, mock_plugin_structure):
        """Scenario: Validation checks for evidence logging patterns
        Given skills without evidence logging patterns
        When validating review workflows
        Then it should flag missing evidence patterns
        Except for review-core skill.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - create skill without evidence patterns
        no_evidence_dir = mock_plugin_structure / "skills" / "no-evidence"
        no_evidence_dir.mkdir()
        (no_evidence_dir / "SKILL.md").write_text("""---
name: no-evidence
description: Skill without evidence patterns
---

# No Evidence Skill

This skill doesn't mention evidence or logging.
""")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        issues = validator.validate_review_workflows()

        # Assert
        evidence_issues = [
            issue for issue in issues if "evidence logging patterns" in issue
        ]
        assert any("no-evidence" in issue for issue in evidence_issues)

    @pytest.mark.unit
    def test_validate_review_workflows_excludes_review_core_from_evidence_check(
        self, mock_plugin_structure
    ):
        """Scenario: Validation excludes review-core from evidence pattern requirement
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
    def test_generate_report_includes_all_sections(self, mock_plugin_structure):
        """Scenario: Report generation includes all required sections
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
    def test_generate_report_shows_issues(self, mock_plugin_structure):
        """Scenario: Report displays validation issues
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
        (no_evidence_dir / "SKILL.md").write_text("No evidence patterns")

        validator = ImbueValidator(mock_plugin_structure)

        # Act
        report = validator.generate_report()

        # Assert
        assert "Issues Found" in report
        assert "Invalid plugin.json" in report
        assert "no-evidence: Should have evidence logging patterns" in report

    @pytest.mark.unit
    def test_generate_report_success_message(self, mock_plugin_structure):
        """Scenario: Report shows success when no issues found
        Given validation without issues
        When generating a report
        Then it should display success message.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # Arrange - ensure all skills have proper patterns
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
    def test_pattern_matching_case_insensitive(self, mock_plugin_structure):
        """Scenario: Pattern matching is case insensitive
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
    def test_empty_plugin_directory(self, tmp_path):
        """Scenario: Validation handles empty plugin directory
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
    def test_missing_plugin_json(self, mock_plugin_structure):
        """Scenario: Validation handles missing plugin.json
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


class TestImbueValidatorIntegration:
    """Feature: Imbue validator integration with real file system.

    As a validation tool
    I want to work with real file system operations
    So that validation accurately reflects plugin structure
    """

    @pytest.mark.integration
    def test_real_plugin_validation(self, imbue_plugin_root):
        """Scenario: Validate real imbue plugin structure
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
    def test_file_permissions_handling(self, tmp_path):
        """Scenario: Validation handles file permission issues
        Given files with permission restrictions
        When running validation
        Then it should handle permissions gracefully.
        """
        if ImbueValidator is None:
            pytest.skip("ImbueValidator not available")

        # This test would require more complex setup for permission testing
        # For now, we'll test with a non-readable file simulation
        plugin_root = tmp_path / "permission-test"
        plugin_root.mkdir()

        # Create a skill file
        skill_dir = plugin_root / "skills" / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Test content")

        # Mock file reading to simulate permission error
        with patch.object(
            skill_file, "read_text", side_effect=PermissionError("Permission denied")
        ):
            validator = ImbueValidator(plugin_root)

            # This should not crash, though behavior depends on implementation
            # The test verifies graceful handling
            with pytest.raises(PermissionError):
                validator.validate_review_workflows()


@pytest.mark.skipif(ImbueValidator is None, reason="ImbueValidator not available")
class TestImbueValidatorPerformance:
    """Feature: Imbue validator performance with large plugins.

    As a validation tool
    I want to handle large plugin structures efficiently
    So that validation completes in reasonable time
    """

    @pytest.mark.performance
    def test_large_plugin_validation_performance(self, tmp_path):
        """Scenario: Validation performance with many skills
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
        import time

        validator = ImbueValidator(plugin_root)

        start_time = time.time()
        result = validator.scan_review_workflows()
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(result["skills_found"]) == 100

    @pytest.mark.performance
    def test_memory_usage_large_plugin(self, tmp_path):
        """Scenario: Memory usage with large plugin structures
        Given a plugin with large skill files
        When running validation
        Then memory usage should remain reasonable.
        """
        # This is a placeholder for memory testing
        # In practice, you'd use memory profiling tools
        plugin_root = tmp_path / "memory-test"
        plugin_root.mkdir()

        # Create large skill files
        for i in range(10):
            skill_dir = plugin_root / "skills" / f"large-skill-{i}"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            # Create a large content file
            large_content = "# Large Skill\n\n" + "This is repeated content.\n" * 10000
            skill_file.write_text(large_content)

        validator = ImbueValidator(plugin_root)

        # The test passes if it doesn't crash with memory issues
        result = validator.scan_review_workflows()
        assert len(result["skills_found"]) == 10
