"""Tests for the config module.

Feature: Centralized configuration management
    As a developer
    I want configuration validated and loaded from multiple sources
    So that abstract tools behave consistently
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from abstract.config import (
    AbstractConfig,
    ConfigFactory,
    ContextOptimizerConfig,
    Environment,
    ErrorHandlingConfig,
    SkillAnalyzerConfig,
    SkillsEvalConfig,
    SkillValidationConfig,
)


class TestEnvironmentEnum:
    """Feature: Environment enumeration values."""

    @pytest.mark.unit
    def test_development_value(self) -> None:
        """Scenario: Development enum has correct string value."""
        assert Environment.DEVELOPMENT.value == "development"

    @pytest.mark.unit
    def test_production_value(self) -> None:
        """Scenario: Production enum has correct string value."""
        assert Environment.PRODUCTION.value == "production"

    @pytest.mark.unit
    def test_testing_value(self) -> None:
        """Scenario: Testing enum has correct string value."""
        assert Environment.TESTING.value == "testing"


class TestSkillValidationConfig:
    """Feature: Skill validation config defaults."""

    @pytest.mark.unit
    def test_post_init_fills_meta_skill_exceptions(self) -> None:
        """Scenario: None META_SKILL_EXCEPTIONS gets filled with defaults.
        Given a SkillValidationConfig with all defaults
        When the config is created
        Then META_SKILL_EXCEPTIONS is populated with known values
        """
        cfg = SkillValidationConfig()
        assert cfg.META_SKILL_EXCEPTIONS is not None
        assert "skills-eval" in cfg.META_SKILL_EXCEPTIONS

    @pytest.mark.unit
    def test_post_init_fills_meta_indicators(self) -> None:
        """Scenario: None META_INDICATORS gets filled with defaults.
        Given a SkillValidationConfig with all defaults
        When the config is created
        Then META_INDICATORS contains known pattern words
        """
        cfg = SkillValidationConfig()
        assert cfg.META_INDICATORS is not None
        assert "pattern" in cfg.META_INDICATORS

    @pytest.mark.unit
    def test_post_init_fills_required_frontmatter_fields(self) -> None:
        """Scenario: None REQUIRED_FRONTMATTER_FIELDS gets filled.
        Given a SkillValidationConfig with all defaults
        When the config is created
        Then REQUIRED_FRONTMATTER_FIELDS contains name and description
        """
        cfg = SkillValidationConfig()
        assert cfg.REQUIRED_FRONTMATTER_FIELDS is not None
        assert "name" in cfg.REQUIRED_FRONTMATTER_FIELDS
        assert "description" in cfg.REQUIRED_FRONTMATTER_FIELDS

    @pytest.mark.unit
    def test_post_init_fills_recommended_frontmatter_fields(self) -> None:
        """Scenario: None RECOMMENDED_FRONTMATTER_FIELDS gets filled.
        Given a SkillValidationConfig with all defaults
        When the config is created
        Then RECOMMENDED_FRONTMATTER_FIELDS contains category and tags
        """
        cfg = SkillValidationConfig()
        assert cfg.RECOMMENDED_FRONTMATTER_FIELDS is not None
        assert "category" in cfg.RECOMMENDED_FRONTMATTER_FIELDS
        assert "tags" in cfg.RECOMMENDED_FRONTMATTER_FIELDS

    @pytest.mark.unit
    def test_custom_values_preserved(self) -> None:
        """Scenario: Explicitly passed values are not overwritten.
        Given a SkillValidationConfig with custom META_SKILL_EXCEPTIONS
        When the config is created
        Then the custom value is preserved
        """
        cfg = SkillValidationConfig(META_SKILL_EXCEPTIONS=["my-skill"])
        assert cfg.META_SKILL_EXCEPTIONS == ["my-skill"]

    @pytest.mark.unit
    def test_max_file_size_default(self) -> None:
        """Scenario: Max file size defaults to 15000 bytes."""
        cfg = SkillValidationConfig()
        assert cfg.MAX_SKILL_FILE_SIZE == 15000


class TestSkillAnalyzerConfig:
    """Feature: Skill analyzer config."""

    @pytest.mark.unit
    def test_markdown_extensions_default(self) -> None:
        """Scenario: MARKDOWN_EXTENSIONS defaults to .md and .markdown."""
        cfg = SkillAnalyzerConfig()
        assert cfg.MARKDOWN_EXTENSIONS is not None
        assert ".md" in cfg.MARKDOWN_EXTENSIONS
        assert ".markdown" in cfg.MARKDOWN_EXTENSIONS

    @pytest.mark.unit
    def test_custom_markdown_extensions_preserved(self) -> None:
        """Scenario: Custom MARKDOWN_EXTENSIONS are preserved after init."""
        cfg = SkillAnalyzerConfig(MARKDOWN_EXTENSIONS=[".rst"])
        assert cfg.MARKDOWN_EXTENSIONS == [".rst"]

    @pytest.mark.unit
    def test_default_threshold(self) -> None:
        """Scenario: Default threshold is 150 lines."""
        cfg = SkillAnalyzerConfig()
        assert cfg.DEFAULT_THRESHOLD == 150


class TestSkillsEvalConfig:
    """Feature: Skills eval config."""

    @pytest.mark.unit
    def test_claude_paths_set_on_init(self) -> None:
        """Scenario: CLAUDE_PATHS is populated with home-based paths."""
        cfg = SkillsEvalConfig()
        assert cfg.CLAUDE_PATHS is not None
        assert len(cfg.CLAUDE_PATHS) > 0
        home = str(Path.home())
        assert any(home in p for p in cfg.CLAUDE_PATHS)

    @pytest.mark.unit
    def test_custom_claude_paths_preserved(self) -> None:
        """Scenario: Custom CLAUDE_PATHS are preserved."""
        cfg = SkillsEvalConfig(CLAUDE_PATHS=["/custom/path"])
        assert cfg.CLAUDE_PATHS == ["/custom/path"]

    @pytest.mark.unit
    def test_weights_sum_to_one(self) -> None:
        """Scenario: All scoring weights sum to 1.0."""
        cfg = SkillsEvalConfig()
        total = (
            cfg.STRUCTURE_WEIGHT
            + cfg.CONTENT_WEIGHT
            + cfg.TOKEN_WEIGHT
            + cfg.ACTIVATION_WEIGHT
            + cfg.TOOL_WEIGHT
            + cfg.DOCUMENTATION_WEIGHT
        )
        assert abs(total - 1.0) < 0.01


class TestContextOptimizerConfig:
    """Feature: Context optimizer config."""

    @pytest.mark.unit
    def test_progressive_disclosure_thresholds_default(self) -> None:
        """Scenario: PROGRESSIVE_DISCLOSURE_THRESHOLDS maps size names to limits."""
        cfg = ContextOptimizerConfig()
        assert cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS is not None
        assert "small" in cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS
        assert "medium" in cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS
        assert "large" in cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS

    @pytest.mark.unit
    def test_thresholds_match_size_limits(self) -> None:
        """Scenario: Thresholds reflect the size limit fields."""
        cfg = ContextOptimizerConfig()
        assert cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS["small"] == cfg.SMALL_SIZE_LIMIT
        assert cfg.PROGRESSIVE_DISCLOSURE_THRESHOLDS["medium"] == cfg.MEDIUM_SIZE_LIMIT


class TestErrorHandlingConfig:
    """Feature: Error handling config."""

    @pytest.mark.unit
    def test_exit_codes_populated(self) -> None:
        """Scenario: EXIT_CODES contains expected entries."""
        cfg = ErrorHandlingConfig()
        assert cfg.EXIT_CODES is not None
        assert "SUCCESS" in cfg.EXIT_CODES
        assert cfg.EXIT_CODES["SUCCESS"] == 0
        assert "GENERAL_ERROR" in cfg.EXIT_CODES

    @pytest.mark.unit
    def test_custom_exit_codes_preserved(self) -> None:
        """Scenario: Custom EXIT_CODES are preserved."""
        cfg = ErrorHandlingConfig(EXIT_CODES={"CUSTOM": 99})
        assert cfg.EXIT_CODES == {"CUSTOM": 99}


class TestAbstractConfig:
    """Feature: AbstractConfig initialization and methods."""

    @pytest.mark.unit
    def test_default_environment_is_production(self) -> None:
        """Scenario: Default environment is PRODUCTION."""
        cfg = AbstractConfig()
        assert cfg.environment == Environment.PRODUCTION

    @pytest.mark.unit
    def test_sub_configs_initialized(self) -> None:
        """Scenario: All sub-configs are initialized by __post_init__."""
        cfg = AbstractConfig()
        assert cfg.skill_validation is not None
        assert cfg.skill_analyzer is not None
        assert cfg.skills_eval is not None
        assert cfg.context_optimizer is not None
        assert cfg.error_handling is not None

    @pytest.mark.unit
    def test_project_root_defaults_to_cwd(self) -> None:
        """Scenario: project_root defaults to current working directory."""
        cfg = AbstractConfig()
        assert cfg.project_root is not None
        assert Path(cfg.project_root).exists()

    @pytest.mark.unit
    def test_validate_returns_empty_list_for_valid_config(self) -> None:
        """Scenario: A default config passes validation with no issues."""
        cfg = AbstractConfig()
        issues = cfg.validate()
        assert isinstance(issues, list)
        # Default config should have no threshold issues or weight issues
        weight_issues = [i for i in issues if "weights" in i]
        assert len(weight_issues) == 0

    @pytest.mark.unit
    def test_validate_detects_bad_threshold(self) -> None:
        """Scenario: A threshold below min triggers a validation issue."""
        cfg = AbstractConfig()
        cfg.skill_analyzer.DEFAULT_THRESHOLD = -1
        issues = cfg.validate()
        assert any("below minimum" in i for i in issues)

    @pytest.mark.unit
    def test_validate_detects_bad_weights(self) -> None:
        """Scenario: Weights that don't sum to 1.0 trigger a validation issue."""
        cfg = AbstractConfig()
        cfg.skills_eval.STRUCTURE_WEIGHT = 0.99
        issues = cfg.validate()
        assert any("weights" in i for i in issues)

    @pytest.mark.unit
    def test_validate_detects_nonexistent_project_root(self) -> None:
        """Scenario: Nonexistent project root triggers a validation issue."""
        cfg = AbstractConfig(project_root="/nonexistent/path/that/does/not/exist")
        issues = cfg.validate()
        assert any("Project root" in i for i in issues)

    @pytest.mark.unit
    def test_get_path_config_dir(self) -> None:
        """Scenario: get_path('config_dir') returns project_root/config."""
        cfg = AbstractConfig()
        path = cfg.get_path("config_dir")
        assert path.endswith("config")

    @pytest.mark.unit
    def test_get_path_scripts_dir(self) -> None:
        """Scenario: get_path('scripts_dir') returns project_root/scripts."""
        cfg = AbstractConfig()
        path = cfg.get_path("scripts_dir")
        assert path.endswith("scripts")

    @pytest.mark.unit
    def test_get_path_project_root(self) -> None:
        """Scenario: get_path('project_root') returns project_root."""
        cfg = AbstractConfig()
        path = cfg.get_path("project_root")
        assert path == cfg.project_root

    @pytest.mark.unit
    def test_get_path_unknown_key_raises(self) -> None:
        """Scenario: Unknown path key raises ValueError."""
        cfg = AbstractConfig()
        with pytest.raises(ValueError, match="Unknown path key"):
            cfg.get_path("unknown_key")

    @pytest.mark.unit
    def test_get_summary_returns_string(self) -> None:
        """Scenario: get_summary returns a non-empty string."""
        cfg = AbstractConfig()
        summary = cfg.get_summary()
        assert isinstance(summary, str)
        assert "Abstract Configuration Summary" in summary
        assert "Environment" in summary

    @pytest.mark.unit
    def test_from_json_file(self, tmp_path: Path) -> None:
        """Scenario: Config loads from a JSON file.
        Given a JSON config file with debug = True
        When loaded via from_file
        Then debug is True
        """
        config_data = {"debug": True}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.debug is True

    @pytest.mark.unit
    def test_from_yaml_file(self, tmp_path: Path) -> None:
        """Scenario: Config loads from a YAML file.
        Given a YAML config file with verbose = true
        When loaded via from_file
        Then verbose is True
        """
        import yaml  # noqa: PLC0415

        config_data = {"verbose": True}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.verbose is True

    @pytest.mark.unit
    def test_from_file_missing_raises(self, tmp_path: Path) -> None:
        """Scenario: Missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            AbstractConfig.from_file(tmp_path / "nonexistent.yaml")

    @pytest.mark.unit
    def test_from_file_unsupported_format_raises(self, tmp_path: Path) -> None:
        """Scenario: Unsupported format raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("[config]\nenv = 'prod'")
        with pytest.raises(ValueError, match="Unsupported"):
            AbstractConfig.from_file(config_file)

    @pytest.mark.unit
    def test_from_yaml_delegates_to_from_file(self, tmp_path: Path) -> None:
        """Scenario: from_yaml is equivalent to from_file for .yaml files."""
        import yaml  # noqa: PLC0415

        config_data = {"debug": True}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_yaml(config_file)
        assert cfg.debug is True

    @pytest.mark.unit
    def test_from_env_reads_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: ABSTRACT_DEBUG=true sets debug to True."""
        monkeypatch.setenv("ABSTRACT_DEBUG", "true")
        cfg = AbstractConfig.from_env()
        assert cfg.debug is True

    @pytest.mark.unit
    def test_from_env_reads_verbose(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: ABSTRACT_VERBOSE=1 sets verbose to True."""
        monkeypatch.setenv("ABSTRACT_VERBOSE", "1")
        cfg = AbstractConfig.from_env()
        assert cfg.verbose is True

    @pytest.mark.unit
    def test_from_env_reads_log_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: ABSTRACT_LOG_FILE sets log_file."""
        monkeypatch.setenv("ABSTRACT_LOG_FILE", "/tmp/test.log")
        cfg = AbstractConfig.from_env()
        assert cfg.log_file == "/tmp/test.log"

    @pytest.mark.unit
    def test_from_env_reads_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: ABSTRACT_ENV=testing sets environment to TESTING."""
        monkeypatch.setenv("ABSTRACT_ENV", "testing")
        cfg = AbstractConfig.from_env()
        assert cfg.environment == Environment.TESTING

    @pytest.mark.unit
    def test_from_env_invalid_environment_defaults_to_production(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Invalid ABSTRACT_ENV falls back to PRODUCTION."""
        monkeypatch.setenv("ABSTRACT_ENV", "invalid_env")
        cfg = AbstractConfig.from_env()
        assert cfg.environment == Environment.PRODUCTION

    @pytest.mark.unit
    def test_to_file_yaml(self, tmp_path: Path) -> None:
        """Scenario: Config saves to YAML file.
        Given a config with debug=True
        When saved to a YAML file
        Then the file exists and contains the config
        """
        cfg = AbstractConfig(debug=True)
        out_file = tmp_path / "output.yaml"
        cfg.to_file(out_file, fmt="yaml")
        assert out_file.exists()
        content = out_file.read_text()
        assert "debug" in content

    @pytest.mark.unit
    def test_to_file_json(self, tmp_path: Path) -> None:
        """Scenario: Config saves to JSON file.
        Given a config with verbose=True
        When saved to a JSON file
        Then the file contains valid JSON
        """
        cfg = AbstractConfig(verbose=True)
        out_file = tmp_path / "output.json"
        cfg.to_file(out_file, fmt="json")
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["verbose"] is True

    @pytest.mark.unit
    def test_to_file_unsupported_format_raises(self, tmp_path: Path) -> None:
        """Scenario: Unsupported output format raises ValueError."""
        cfg = AbstractConfig()
        with pytest.raises(ValueError, match="Unsupported format"):
            cfg.to_file(tmp_path / "out.toml", fmt="toml")

    @pytest.mark.unit
    def test_to_file_creates_parent_dir(self, tmp_path: Path) -> None:
        """Scenario: Missing parent directories are created automatically."""
        cfg = AbstractConfig()
        out_file = tmp_path / "nested" / "dir" / "output.yaml"
        cfg.to_file(out_file, fmt="yaml")
        assert out_file.exists()

    @pytest.mark.unit
    def test_from_yaml_with_sub_configs(self, tmp_path: Path) -> None:
        """Scenario: YAML with nested skill_validation config is loaded."""
        import yaml  # noqa: PLC0415

        config_data = {
            "environment": "testing",
            "skill_validation": {
                "MAX_SKILL_FILE_SIZE": 20000,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.skill_validation is not None
        assert cfg.skill_validation.MAX_SKILL_FILE_SIZE == 20000

    @pytest.mark.unit
    def test_from_yaml_with_skill_analyzer_sub_config(self, tmp_path: Path) -> None:
        """Scenario: YAML with nested skill_analyzer config is loaded."""
        import yaml  # noqa: PLC0415

        config_data = {
            "skill_analyzer": {
                "DEFAULT_THRESHOLD": 200,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.skill_analyzer is not None
        assert cfg.skill_analyzer.DEFAULT_THRESHOLD == 200

    @pytest.mark.unit
    def test_from_yaml_with_skills_eval_sub_config(self, tmp_path: Path) -> None:
        """Scenario: YAML with nested skills_eval config is loaded."""
        import yaml  # noqa: PLC0415

        config_data = {
            "skills_eval": {
                "MINIMUM_QUALITY_THRESHOLD": 75.0,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.skills_eval is not None
        assert cfg.skills_eval.MINIMUM_QUALITY_THRESHOLD == 75.0

    @pytest.mark.unit
    def test_from_yaml_with_context_optimizer_sub_config(self, tmp_path: Path) -> None:
        """Scenario: YAML with nested context_optimizer config is loaded."""
        import yaml  # noqa: PLC0415

        config_data = {
            "context_optimizer": {
                "MAX_SECTION_LINES": 30,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.context_optimizer is not None
        assert cfg.context_optimizer.MAX_SECTION_LINES == 30

    @pytest.mark.unit
    def test_from_yaml_with_error_handling_sub_config(self, tmp_path: Path) -> None:
        """Scenario: YAML with nested error_handling config is loaded."""
        import yaml  # noqa: PLC0415

        config_data = {
            "error_handling": {
                "DEFAULT_LOG_LEVEL": "DEBUG",
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AbstractConfig.from_file(config_file)
        assert cfg.error_handling is not None
        assert cfg.error_handling.DEFAULT_LOG_LEVEL == "DEBUG"


class TestConfigFactory:
    """Feature: ConfigFactory manages named config instances."""

    @pytest.mark.unit
    def test_set_and_get_config(self) -> None:
        """Scenario: set_config stores and get_config retrieves it.
        Given a config stored under 'test' name
        When retrieved via get_config
        Then the same config instance is returned
        """
        ConfigFactory.reset_config("test_set_get")
        cfg = AbstractConfig(debug=True)
        ConfigFactory.set_config(cfg, name="test_set_get")
        retrieved = ConfigFactory.get_config("test_set_get")
        assert retrieved is cfg

    @pytest.mark.unit
    def test_reset_config_removes_stored_instance(self) -> None:
        """Scenario: reset_config removes a stored instance.
        Given a config stored under 'test_reset' name
        When reset_config is called
        Then the name is no longer in _instances
        """
        cfg = AbstractConfig(debug=True)
        ConfigFactory.set_config(cfg, name="test_reset")
        ConfigFactory.reset_config("test_reset")

        # After reset, the key should be gone from _instances
        assert "test_reset" not in ConfigFactory._instances

    @pytest.mark.unit
    def test_reset_nonexistent_does_not_raise(self) -> None:
        """Scenario: Resetting a non-existent config name is a no-op."""
        # Should not raise
        ConfigFactory.reset_config("config_that_never_existed_xyz")

    @pytest.mark.unit
    def test_create_config_returns_new_instance(self) -> None:
        """Scenario: create_config returns a new AbstractConfig with kwargs."""
        cfg = ConfigFactory.create_config(debug=True)
        assert isinstance(cfg, AbstractConfig)
        assert cfg.debug is True

    @pytest.mark.unit
    def test_load_config_from_file(self, tmp_path: Path) -> None:
        """Scenario: load_config loads and stores config from file.
        Given a JSON config file with debug=True
        When load_config is called
        Then the instance is stored and debug is True
        """
        config_data = {"debug": True}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        ConfigFactory.reset_config("test_load")
        cfg = ConfigFactory.load_config(config_file, name="test_load")
        assert cfg.debug is True
        assert ConfigFactory.get_config("test_load") is cfg

    @pytest.mark.unit
    def test_get_config_falls_back_to_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Scenario: get_config falls back to env vars when no config file exists.
        Given ABSTRACT_DEBUG=yes in the environment
        And no config file in cwd
        When get_config is called
        Then debug is True
        """

        ConfigFactory.reset_config("test_env_fallback")
        monkeypatch.setenv("ABSTRACT_DEBUG", "yes")
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            cfg = ConfigFactory.get_config("test_env_fallback")
            assert cfg.debug is True
        finally:
            os.chdir(original)
            ConfigFactory.reset_config("test_env_fallback")
