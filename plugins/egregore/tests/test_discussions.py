"""Tests for the egregore GitHub Discussions publishing module."""

from __future__ import annotations

from discussions import (
    DiscussionsConfig,
)


class TestDiscussionsConfig:
    """Feature: Discussions configuration management.

    As an egregore operator
    I want to configure which discussion types are published
    So that I control what appears in GitHub Discussions
    """

    def test_defaults_enable_all_types(self) -> None:
        """Scenario: Default config enables all publishing.

        Given a fresh DiscussionsConfig
        When I check the defaults
        Then all content types are enabled
        """
        cfg = DiscussionsConfig()
        assert cfg.enabled is True
        assert cfg.publish_discoveries is True
        assert cfg.publish_insights is True
        assert cfg.publish_contention is True
        assert cfg.publish_retrospectives is True
        assert cfg.max_per_work_item == 10

    def test_to_dict_returns_all_fields(self) -> None:
        """Scenario: Serialization includes every field.

        Given a DiscussionsConfig with custom values
        When I call to_dict
        Then the dict contains all fields with correct values
        """
        cfg = DiscussionsConfig(
            enabled=False,
            publish_discoveries=False,
            publish_insights=True,
            publish_contention=False,
            publish_retrospectives=True,
            max_per_work_item=5,
        )
        data = cfg.to_dict()
        assert data["enabled"] is False
        assert data["publish_discoveries"] is False
        assert data["publish_insights"] is True
        assert data["publish_contention"] is False
        assert data["publish_retrospectives"] is True
        assert data["max_per_work_item"] == 5

    def test_from_dict_restores_values(self) -> None:
        """Scenario: Deserialization restores original values.

        Given a dict with config values
        When I call from_dict
        Then the resulting config matches the dict
        """
        data = {
            "enabled": False,
            "publish_discoveries": True,
            "publish_insights": False,
            "publish_contention": True,
            "publish_retrospectives": False,
            "max_per_work_item": 3,
        }
        cfg = DiscussionsConfig.from_dict(data)
        assert cfg.enabled is False
        assert cfg.publish_insights is False
        assert cfg.max_per_work_item == 3

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Scenario: Unknown keys in dict are silently ignored.

        Given a dict with extra unknown keys
        When I call from_dict
        Then no error is raised and known keys are loaded
        """
        data = {
            "enabled": True,
            "unknown_field": "should be ignored",
            "another_unknown": 42,
        }
        cfg = DiscussionsConfig.from_dict(data)
        assert cfg.enabled is True
        assert not hasattr(cfg, "unknown_field")

    def test_roundtrip_through_dict(self) -> None:
        """Scenario: to_dict then from_dict preserves all values.

        Given a DiscussionsConfig with non-default values
        When I serialize and deserialize
        Then the result matches the original
        """
        original = DiscussionsConfig(
            enabled=False,
            publish_discoveries=False,
            publish_insights=True,
            publish_contention=False,
            publish_retrospectives=True,
            max_per_work_item=7,
        )
        restored = DiscussionsConfig.from_dict(original.to_dict())
        assert restored.enabled == original.enabled
        assert restored.publish_discoveries == original.publish_discoveries
        assert restored.publish_insights == original.publish_insights
        assert restored.publish_contention == original.publish_contention
        assert restored.publish_retrospectives == original.publish_retrospectives
        assert restored.max_per_work_item == original.max_per_work_item
