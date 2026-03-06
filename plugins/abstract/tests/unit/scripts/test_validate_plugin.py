"""Tests for validate_plugin.py - hooks validation and deprecated shared dir detection.

Feature: Plugin Validator Enhancements
  As a plugin developer
  I want the validator to catch hooks path issues and deprecated patterns
  So that plugin structure stays current with ecosystem conventions
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))

from validate_plugin import PluginValidator, main


def _make_plugin(tmp_path: Path, config: dict) -> Path:
    """Create a minimal plugin directory structure."""
    plugin_dir = tmp_path / "myplugin"
    plugin_dir.mkdir()
    claude_dir = plugin_dir / ".claude-plugin"
    claude_dir.mkdir()
    json_file = claude_dir / "plugin.json"
    json_file.write_text(json.dumps(config))
    return plugin_dir


@pytest.fixture
def plugin_dir(tmp_path: Path) -> Path:
    """Given a minimal valid plugin directory structure."""
    plugin = tmp_path / "test-plugin"
    claude_dir = plugin / ".claude-plugin"
    claude_dir.mkdir(parents=True)
    config = {
        "name": "test-plugin",
        "description": "A test plugin",
        "version": "1.0.0",
        "skills": [],
    }
    (claude_dir / "plugin.json").write_text(json.dumps(config))
    return plugin


def _make_validator(
    plugin_dir: Path, config_override: dict | None = None
) -> PluginValidator:
    """Create a PluginValidator with optional config override written to plugin.json."""
    if config_override is not None:
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(config_override)
        )
    v = PluginValidator(plugin_dir)
    v._validate_plugin_json_exists()
    return v


class TestHooksPathValidation:
    """Feature: Validate hooks field in plugin.json.

    As a plugin validator
    I want to verify hooks paths point to valid JSON files
    So that hook registration does not silently fail
    """

    @pytest.mark.unit
    def test_valid_hooks_path_produces_info(self, plugin_dir: Path) -> None:
        """Scenario: hooks path points to a valid JSON file.

        Given a plugin.json with hooks: "./hooks/hooks.json"
        And a valid hooks.json file exists at that path
        When validation runs
        Then an info message confirms the hooks path is valid
        """
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))

        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "hooks": "./hooks/hooks.json",
                "skills": [],
            },
        )
        v._validate_paths()

        info_msgs = " ".join(v.issues["info"])
        assert "hooks path" in info_msgs
        assert "valid JSON" in info_msgs
        assert len(v.issues["critical"]) == 0

    @pytest.mark.unit
    def test_missing_hooks_path_is_critical(self, plugin_dir: Path) -> None:
        """Scenario: hooks path references a file that does not exist.

        Given a plugin.json with hooks: "./hooks/hooks.json"
        And no hooks.json file exists
        When validation runs
        Then a critical issue is reported
        """
        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "hooks": "./hooks/hooks.json",
                "skills": [],
            },
        )
        v._validate_paths()

        assert any("hooks path not found" in msg for msg in v.issues["critical"])

    @pytest.mark.unit
    def test_invalid_json_hooks_file_is_critical(self, plugin_dir: Path) -> None:
        """Scenario: hooks file exists but contains invalid JSON.

        Given a plugin.json with hooks: "./hooks/hooks.json"
        And hooks.json contains malformed JSON
        When validation runs
        Then a critical issue about invalid JSON is reported
        """
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text("{not valid json!!!")

        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "hooks": "./hooks/hooks.json",
                "skills": [],
            },
        )
        v._validate_paths()

        assert any("not valid JSON" in msg for msg in v.issues["critical"])

    @pytest.mark.unit
    def test_hooks_json_with_non_container_type_warns(self, plugin_dir: Path) -> None:
        """Scenario: hooks.json contains a scalar instead of object/array.

        Given a plugin.json with hooks pointing to a file
        And that file contains a JSON string (not object/array)
        When validation runs
        Then a warning is issued
        """
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text(json.dumps("just a string"))

        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "hooks": "./hooks/hooks.json",
                "skills": [],
            },
        )
        v._validate_paths()

        assert any("JSON object or array" in msg for msg in v.issues["warnings"])

    @pytest.mark.unit
    def test_hooks_path_without_leading_dot_slash(self, plugin_dir: Path) -> None:
        """Scenario: hooks path uses bare relative path (no ./ prefix).

        Given a plugin.json with hooks: "hooks/hooks.json"
        And the file exists
        When validation runs
        Then it still resolves correctly (no critical error)
        """
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text(json.dumps([]))

        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "hooks": "hooks/hooks.json",
                "skills": [],
            },
        )
        v._validate_paths()

        assert not any("hooks path not found" in msg for msg in v.issues["critical"])


class TestDeprecatedSharedDirDetection:
    """Feature: Detect deprecated skills/shared/ directory pattern.

    As a plugin maintainer
    I want the validator to flag skills/shared/ directories
    So that I migrate modules into skill-specific modules/ dirs
    """

    @pytest.mark.unit
    def test_shared_dir_with_modules_produces_warning(self, plugin_dir: Path) -> None:
        """Scenario: skills/shared/ exists with markdown modules.

        Given a plugin with skills/shared/modules/some-module.md
        When directory structure validation runs
        Then a deprecation warning is issued mentioning the module count
        """
        shared_dir = plugin_dir / "skills" / "shared" / "modules"
        shared_dir.mkdir(parents=True)
        (shared_dir / "common-patterns.md").write_text("# Shared patterns")
        (shared_dir / "output-templates.md").write_text("# Templates")

        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        warnings = " ".join(v.issues["warnings"])
        assert "Deprecated pattern" in warnings
        assert "skills/shared/" in warnings
        assert "2 module(s)" in warnings

    @pytest.mark.unit
    def test_shared_dir_empty_no_warning(self, plugin_dir: Path) -> None:
        """Scenario: skills/shared/ exists but has no .md files.

        Given a plugin with an empty skills/shared/ directory
        When directory structure validation runs
        Then no deprecation warning is issued
        """
        shared_dir = plugin_dir / "skills" / "shared"
        shared_dir.mkdir(parents=True)

        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        assert not any("Deprecated pattern" in msg for msg in v.issues["warnings"])

    @pytest.mark.unit
    def test_no_shared_dir_no_warning(self, plugin_dir: Path) -> None:
        """Scenario: No skills/shared/ directory exists.

        Given a plugin without skills/shared/
        When directory structure validation runs
        Then no deprecation warning is issued
        """
        (plugin_dir / "skills").mkdir(exist_ok=True)

        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        assert not any("Deprecated pattern" in msg for msg in v.issues["warnings"])


class TestKeywordsRecommendation:
    """Feature: Keywords field is now recommended.

    As a plugin developer
    I want to know if I'm missing the keywords field
    So that my plugin is discoverable
    """

    @pytest.mark.unit
    def test_missing_keywords_produces_recommendation(self, plugin_dir: Path) -> None:
        """Scenario: plugin.json has no keywords field.

        Given a plugin.json without a keywords field
        When recommended fields validation runs
        Then a recommendation about keywords is issued
        """
        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "Test",
                "author": "Test Author",
                "license": "MIT",
                "skills": [],
            },
        )
        v._validate_recommended_fields()

        assert any("keywords" in msg for msg in v.issues["recommendations"])

    @pytest.mark.unit
    def test_present_keywords_no_recommendation(self, plugin_dir: Path) -> None:
        """Scenario: plugin.json includes keywords.

        Given a plugin.json with a keywords field
        When recommended fields validation runs
        Then no recommendation about keywords is issued
        """
        v = _make_validator(
            plugin_dir,
            {
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "Test",
                "author": "Test Author",
                "license": "MIT",
                "keywords": ["git", "workflow"],
                "skills": [],
            },
        )
        v._validate_recommended_fields()

        assert not any("keywords" in msg for msg in v.issues["recommendations"])


class TestDeprecatedSharedDirectory:
    """Feature: Detect deprecated skills/shared/ directory pattern.

    As a plugin validator
    I want to warn when skills/shared/ directories exist
    So that plugin authors migrate to skill-specific modules
    """

    @pytest.mark.unit
    def test_shared_dir_with_modules_triggers_warning(self, plugin_dir: Path) -> None:
        """Scenario: skills/shared/ directory with markdown files.

        Given a plugin with skills/shared/ containing .md files
        When structure validation runs
        Then a deprecation warning is issued
        """
        shared_dir = plugin_dir / "skills" / "shared"
        shared_dir.mkdir(parents=True)
        (shared_dir / "SKILL.md").write_text("# Shared")
        modules_dir = shared_dir / "modules"
        modules_dir.mkdir()
        (modules_dir / "patterns.md").write_text("# Patterns")

        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        assert any("Deprecated pattern" in msg for msg in v.issues["warnings"])
        assert any("skills/shared/" in msg for msg in v.issues["warnings"])

    @pytest.mark.unit
    def test_no_shared_dir_no_warning(self, plugin_dir: Path) -> None:
        """Scenario: plugin without skills/shared/ directory.

        Given a plugin without a skills/shared/ directory
        When structure validation runs
        Then no deprecation warning is issued
        """
        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        assert not any("Deprecated pattern" in msg for msg in v.issues["warnings"])

    @pytest.mark.unit
    def test_empty_shared_dir_no_warning(self, plugin_dir: Path) -> None:
        """Scenario: skills/shared/ exists but has no markdown files.

        Given a plugin with an empty skills/shared/ directory
        When structure validation runs
        Then no deprecation warning is issued
        """
        shared_dir = plugin_dir / "skills" / "shared"
        shared_dir.mkdir(parents=True)

        v = _make_validator(plugin_dir)
        v._validate_directory_structure()

        assert not any("Deprecated pattern" in msg for msg in v.issues["warnings"])


# ---------------------------------------------------------------------------
# Tests merged from coverage sprint (validate_plugin full coverage)
# ---------------------------------------------------------------------------


class TestValidatePluginJsonExists:
    """Plugin.json must exist in .claude-plugin/."""

    @pytest.mark.unit
    def test_missing_json_adds_critical(self, tmp_path: Path) -> None:
        """No plugin.json adds a critical issue."""
        pd = tmp_path / "myplugin"
        pd.mkdir()
        (pd / ".claude-plugin").mkdir()
        v = PluginValidator(pd)
        v.validate()
        assert any(
            ".claude-plugin/plugin.json not found" in i for i in v.issues["critical"]
        )

    @pytest.mark.unit
    def test_json_at_wrong_location_adds_critical(self, tmp_path: Path) -> None:
        """plugin.json at root instead of .claude-plugin/ adds critical."""
        pd = tmp_path / "myplugin"
        pd.mkdir()
        (pd / ".claude-plugin").mkdir()
        (pd / "plugin.json").write_text(json.dumps({"name": "myplugin"}))
        v = PluginValidator(pd)
        v.validate()
        assert any("root but should be" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_invalid_json_adds_critical(self, tmp_path: Path) -> None:
        """Invalid JSON content adds a critical issue."""
        pd = tmp_path / "myplugin"
        pd.mkdir()
        cd = pd / ".claude-plugin"
        cd.mkdir()
        (cd / "plugin.json").write_text("{invalid json}")
        v = PluginValidator(pd)
        v.validate()
        assert any("not valid JSON" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_non_dict_json_adds_critical(self, tmp_path: Path) -> None:
        """plugin.json containing an array adds a critical issue."""
        pd = tmp_path / "myplugin"
        pd.mkdir()
        cd = pd / ".claude-plugin"
        cd.mkdir()
        (cd / "plugin.json").write_text("[1, 2, 3]")
        v = PluginValidator(pd)
        v.validate()
        assert any("JSON object" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_valid_json_sets_config(self, tmp_path: Path) -> None:
        """Valid plugin.json sets the config on the validator."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        assert v.config is not None
        assert v.config["name"] == "my-plugin"


class TestValidatePluginName:
    """Plugin name must follow kebab-case convention."""

    @pytest.mark.unit
    def test_valid_kebab_case_name(self, tmp_path: Path) -> None:
        """kebab-case name produces no critical issues."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_plugin_name()
        assert not any("Invalid plugin name" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_missing_name_adds_critical(self, tmp_path: Path) -> None:
        """Missing name field adds a critical issue."""
        pd = _make_plugin(tmp_path, {"version": "1.0.0"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_plugin_name()
        assert any("Missing required field: name" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_non_string_name_adds_critical(self, tmp_path: Path) -> None:
        """Non-string name adds a critical issue."""
        pd = _make_plugin(tmp_path, {"name": 123})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_plugin_name()
        assert any("must be a string" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_invalid_name_format_adds_critical(self, tmp_path: Path) -> None:
        """CamelCase name adds a critical issue."""
        pd = _make_plugin(tmp_path, {"name": "MyPlugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_plugin_name()
        assert any("Invalid plugin name" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_name_with_underscores_fails(self, tmp_path: Path) -> None:
        """Name with underscores fails kebab-case check."""
        pd = _make_plugin(tmp_path, {"name": "my_plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_plugin_name()
        assert any("Invalid plugin name" in i for i in v.issues["critical"])


class TestValidateRecommendedFields:
    """Recommended metadata fields generate recommendations."""

    @pytest.mark.unit
    def test_missing_version_generates_recommendation(self, tmp_path: Path) -> None:
        """Missing version field generates a recommendation."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_recommended_fields()
        assert any("version" in i for i in v.issues["recommendations"])

    @pytest.mark.unit
    def test_valid_semver_version_no_warning(self, tmp_path: Path) -> None:
        """Correct semantic version produces no warning."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "version": "1.2.3"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_recommended_fields()
        assert not v.issues["warnings"]

    @pytest.mark.unit
    def test_non_string_version_adds_warning(self, tmp_path: Path) -> None:
        """Non-string version adds a warning."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "version": 123})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_recommended_fields()
        assert any("string" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_invalid_version_format_adds_warning(self, tmp_path: Path) -> None:
        """Version without dots adds a warning."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "version": "v1"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_recommended_fields()
        assert any("semantic versioning" in i for i in v.issues["warnings"])


class TestValidateDependencies:
    """Dependencies format validation."""

    @pytest.mark.unit
    def test_no_dependencies_no_issues(self, tmp_path: Path) -> None:
        """Missing dependencies field is allowed."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_dependencies()
        assert not v.issues["warnings"]

    @pytest.mark.unit
    def test_list_dependencies_adds_recommendation(self, tmp_path: Path) -> None:
        """Array-style dependencies add a recommendation."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "dependencies": ["abstract"]})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_dependencies()
        assert any("object" in i for i in v.issues["recommendations"])

    @pytest.mark.unit
    def test_dict_dependencies_valid_semver(self, tmp_path: Path) -> None:
        """Object dependencies with valid semver produce no warnings."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "dependencies": {"abstract": ">=2.0.0"}}
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_dependencies()
        assert not v.issues["warnings"]

    @pytest.mark.unit
    def test_dict_dependencies_non_string_version(self, tmp_path: Path) -> None:
        """Non-string version in dependencies adds a warning."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "dependencies": {"abstract": 2}}
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_dependencies()
        assert any("should be a string" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_dict_dependencies_invalid_version_format(self, tmp_path: Path) -> None:
        """Invalid semver format in dependencies adds a warning."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "dependencies": {"abstract": "latest"}}
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_dependencies()
        assert any("semantic versioning" in i for i in v.issues["warnings"])


class TestValidateDirectoryStructureExtended:
    """Directory structure extended tests."""

    @pytest.mark.unit
    def test_missing_skills_dir_adds_warning(self, tmp_path: Path) -> None:
        """skills referenced but directory missing adds warning."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_directory_structure()
        assert any("skills/" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_wrong_location_adds_critical(self, tmp_path: Path) -> None:
        """skills dir inside .claude-plugin adds critical issue."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        wrong = pd / ".claude-plugin" / "skills"
        wrong.mkdir()
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_directory_structure()
        assert any("should be at plugin root" in i for i in v.issues["critical"])


class TestValidateSkills:
    """Skill files are validated for frontmatter."""

    @pytest.mark.unit
    def test_skill_with_valid_frontmatter(self, tmp_path: Path) -> None:
        """Skill with name and description produces no warnings."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        sd = pd / "skills" / "my-skill"
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: A skill\n---\n\n# My Skill\n"
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_skills()
        assert not any("missing 'name'" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_skill_without_frontmatter_adds_warning(self, tmp_path: Path) -> None:
        """Skill without --- frontmatter adds warning."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        sd = pd / "skills" / "my-skill"
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text("# Just a heading\nNo frontmatter.\n")
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_skills()
        assert any(
            "should start with YAML frontmatter" in i for i in v.issues["warnings"]
        )

    @pytest.mark.unit
    def test_skill_missing_name_adds_warning(self, tmp_path: Path) -> None:
        """Skill without name in frontmatter adds a warning."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        sd = pd / "skills" / "my-skill"
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text("---\ndescription: A skill\n---\n\n# Content\n")
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_skills()
        assert any("missing 'name'" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_skill_missing_description_adds_recommendation(
        self, tmp_path: Path
    ) -> None:
        """Skill without description adds recommendation."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        sd = pd / "skills" / "my-skill"
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text("---\nname: my-skill\n---\n\n# Content\n")
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_skills()
        assert any("missing 'description'" in i for i in v.issues["recommendations"])

    @pytest.mark.unit
    def test_skills_not_a_list_no_crash(self, tmp_path: Path) -> None:
        """skills field that is not a list is handled gracefully."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "skills": "not-a-list"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_skills()


class TestValidateClaudeConfig:
    """Claude-specific config validation."""

    @pytest.mark.unit
    def test_missing_claude_key_adds_recommendation(self, tmp_path: Path) -> None:
        """No claude config key adds a recommendation."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_claude_config()
        assert any("claude" in i for i in v.issues["recommendations"])

    @pytest.mark.unit
    def test_non_dict_claude_adds_warning(self, tmp_path: Path) -> None:
        """claude config that is not a dict adds a warning."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "claude": "string"})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_claude_config()
        assert any("JSON object" in i for i in v.issues["warnings"])

    @pytest.mark.unit
    def test_valid_claude_config_no_critical(self, tmp_path: Path) -> None:
        """Valid dict claude config adds no critical issues."""
        pd = _make_plugin(
            tmp_path,
            {"name": "my-plugin", "claude": {"skill_prefix": "my"}},
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_claude_config()
        assert not v.issues["critical"]


class TestValidatePathsExtended:
    """Path references validation."""

    @pytest.mark.unit
    def test_valid_skills_path_no_critical(self, tmp_path: Path) -> None:
        """Existing skills path produces no critical issues."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/my-skill"]}
        )
        sd = pd / "skills" / "my-skill"
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text("---\nname: my-skill\n---\n\n# Skill\n")
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_paths()
        assert not any("path not found" in i for i in v.issues["critical"])

    @pytest.mark.unit
    def test_missing_skills_path_adds_critical(self, tmp_path: Path) -> None:
        """Missing skills path adds a critical issue."""
        pd = _make_plugin(
            tmp_path, {"name": "my-plugin", "skills": ["./skills/missing"]}
        )
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        v._validate_paths()
        assert any("path not found" in i for i in v.issues["critical"])


class TestValidateHooksPathExtended:
    """Hooks path validation."""

    @pytest.mark.unit
    def test_valid_hooks_json(self, tmp_path: Path) -> None:
        """Valid hooks.json produces no critical issues."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "hooks": "./hooks.json"})
        (pd / "hooks.json").write_text(json.dumps({"events": []}))
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        config = v._require_config()
        v._validate_hooks_path(config)
        assert not v.issues["critical"]

    @pytest.mark.unit
    def test_non_string_hooks_value_skipped(self, tmp_path: Path) -> None:
        """hooks value that is not a string is skipped gracefully."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "hooks": {"key": "val"}})
        v = PluginValidator(pd)
        v._validate_plugin_json_exists()
        config = v._require_config()
        v._validate_hooks_path(config)
        assert not any("hooks" in i for i in v.issues["critical"])


class TestValidateIntegration:
    """Full validation returns correct exit codes."""

    @pytest.mark.unit
    def test_valid_plugin_returns_zero(self, tmp_path: Path) -> None:
        """Valid plugin structure returns exit code 0."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin", "version": "1.0.0"})
        v = PluginValidator(pd)
        assert v.validate() == 0

    @pytest.mark.unit
    def test_invalid_plugin_returns_one(self, tmp_path: Path) -> None:
        """Plugin with critical issues returns exit code 1."""
        pd = tmp_path / "bad-plugin"
        pd.mkdir()
        (pd / ".claude-plugin").mkdir()
        v = PluginValidator(pd)
        assert v.validate() == 1


class TestMain:
    """main() CLI entry point."""

    @pytest.mark.unit
    def test_main_no_args_returns_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No arguments to main returns 1."""
        monkeypatch.setattr(sys, "argv", ["validate_plugin.py"])
        assert main() == 1

    @pytest.mark.unit
    def test_main_nonexistent_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Non-existent path argument returns 1."""
        monkeypatch.setattr(
            sys, "argv", ["validate_plugin.py", str(tmp_path / "nonexistent")]
        )
        assert main() == 1

    @pytest.mark.unit
    def test_main_file_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """File path (not directory) argument returns 1."""
        f = tmp_path / "file.txt"
        f.write_text("data")
        monkeypatch.setattr(sys, "argv", ["validate_plugin.py", str(f)])
        assert main() == 1

    @pytest.mark.unit
    def test_main_valid_plugin(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Valid plugin directory runs successfully."""
        pd = _make_plugin(tmp_path, {"name": "my-plugin"})
        monkeypatch.setattr(sys, "argv", ["validate_plugin.py", str(pd)])
        assert main() == 0
