"""Integration tests for full plugin validation."""

import pytest

from sanctum.validators import SanctumValidationReport, SanctumValidator


class TestSanctumValidationReport:
    """Tests for the full validation report dataclass."""

    def test_report_creation(self) -> None:

    @pytest.mark.integration
    def test_validates_complete_plugin(self, temp_full_plugin) -> None:
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert hasattr(report, "plugin_result")
        assert hasattr(report, "skill_results")
        assert hasattr(report, "command_results")
        assert hasattr(report, "agent_results")


class TestSanctumValidatorSkillScanning:
    """Integration tests for skill scanning."""

    @pytest.mark.integration
    def test_scans_all_skills(self, temp_full_plugin) -> None:

    @pytest.mark.integration
    def test_scans_all_commands(self, temp_full_plugin) -> None:

    @pytest.mark.integration
    def test_scans_all_agents(self, temp_full_plugin) -> None:

    @pytest.mark.integration
    def test_all_errors_method(self, tmp_path) -> None:

    @pytest.mark.integration
    def test_report_is_valid_with_no_errors(self, temp_full_plugin) -> None:
