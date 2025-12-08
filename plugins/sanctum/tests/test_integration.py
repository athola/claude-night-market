"""Integration tests for full plugin validation."""

import pytest

from sanctum.validators import SanctumValidationReport, SanctumValidator


class TestSanctumValidationReport:
    """Tests for the full validation report dataclass."""

    def test_report_creation(self):
        """Creates a complete validation report."""
        report = SanctumValidationReport(
            is_valid=True,
            total_errors=0,
            total_warnings=2,
        )
        assert report.is_valid
        assert report.total_warnings == 2
        assert report.total_errors == 0

    def test_report_invalid_when_errors_exist(self):
        """Report is invalid when any component fails."""
        report = SanctumValidationReport(
            is_valid=False,
            total_errors=1,
            total_warnings=0,
        )
        assert not report.is_valid
        assert report.total_errors == 1


class TestSanctumValidatorFullPlugin:
    """Integration tests for validating complete plugins."""

    @pytest.mark.integration
    def test_validates_complete_plugin(self, temp_full_plugin):
        """Validates a complete temporary plugin structure."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert report.is_valid
        assert report.plugin_result is not None
        assert report.plugin_result.is_valid

    @pytest.mark.integration
    def test_validates_real_sanctum_plugin(self, sanctum_plugin_root):
        """Validates the actual sanctum plugin structure."""
        report = SanctumValidator.validate_plugin(sanctum_plugin_root)
        # The real plugin should be valid
        assert report.is_valid, f"Errors: {report.all_errors()}"

    @pytest.mark.integration
    def test_collects_all_errors(self, tmp_path):
        """Collects errors from all components."""
        # Create minimal broken plugin
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            '{"name":"broken","version":"1.0.0","description":"t",'
            '"skills":["./skills/missing"],"commands":["./commands/missing.md"]}'
        )

        report = SanctumValidator.validate_plugin(tmp_path)
        assert not report.is_valid
        assert report.total_errors >= 2  # At least skill and command missing

    @pytest.mark.integration
    def test_returns_component_results(self, temp_full_plugin):
        """Report includes validation results for each component."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert hasattr(report, "plugin_result")
        assert hasattr(report, "skill_results")
        assert hasattr(report, "command_results")
        assert hasattr(report, "agent_results")


class TestSanctumValidatorSkillScanning:
    """Integration tests for skill scanning."""

    @pytest.mark.integration
    def test_scans_all_skills(self, temp_full_plugin):
        """Scans and validates all skills in the plugin."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        # Our fixture has 2 skills based on sample_plugin_json
        assert len(report.skill_results) >= 2

    @pytest.mark.integration
    def test_reports_skill_metadata(self, temp_full_plugin):
        """Reports metadata for each skill."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        for skill_result in report.skill_results:
            assert skill_result.skill_name is not None

    @pytest.mark.integration
    def test_scans_real_sanctum_skills(self, sanctum_plugin_root):
        """Scans skills in the actual sanctum plugin."""
        report = SanctumValidator.validate_plugin(sanctum_plugin_root)
        skill_names = [s.skill_name for s in report.skill_results]
        # At least some skills should be present
        assert len(skill_names) >= 1


class TestSanctumValidatorCommandScanning:
    """Integration tests for command scanning."""

    @pytest.mark.integration
    def test_scans_all_commands(self, temp_full_plugin):
        """Scans and validates all commands in the plugin."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert len(report.command_results) >= 2

    @pytest.mark.integration
    def test_scans_real_sanctum_commands(self, sanctum_plugin_root):
        """Scans commands in the actual sanctum plugin."""
        report = SanctumValidator.validate_plugin(sanctum_plugin_root)
        # At least some commands should be present
        assert len(report.command_results) >= 1


class TestSanctumValidatorAgentScanning:
    """Integration tests for agent scanning."""

    @pytest.mark.integration
    def test_scans_all_agents(self, temp_full_plugin):
        """Scans and validates all agents in the plugin."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert len(report.agent_results) >= 1

    @pytest.mark.integration
    def test_scans_real_sanctum_agents(self, sanctum_plugin_root):
        """Scans agents in the actual sanctum plugin."""
        report = SanctumValidator.validate_plugin(sanctum_plugin_root)
        # At least some agents should be present
        assert len(report.agent_results) >= 1


class TestSanctumValidatorErrorCollection:
    """Integration tests for error and warning collection."""

    @pytest.mark.integration
    def test_all_errors_method(self, tmp_path):
        """all_errors() collects errors from all components."""
        # Create minimal broken plugin
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            '{"name":"broken","version":"1.0.0","description":"t",'
            '"skills":["./skills/missing"]}'
        )

        report = SanctumValidator.validate_plugin(tmp_path)
        all_errors = report.all_errors()
        assert len(all_errors) >= 1
        assert any("skill" in e.lower() or "missing" in e.lower() for e in all_errors)

    @pytest.mark.integration
    def test_counts_totals(self, temp_full_plugin):
        """Report tracks total errors and warnings."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert isinstance(report.total_errors, int)
        assert isinstance(report.total_warnings, int)
        assert report.total_errors >= 0
        assert report.total_warnings >= 0


class TestSanctumValidatorReport:
    """Tests for validation report generation."""

    @pytest.mark.integration
    def test_report_is_valid_with_no_errors(self, temp_full_plugin):
        """Report is valid when no errors exist."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert report.is_valid == (report.total_errors == 0)

    @pytest.mark.integration
    def test_report_has_plugin_result(self, temp_full_plugin):
        """Report includes plugin-level validation result."""
        report = SanctumValidator.validate_plugin(temp_full_plugin)
        assert report.plugin_result is not None
        assert report.plugin_result.plugin_name == "sanctum"

    @pytest.mark.integration
    def test_minimal_plugin_validation(self, tmp_path):
        """Validates a minimal plugin structure."""
        # Create minimal valid plugin
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            '{"name":"minimal","version":"1.0.0","description":"Minimal plugin"}'
        )

        report = SanctumValidator.validate_plugin(tmp_path)
        # Minimal plugin should be valid
        assert report.is_valid
