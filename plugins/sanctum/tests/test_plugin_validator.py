"""Tests for plugin.json validation."""


from sanctum.validators import PluginValidationResult, PluginValidator


class TestPluginValidationResult:
    """Tests for PluginValidationResult dataclass."""

    def test_valid_result_creation(self):
        """Valid result has no errors and is_valid is True."""
        result = PluginValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            plugin_name="test-plugin",
            plugin_version="1.0.0",
        )
        assert result.is_valid
        assert result.errors == []
        assert result.plugin_name == "test-plugin"

    def test_invalid_result_with_errors(self):
        """Invalid result has errors and is_valid is False."""
        result = PluginValidationResult(
            is_valid=False,
            errors=["Missing required field: version"],
            warnings=[],
            plugin_name="broken-plugin",
            plugin_version=None,
        )
        assert not result.is_valid
        assert "Missing required field: version" in result.errors

    def test_result_with_warnings_still_valid(self):
        """Result with only warnings is still valid."""
        result = PluginValidationResult(
            is_valid=True,
            errors=[],
            warnings=["No keywords defined"],
            plugin_name="minimal-plugin",
            plugin_version="1.0.0",
        )
        assert result.is_valid
        assert "No keywords defined" in result.warnings


class TestPluginValidatorRequiredFields:
    """Tests for required field validation in plugin.json."""

    def test_validates_complete_plugin_json(self, sample_plugin_json):
        """Complete plugin.json passes validation."""
        result = PluginValidator.validate_structure(sample_plugin_json)
        assert result.is_valid
        assert result.errors == []

    def test_validates_minimal_plugin_json(self, sample_plugin_json_minimal):
        """Minimal plugin.json with only required fields passes."""
        result = PluginValidator.validate_structure(sample_plugin_json_minimal)
        assert result.is_valid
        assert result.plugin_name == "minimal-plugin"
        assert result.plugin_version == "1.0.0"

    def test_fails_when_missing_name(self):
        """Plugin.json without name fails validation."""
        plugin_json = {"version": "1.0.0", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        assert not result.is_valid
        assert any("name" in error for error in result.errors)

    def test_fails_when_missing_version(self):
        """Plugin.json without version fails validation."""
        plugin_json = {"name": "test", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        assert not result.is_valid
        assert any("version" in error for error in result.errors)

    def test_fails_when_missing_description(self):
        """Plugin.json without description fails validation."""
        plugin_json = {"name": "test", "version": "1.0.0"}
        result = PluginValidator.validate_structure(plugin_json)
        assert not result.is_valid
        assert any("description" in error for error in result.errors)

    def test_fails_with_multiple_missing_fields(self, sample_plugin_json_invalid):
        """Plugin.json missing multiple fields reports all errors."""
        result = PluginValidator.validate_structure(sample_plugin_json_invalid)
        assert not result.is_valid
        assert len(result.errors) >= 2  # At least version and description missing


class TestPluginValidatorVersionFormat:
    """Tests for version format validation."""

    def test_valid_semver_version(self):
        """Standard semver version passes."""
        plugin_json = {"name": "test", "version": "1.0.0", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        assert result.is_valid

    def test_valid_semver_with_prerelease(self):
        """Semver with prerelease suffix passes."""
        plugin_json = {"name": "test", "version": "1.0.0-beta.1", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        assert result.is_valid

    def test_warns_on_non_standard_version(self):
        """Non-standard version format generates warning."""
        plugin_json = {"name": "test", "version": "latest", "description": "Test"}
        result = PluginValidator.validate_structure(plugin_json)
        # May be valid but with warning about version format
        assert result.is_valid or "version" in str(result.warnings)


class TestPluginValidatorPathValidation:
    """Tests for path reference validation in plugin.json."""

    def test_warns_on_empty_commands_array(self):
        """Empty commands array generates warning."""
        plugin_json = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "commands": [],
        }
        result = PluginValidator.validate_structure(plugin_json)
        assert result.is_valid
        assert any("commands" in warning.lower() for warning in result.warnings)

    def test_warns_on_empty_skills_array(self):
        """Empty skills array generates warning."""
        plugin_json = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "skills": [],
        }
        result = PluginValidator.validate_structure(plugin_json)
        assert result.is_valid
        assert any("skills" in warning.lower() for warning in result.warnings)

    def test_validates_path_format(self):
        """Path references should start with ./."""
        plugin_json = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "commands": ["commands/test.md"],  # Missing ./
        }
        result = PluginValidator.validate_structure(plugin_json)
        # Either error or warning about path format
        assert not result.is_valid or "path" in str(result.warnings).lower()


class TestPluginValidatorFileCheck:
    """Tests for validating that referenced files exist."""

    def test_validates_existing_files(self, temp_full_plugin):
        """Validation passes when all referenced files exist."""
        result = PluginValidator.validate_plugin_dir(temp_full_plugin)
        assert result.is_valid

    def test_fails_when_command_file_missing(self, temp_plugin_dir):
        """Validation fails when a referenced command file is missing."""
        # temp_plugin_dir has plugin.json but no actual command files
        result = PluginValidator.validate_plugin_dir(temp_plugin_dir)
        assert not result.is_valid
        assert any("command" in error.lower() for error in result.errors)

    def test_fails_when_skill_dir_missing(self, temp_plugin_dir):
        """Validation fails when a referenced skill directory is missing."""
        result = PluginValidator.validate_plugin_dir(temp_plugin_dir)
        assert not result.is_valid
        assert any("skill" in error.lower() for error in result.errors)

    def test_validates_skill_has_skill_md(self, tmp_path, sample_plugin_json):
        """Skill directories must contain SKILL.md file."""
        # Create plugin.json
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            '{"name":"test","version":"1.0.0","description":"t","skills":["./skills/test-skill"]}'
        )

        # Create skill directory WITHOUT SKILL.md
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        result = PluginValidator.validate_plugin_dir(tmp_path)
        assert not result.is_valid
        assert any("SKILL.md" in error for error in result.errors)


class TestPluginValidatorFromFile:
    """Tests for loading and validating plugin.json from file."""

    def test_validates_from_plugin_dir(self, temp_full_plugin):
        """Can validate a complete plugin directory."""
        result = PluginValidator.validate_plugin_dir(temp_full_plugin)
        assert result.is_valid
        assert result.plugin_name == "sanctum"

    def test_fails_when_plugin_json_missing(self, tmp_path):
        """Fails when .claude-plugin/plugin.json is missing."""
        result = PluginValidator.validate_plugin_dir(tmp_path)
        assert not result.is_valid
        assert any("plugin.json" in error for error in result.errors)

    def test_fails_on_invalid_json(self, tmp_path):
        """Fails when plugin.json contains invalid JSON."""
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text("{invalid json content}")

        result = PluginValidator.validate_plugin_dir(tmp_path)
        assert not result.is_valid
        assert any("JSON" in error or "parse" in error.lower() for error in result.errors)
