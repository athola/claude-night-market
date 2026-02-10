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

from validate_plugin import PluginValidator


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
