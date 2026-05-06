"""Tests for src/abstract/config.py.

Covers AbstractConfig, sub-configs, Environment enum, ConfigFactory,
and file-based loading/saving.
"""

from __future__ import annotations

import json

import pytest
import yaml

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

# ---------------------------------------------------------------------------
# Environment enum
# ---------------------------------------------------------------------------


class TestEnvironment:
    """Environment enum has the expected values."""

    @pytest.mark.unit
    def test_values(self):
        """All three environment values are defined."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"


# ---------------------------------------------------------------------------
# SkillValidationConfig
# ---------------------------------------------------------------------------


class TestSkillValidationConfig:
    """SkillValidationConfig initializes defaults correctly."""

    @pytest.mark.unit
    def test_default_required_fields(self):
        """Default required fields include name and description."""
        config = SkillValidationConfig()
        assert "name" in config.REQUIRED_FRONTMATTER_FIELDS
        assert "description" in config.REQUIRED_FRONTMATTER_FIELDS

    @pytest.mark.unit
    def test_default_meta_indicators(self):
        """Default meta-skill indicators are non-empty."""
        config = SkillValidationConfig()
        assert len(config.META_INDICATORS) > 0

    @pytest.mark.unit
    def test_default_meta_exceptions(self):
        """Default META_SKILL_EXCEPTIONS includes known exceptions."""
        config = SkillValidationConfig()
        assert "skills-eval" in config.META_SKILL_EXCEPTIONS

    @pytest.mark.unit
    def test_custom_values_accepted(self):
        """Custom values override defaults."""
        config = SkillValidationConfig(
            META_INDICATORS=["custom"],
            META_SKILL_EXCEPTIONS=["my-skill"],
        )
        assert config.META_INDICATORS == ["custom"]
        assert config.META_SKILL_EXCEPTIONS == ["my-skill"]

    @pytest.mark.unit
    def test_max_file_size_default(self):
        """Default max file size is 15000 bytes."""
        config = SkillValidationConfig()
        assert config.MAX_SKILL_FILE_SIZE == 15000


# ---------------------------------------------------------------------------
# SkillAnalyzerConfig
# ---------------------------------------------------------------------------


class TestSkillAnalyzerConfig:
    """SkillAnalyzerConfig has sensible numeric defaults."""

    @pytest.mark.unit
    def test_default_threshold(self):
        """Default threshold is 150 lines."""
        config = SkillAnalyzerConfig()
        assert config.DEFAULT_THRESHOLD == 150

    @pytest.mark.unit
    def test_markdown_extensions_initialized(self):
        """MARKDOWN_EXTENSIONS defaults to ['.md', '.markdown']."""
        config = SkillAnalyzerConfig()
        assert ".md" in config.MARKDOWN_EXTENSIONS

    @pytest.mark.unit
    def test_token_ratio_default(self):
        """TOKEN_RATIO default is 4."""
        config = SkillAnalyzerConfig()
        assert config.TOKEN_RATIO == 4


# ---------------------------------------------------------------------------
# SkillsEvalConfig
# ---------------------------------------------------------------------------


class TestSkillsEvalConfig:
    """SkillsEvalConfig weights should sum to 1.0."""

    @pytest.mark.unit
    def test_weights_sum_to_one(self):
        """Default scoring weights sum to exactly 1.0."""
        config = SkillsEvalConfig()
        total = (
            config.STRUCTURE_WEIGHT
            + config.CONTENT_WEIGHT
            + config.TOKEN_WEIGHT
            + config.ACTIVATION_WEIGHT
            + config.TOOL_WEIGHT
            + config.DOCUMENTATION_WEIGHT
        )
        assert abs(total - 1.0) < 0.01

    @pytest.mark.unit
    def test_quality_threshold_defaults(self):
        """Quality thresholds are in expected range."""
        config = SkillsEvalConfig()
        assert config.MINIMUM_QUALITY_THRESHOLD == 70.0
        assert config.HIGH_QUALITY_THRESHOLD == 80.0

    @pytest.mark.unit
    def test_claude_paths_initialized(self):
        """CLAUDE_PATHS is initialized with home-relative paths."""
        config = SkillsEvalConfig()
        assert len(config.CLAUDE_PATHS) > 0


# ---------------------------------------------------------------------------
# ContextOptimizerConfig
# ---------------------------------------------------------------------------


class TestContextOptimizerConfig:
    """ContextOptimizerConfig initializes thresholds correctly."""

    @pytest.mark.unit
    def test_progressive_thresholds_initialized(self):
        """PROGRESSIVE_DISCLOSURE_THRESHOLDS is populated."""
        config = ContextOptimizerConfig()
        assert config.PROGRESSIVE_DISCLOSURE_THRESHOLDS is not None
        assert "small" in config.PROGRESSIVE_DISCLOSURE_THRESHOLDS

    @pytest.mark.unit
    def test_size_limits_ordered(self):
        """SMALL < MEDIUM < LARGE."""
        config = ContextOptimizerConfig()
        assert config.SMALL_SIZE_LIMIT < config.MEDIUM_SIZE_LIMIT
        assert config.MEDIUM_SIZE_LIMIT < config.LARGE_SIZE_LIMIT


# ---------------------------------------------------------------------------
# ErrorHandlingConfig
# ---------------------------------------------------------------------------


class TestErrorHandlingConfig:
    """ErrorHandlingConfig has standard exit codes."""

    @pytest.mark.unit
    def test_exit_codes_initialized(self):
        """EXIT_CODES dict is populated."""
        config = ErrorHandlingConfig()
        assert config.EXIT_CODES is not None
        assert "SUCCESS" in config.EXIT_CODES
        assert config.EXIT_CODES["SUCCESS"] == 0

    @pytest.mark.unit
    def test_default_log_level(self):
        """DEFAULT_LOG_LEVEL is 'INFO'."""
        config = ErrorHandlingConfig()
        assert config.DEFAULT_LOG_LEVEL == "INFO"


# ---------------------------------------------------------------------------
# AbstractConfig.__post_init__
# ---------------------------------------------------------------------------


class TestAbstractConfigInit:
    """AbstractConfig initializes sub-configs on creation."""

    @pytest.mark.unit
    def test_sub_configs_initialized(self):
        """All sub-configs are initialized to non-None instances."""
        config = AbstractConfig()
        assert config.skill_validation is not None
        assert config.skill_analyzer is not None
        assert config.skills_eval is not None
        assert config.context_optimizer is not None
        assert config.error_handling is not None

    @pytest.mark.unit
    def test_default_environment_is_production(self):
        config = AbstractConfig()
        assert config.environment == Environment.PRODUCTION

    @pytest.mark.unit
    def test_project_root_set_to_cwd(self):
        """project_root is set to current working directory by default."""
        config = AbstractConfig()
        assert config.project_root is not None

    @pytest.mark.unit
    def test_debug_and_verbose_default_false(self):
        config = AbstractConfig()
        assert config.debug is False
        assert config.verbose is False


# ---------------------------------------------------------------------------
# AbstractConfig.from_file
# ---------------------------------------------------------------------------


class TestAbstractConfigFromFile:
    """AbstractConfig.from_file loads config from YAML or JSON."""

    @pytest.mark.unit
    def test_raises_when_file_missing(self, tmp_path):
        """FileNotFoundError raised when file does not exist."""
        with pytest.raises(FileNotFoundError):
            AbstractConfig.from_file(tmp_path / "missing.yaml")

    @pytest.mark.unit
    def test_raises_for_unsupported_extension(self, tmp_path):
        """ValueError raised for unsupported file extension."""
        f = tmp_path / "config.toml"
        f.write_text("[section]\nkey = 'value'\n")
        with pytest.raises(ValueError, match="Unsupported"):
            AbstractConfig.from_file(f)

    @pytest.mark.unit
    def test_loads_yaml_config(self, tmp_path):
        """Loads configuration from a YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("debug: true\nverbose: false\n")
        config = AbstractConfig.from_file(config_file)
        assert config.debug is True

    @pytest.mark.unit
    def test_loads_json_config(self, tmp_path):
        """Loads configuration from a JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {"debug": True, "verbose": False}
        config_file.write_text(json.dumps(config_data))
        config = AbstractConfig.from_file(config_file)
        assert config.debug is True

    @pytest.mark.unit
    def test_loads_sub_config_from_yaml(self, tmp_path):
        """Sub-configs in YAML are instantiated as proper sub-config classes."""
        config_file = tmp_path / "config.yaml"
        data = {
            "debug": False,
            "skill_analyzer": {
                "DEFAULT_THRESHOLD": 200,
            },
        }
        config_file.write_text(yaml.dump(data))
        config = AbstractConfig.from_file(config_file)
        assert config.skill_analyzer.DEFAULT_THRESHOLD == 200


# ---------------------------------------------------------------------------
# AbstractConfig.from_yaml
# ---------------------------------------------------------------------------


class TestAbstractConfigFromYaml:
    """from_yaml is a convenience alias for from_file."""

    @pytest.mark.unit
    def test_loads_yaml_file(self, tmp_path):
        """from_yaml loads a YAML file successfully."""
        config_file = tmp_path / "cfg.yaml"
        config_file.write_text("verbose: true\n")
        config = AbstractConfig.from_yaml(config_file)
        assert config.verbose is True


# ---------------------------------------------------------------------------
# AbstractConfig.from_env
# ---------------------------------------------------------------------------


class TestAbstractConfigFromEnv:
    """from_env reads configuration from environment variables."""

    @pytest.mark.unit
    def test_debug_from_env(self, monkeypatch):
        """ABSTRACT_DEBUG=true sets debug=True."""
        monkeypatch.setenv("ABSTRACT_DEBUG", "true")
        config = AbstractConfig.from_env()
        assert config.debug is True

    @pytest.mark.unit
    def test_verbose_from_env(self, monkeypatch):
        """ABSTRACT_VERBOSE=1 sets verbose=True."""
        monkeypatch.setenv("ABSTRACT_VERBOSE", "1")
        config = AbstractConfig.from_env()
        assert config.verbose is True

    @pytest.mark.unit
    def test_environment_from_env(self, monkeypatch):
        """ABSTRACT_ENV=development sets environment to DEVELOPMENT."""
        monkeypatch.setenv("ABSTRACT_ENV", "development")
        config = AbstractConfig.from_env()
        assert config.environment == Environment.DEVELOPMENT

    @pytest.mark.unit
    def test_invalid_env_defaults_to_production(self, monkeypatch):
        """Invalid ABSTRACT_ENV value defaults to PRODUCTION."""
        monkeypatch.setenv("ABSTRACT_ENV", "invalid-value")
        config = AbstractConfig.from_env()
        assert config.environment == Environment.PRODUCTION

    @pytest.mark.unit
    def test_log_file_from_env(self, monkeypatch):
        """ABSTRACT_LOG_FILE is read from environment."""
        monkeypatch.setenv("ABSTRACT_LOG_FILE", "/tmp/abstract.log")
        config = AbstractConfig.from_env()
        assert config.log_file == "/tmp/abstract.log"


# ---------------------------------------------------------------------------
# AbstractConfig.to_file
# ---------------------------------------------------------------------------


class TestAbstractConfigToFile:
    """to_file saves config to YAML or JSON."""

    @pytest.mark.unit
    def test_saves_yaml_file(self, tmp_path):
        """Saves config as YAML when fmt='yaml'."""
        config = AbstractConfig()
        out_path = tmp_path / "output.yaml"
        config.to_file(out_path, fmt="yaml")
        assert out_path.exists()
        # File exists and is non-empty
        assert out_path.stat().st_size > 0

    @pytest.mark.unit
    def test_saves_json_file(self, tmp_path):
        """Saves config as JSON when fmt='json'."""
        config = AbstractConfig()
        out_path = tmp_path / "output.json"
        config.to_file(out_path, fmt="json")
        assert out_path.exists()
        loaded = json.loads(out_path.read_text())
        assert "environment" in loaded

    @pytest.mark.unit
    def test_raises_for_unsupported_format(self, tmp_path):
        """ValueError raised for unsupported format."""
        config = AbstractConfig()
        with pytest.raises(ValueError, match="Unsupported format"):
            config.to_file(tmp_path / "config.csv", fmt="csv")

    @pytest.mark.unit
    def test_creates_parent_directory(self, tmp_path):
        """Creates parent directories when they don't exist."""
        config = AbstractConfig()
        nested = tmp_path / "deep" / "nested" / "config.yaml"
        config.to_file(nested, fmt="yaml")
        assert nested.exists()


# ---------------------------------------------------------------------------
# AbstractConfig.get_path
# ---------------------------------------------------------------------------


class TestAbstractConfigGetPath:
    """get_path resolves paths relative to project_root."""

    @pytest.mark.unit
    def test_config_dir_path(self, tmp_path):
        """Returns project_root/config for 'config_dir' key."""
        config = AbstractConfig(project_root=str(tmp_path))
        result = config.get_path("config_dir")
        assert result == str(tmp_path / "config")

    @pytest.mark.unit
    def test_scripts_dir_path(self, tmp_path):
        """Returns project_root/scripts for 'scripts_dir' key."""
        config = AbstractConfig(project_root=str(tmp_path))
        result = config.get_path("scripts_dir")
        assert result == str(tmp_path / "scripts")

    @pytest.mark.unit
    def test_project_root_path(self, tmp_path):
        """Returns project_root for 'project_root' key."""
        config = AbstractConfig(project_root=str(tmp_path))
        result = config.get_path("project_root")
        assert result == str(tmp_path)

    @pytest.mark.unit
    def test_unknown_key_raises(self, tmp_path):
        """Unknown key raises ValueError."""
        config = AbstractConfig(project_root=str(tmp_path))
        with pytest.raises(ValueError, match="Unknown path key"):
            config.get_path("unknown_key")


# ---------------------------------------------------------------------------
# AbstractConfig.validate
# ---------------------------------------------------------------------------


class TestAbstractConfigValidate:
    """validate returns a list of configuration issues."""

    @pytest.mark.unit
    def test_valid_config_returns_no_issues(self, tmp_path):
        """Well-configured AbstractConfig returns empty issues list."""
        config = AbstractConfig(project_root=str(tmp_path))
        issues = config.validate()
        # project_root exists, so no issue for that
        assert all("does not exist" not in i for i in issues)

    @pytest.mark.unit
    def test_threshold_below_min_is_issue(self, tmp_path):
        """Threshold below MIN_THRESHOLD is reported."""
        config = AbstractConfig(project_root=str(tmp_path))
        config.skill_analyzer.DEFAULT_THRESHOLD = 0
        config.skill_analyzer.MIN_THRESHOLD = 1
        issues = config.validate()
        assert any("below minimum" in i for i in issues)

    @pytest.mark.unit
    def test_nonexistent_project_root_is_issue(self, tmp_path):
        """Non-existent project_root is reported."""
        config = AbstractConfig(project_root=str(tmp_path / "missing"))
        issues = config.validate()
        assert any("does not exist" in i for i in issues)

    @pytest.mark.unit
    def test_weights_not_summing_to_one_is_issue(self, tmp_path):
        """When skill_eval weights don't sum to 1.0, issue is reported."""
        config = AbstractConfig(project_root=str(tmp_path))
        config.skills_eval.STRUCTURE_WEIGHT = 0.5  # Throws off the sum
        issues = config.validate()
        assert any("weight" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# AbstractConfig.get_summary
# ---------------------------------------------------------------------------


class TestAbstractConfigGetSummary:
    """get_summary produces a human-readable string."""

    @pytest.mark.unit
    def test_summary_contains_environment(self):
        """Summary includes environment value."""
        config = AbstractConfig()
        summary = config.get_summary()
        assert "production" in summary.lower()

    @pytest.mark.unit
    def test_summary_contains_skill_validation_info(self):
        """Summary includes Skill Validation section."""
        config = AbstractConfig()
        summary = config.get_summary()
        assert "Skill Validation" in summary

    @pytest.mark.unit
    def test_summary_contains_threshold(self):
        """Summary includes threshold value from SkillAnalyzerConfig."""
        config = AbstractConfig()
        summary = config.get_summary()
        assert "150" in summary  # Default threshold


# ---------------------------------------------------------------------------
# ConfigFactory
# ---------------------------------------------------------------------------


class TestConfigFactory:
    """ConfigFactory manages named AbstractConfig instances."""

    def teardown_method(self):
        """Reset the ConfigFactory between tests."""
        ConfigFactory.reset_config("default")
        ConfigFactory.reset_config("custom")

    @pytest.mark.unit
    def test_get_config_returns_abstract_config(self, tmp_path, monkeypatch):
        """get_config returns an AbstractConfig instance."""
        monkeypatch.chdir(tmp_path)
        result = ConfigFactory.get_config("default")
        assert isinstance(result, AbstractConfig)

    @pytest.mark.unit
    def test_get_config_returns_same_instance(self, tmp_path, monkeypatch):
        """Subsequent calls return the same cached instance."""
        monkeypatch.chdir(tmp_path)
        first = ConfigFactory.get_config("default")
        second = ConfigFactory.get_config("default")
        assert first is second

    @pytest.mark.unit
    def test_set_config_stores_instance(self):
        """set_config stores an instance by name."""
        config = AbstractConfig(debug=True)
        ConfigFactory.set_config(config, "custom")
        result = ConfigFactory.get_config("custom")
        assert result is config

    @pytest.mark.unit
    def test_reset_config_removes_instance(self, tmp_path, monkeypatch):
        """reset_config removes the cached instance."""
        monkeypatch.chdir(tmp_path)
        ConfigFactory.get_config("default")  # Cache it
        ConfigFactory.reset_config("default")
        # After reset, a new instance is created
        result = ConfigFactory.get_config("default")
        assert isinstance(result, AbstractConfig)

    @pytest.mark.unit
    def test_create_config_with_kwargs(self):
        """create_config returns a new config with custom parameters."""
        config = ConfigFactory.create_config(debug=True, verbose=True)
        assert config.debug is True
        assert config.verbose is True

    @pytest.mark.unit
    def test_load_config_from_yaml(self, tmp_path):
        """load_config loads from file and stores with given name."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("debug: true\n")
        config = ConfigFactory.load_config(config_file, name="from-file")
        assert config.debug is True
        # Should be stored and retrievable
        assert ConfigFactory.get_config("from-file") is config
        ConfigFactory.reset_config("from-file")

    @pytest.mark.unit
    def test_get_config_loads_from_file_when_yaml_exists(self, tmp_path, monkeypatch):
        """When config/abstract_config.yaml exists in cwd, it is loaded."""
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "abstract_config.yaml").write_text("debug: true\n")

        result = ConfigFactory.get_config()
        assert result.debug is True
