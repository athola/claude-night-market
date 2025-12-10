"""Tests for plugin.json validation."""

from sanctum.validators import PluginValidationResult, PluginValidator


class TestPluginValidationResult:
    """Tests for PluginValidationResult dataclass."""

    def test_valid_result_creation(self) -> None:

    def test_validates_complete_plugin_json(self, sample_plugin_json) -> None:
        plugin_json = {"name": "test", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        assert not result.is_valid
        assert any("version" in error for error in result.errors)

    def test_fails_when_missing_description(self) -> None:

    def test_valid_semver_version(self) -> None:

    def test_warns_on_empty_commands_array(self) -> None:

    def test_validates_existing_files(self, temp_full_plugin) -> None:
        # Create plugin.json
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            '{"name":"test","version":"1.0.0","description":"t","skills":["./skills/test-skill"]}',
        )

        # Create skill directory WITHOUT SKILL.md
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        result = PluginValidator.validate_plugin_dir(tmp_path)
        assert not result.is_valid
        assert any("SKILL.md" in error for error in result.errors)


class TestPluginValidatorFromFile:
    """Tests for loading and validating plugin.json from file."""

    def test_validates_from_plugin_dir(self, temp_full_plugin) -> None:
