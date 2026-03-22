"""Tests for shared skill name parsing utilities."""

from __future__ import annotations

import pytest
from hooks.shared.skill_utils import parse_skill_name


class TestParseSkillName:
    """
    Feature: Skill name parsing with sanitization

    As a hook developer
    I want a single parse_skill_name utility
    So that all hooks parse and sanitize skill names consistently
    """

    @pytest.mark.unit
    def test_parses_plugin_colon_skill_format(self):
        """
        Scenario: Standard plugin:skill reference
        Given a tool input with skill "abstract:auditor"
        When parse_skill_name is called
        Then it returns ("abstract", "auditor")
        """
        plugin, skill = parse_skill_name({"skill": "abstract:auditor"})
        assert plugin == "abstract"
        assert skill == "auditor"

    @pytest.mark.unit
    def test_parses_skill_only_format(self):
        """
        Scenario: Skill name without plugin prefix
        Given a tool input with skill "auditor"
        When parse_skill_name is called
        Then it returns ("unknown", "auditor")
        """
        plugin, skill = parse_skill_name({"skill": "auditor"})
        assert plugin == "unknown"
        assert skill == "auditor"

    @pytest.mark.unit
    def test_returns_unknown_for_missing_skill_key(self):
        """
        Scenario: Tool input missing skill key
        Given an empty tool input dict
        When parse_skill_name is called
        Then it returns ("unknown", "unknown")
        """
        plugin, skill = parse_skill_name({})
        assert plugin == "unknown"
        assert skill == "unknown"

    @pytest.mark.unit
    def test_sanitizes_path_traversal_in_plugin(self):
        """
        Scenario: Path traversal attempt in plugin name
        Given a tool input with skill "../etc:passwd"
        When parse_skill_name is called
        Then the plugin is sanitized to "unknown"
        """
        plugin, skill = parse_skill_name({"skill": "../etc:passwd"})
        assert plugin == "unknown"
        assert skill == "passwd"

    @pytest.mark.unit
    def test_sanitizes_path_traversal_in_skill(self):
        """
        Scenario: Path traversal attempt in skill name
        Given a tool input with skill "plugin:../../etc/passwd"
        When parse_skill_name is called
        Then the skill is sanitized to "unknown"
        """
        plugin, skill = parse_skill_name({"skill": "plugin:../../etc/passwd"})
        assert plugin == "plugin"
        assert skill == "unknown"

    @pytest.mark.unit
    def test_strips_whitespace_from_components(self):
        """
        Scenario: Whitespace around plugin and skill names
        Given a tool input with skill " abstract : auditor "
        When parse_skill_name is called
        Then both components are stripped
        """
        plugin, skill = parse_skill_name({"skill": " abstract : auditor "})
        assert plugin == "abstract"
        assert skill == "auditor"

    @pytest.mark.unit
    def test_allows_hyphens_and_underscores(self):
        """
        Scenario: Skill names with hyphens and underscores
        Given a tool input with skill "my-plugin:skill_name"
        When parse_skill_name is called
        Then both components are accepted as-is
        """
        plugin, skill = parse_skill_name({"skill": "my-plugin:skill_name"})
        assert plugin == "my-plugin"
        assert skill == "skill_name"

    @pytest.mark.unit
    def test_rejects_empty_string_plugin(self):
        """
        Scenario: Empty plugin component
        Given a tool input with skill ":auditor"
        When parse_skill_name is called
        Then the plugin is sanitized to "unknown"
        """
        plugin, skill = parse_skill_name({"skill": ":auditor"})
        assert plugin == "unknown"
        assert skill == "auditor"
