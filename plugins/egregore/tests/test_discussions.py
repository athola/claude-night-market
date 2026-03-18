"""Tests for the egregore GitHub Discussions publishing module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from discussions import (
    DiscussionCategory,
    DiscussionEntry,
    DiscussionsConfig,
    PublishTracker,
    build_discussion_body,
    load_tracker,
    publish_discussion,
    save_tracker,
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


class TestDiscussionCategory:
    """Feature: Content type to Discussion category mapping.

    As an egregore operator
    I want discoveries routed to Research and insights to War Room
    So that discussions land in the right GitHub category
    """

    @pytest.mark.parametrize(
        ("content_type", "expected"),
        [
            ("discovery", "Research"),
            ("improvement", "Research"),
            ("tangential_idea", "Research"),
            ("insight", "War Room"),
            ("contention", "War Room"),
            ("retrospective", "War Room"),
        ],
        ids=[
            "discovery-to-research",
            "improvement-to-research",
            "tangential-idea-to-research",
            "insight-to-war-room",
            "contention-to-war-room",
            "retrospective-to-war-room",
        ],
    )
    def test_known_types_map_to_correct_category(
        self, content_type: str, expected: str
    ) -> None:
        """Scenario: Known content types map to expected categories.

        Given a known content type
        When I look up its category
        Then it returns the correct GitHub Discussion category
        """
        assert DiscussionCategory.for_content_type(content_type) == expected

    def test_unknown_type_defaults_to_research(self) -> None:
        """Scenario: Unknown content types fall back to Research.

        Given an unrecognized content type
        When I look up its category
        Then it returns Research as default
        """
        assert DiscussionCategory.for_content_type("unknown_type") == "Research"


class TestDiscussionEntry:
    """Feature: Discussion entry data model.

    As an egregore pipeline step
    I want to create discussion entries with metadata
    So that discoveries carry full context when published
    """

    def test_category_property_delegates_to_category_class(self) -> None:
        """Scenario: Entry category comes from DiscussionCategory mapping.

        Given a DiscussionEntry with content_type 'insight'
        When I access its category property
        Then it returns 'War Room'
        """
        entry = DiscussionEntry(
            title="Test insight",
            body="Some insight body",
            content_type="insight",
        )
        assert entry.category == "War Room"

    def test_default_tags_are_empty(self) -> None:
        """Scenario: Tags default to empty list.

        Given a DiscussionEntry created without tags
        When I check tags
        Then it is an empty list
        """
        entry = DiscussionEntry(
            title="Test",
            body="Body",
            content_type="discovery",
        )
        assert entry.tags == []

    def test_created_at_has_default(self) -> None:
        """Scenario: Timestamp is auto-populated.

        Given a DiscussionEntry created without explicit timestamp
        When I check created_at
        Then it is a non-empty ISO format string
        """
        entry = DiscussionEntry(
            title="Test",
            body="Body",
            content_type="discovery",
        )
        assert len(entry.created_at) > 0
        assert "T" in entry.created_at  # ISO format contains 'T'


class TestBuildDiscussionBody:
    """Feature: Discussion body formatting.

    As a GitHub Discussions reader
    I want well-formatted discussion bodies
    So that discoveries are easy to read and search
    """

    def test_includes_content_type_heading(self) -> None:
        """Scenario: Body starts with a heading for the content type.

        Given a discovery entry
        When I build the body
        Then it contains a '## Discovery' heading
        """
        entry = DiscussionEntry(
            title="Found a pattern",
            body="Interesting pattern in the data.",
            content_type="discovery",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "## Discovery" in body

    def test_includes_work_item_when_set(self) -> None:
        """Scenario: Body includes work item reference when present.

        Given an entry with a work_item_id
        When I build the body
        Then the body contains the work item reference
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="insight",
            work_item_id="WI-42",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "**Work Item:** WI-42" in body

    def test_includes_pipeline_step_when_set(self) -> None:
        """Scenario: Body includes pipeline step when present.

        Given an entry with a pipeline_step
        When I build the body
        Then the body contains the pipeline step
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="insight",
            pipeline_step="brainstorm",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "**Pipeline Step:** brainstorm" in body

    def test_includes_timestamp(self) -> None:
        """Scenario: Body always includes the timestamp.

        Given an entry with a specific timestamp
        When I build the body
        Then the timestamp appears in the body
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="discovery",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "**Timestamp:** 2026-01-15T10:00:00+00:00" in body

    def test_includes_entry_body_text(self) -> None:
        """Scenario: Body includes the actual content.

        Given an entry with body text
        When I build the body
        Then the text appears in the formatted body
        """
        entry = DiscussionEntry(
            title="Test",
            body="The flux capacitor needs 1.21 gigawatts.",
            content_type="discovery",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "The flux capacitor needs 1.21 gigawatts." in body

    def test_includes_tags_when_present(self) -> None:
        """Scenario: Tags appear at the bottom when set.

        Given an entry with tags
        When I build the body
        Then the tags appear after a separator
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="discovery",
            tags=["architecture", "performance"],
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "---" in body
        assert "Tags: architecture, performance" in body

    def test_omits_tags_section_when_empty(self) -> None:
        """Scenario: No tags section when tags list is empty.

        Given an entry without tags
        When I build the body
        Then no separator or Tags line appears
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="discovery",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "Tags:" not in body

    def test_omits_work_item_when_empty(self) -> None:
        """Scenario: No work item line when id is empty.

        Given an entry without a work_item_id
        When I build the body
        Then no Work Item line appears
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="discovery",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "**Work Item:**" not in body

    def test_tangential_idea_heading_format(self) -> None:
        """Scenario: Underscored content types format as title case.

        Given a tangential_idea entry
        When I build the body
        Then heading reads 'Tangential Idea'
        """
        entry = DiscussionEntry(
            title="Test",
            body="Content",
            content_type="tangential_idea",
            created_at="2026-01-15T10:00:00+00:00",
        )
        body = build_discussion_body(entry)
        assert "## Tangential Idea" in body


class TestPublishTracker:
    """Feature: Per-work-item rate limiting.

    As an egregore operator
    I want to limit how many discussions a single work item produces
    So that noisy items do not flood GitHub Discussions
    """

    def test_fresh_tracker_allows_publishing(self) -> None:
        """Scenario: New tracker allows publishing for any item.

        Given an empty PublishTracker
        When I check if WI-1 can publish with max 5
        Then it returns True
        """
        tracker = PublishTracker()
        assert tracker.can_publish("WI-1", 5) is True

    def test_record_increments_count(self) -> None:
        """Scenario: Recording a publish increments the count.

        Given a tracker with no publishes for WI-1
        When I record a publish for WI-1
        Then the count for WI-1 is 1
        """
        tracker = PublishTracker()
        tracker.record_publish("WI-1")
        assert tracker.counts["WI-1"] == 1

    def test_blocks_at_max(self) -> None:
        """Scenario: Tracker blocks publishing when limit is reached.

        Given a tracker with 3 publishes for WI-1
        When I check if WI-1 can publish with max 3
        Then it returns False
        """
        tracker = PublishTracker(counts={"WI-1": 3})
        assert tracker.can_publish("WI-1", 3) is False

    def test_allows_just_under_max(self) -> None:
        """Scenario: Tracker allows publishing when count is below max.

        Given a tracker with 2 publishes for WI-1
        When I check if WI-1 can publish with max 3
        Then it returns True
        """
        tracker = PublishTracker(counts={"WI-1": 2})
        assert tracker.can_publish("WI-1", 3) is True

    def test_different_items_tracked_independently(self) -> None:
        """Scenario: Each work item has its own counter.

        Given WI-1 is at limit but WI-2 has zero publishes
        When I check if WI-2 can publish
        Then it returns True
        """
        tracker = PublishTracker(counts={"WI-1": 10})
        assert tracker.can_publish("WI-2", 10) is True

    def test_to_dict_serializes_counts(self) -> None:
        """Scenario: Serialization preserves counts.

        Given a tracker with multiple items
        When I call to_dict
        Then the dict has a counts key matching the data
        """
        tracker = PublishTracker(counts={"WI-1": 3, "WI-2": 7})
        data = tracker.to_dict()
        assert data == {"counts": {"WI-1": 3, "WI-2": 7}}

    def test_from_dict_restores_counts(self) -> None:
        """Scenario: Deserialization restores counts.

        Given a dict with counts
        When I call from_dict
        Then the tracker has the correct counts
        """
        tracker = PublishTracker.from_dict({"counts": {"WI-5": 2}})
        assert tracker.counts == {"WI-5": 2}

    def test_from_dict_handles_missing_counts(self) -> None:
        """Scenario: Empty dict produces empty tracker.

        Given an empty dict
        When I call from_dict
        Then the tracker has zero counts
        """
        tracker = PublishTracker.from_dict({})
        assert tracker.counts == {}


class TestPublishDiscussion:
    """Feature: Discussion publishing with guards.

    As an egregore orchestrator
    I want publish_discussion to check config and rate limits
    So that only appropriate discussions are published
    """

    def _make_entry(
        self,
        content_type: str = "discovery",
        work_item_id: str = "WI-1",
    ) -> DiscussionEntry:
        return DiscussionEntry(
            title="Test discussion",
            body="Test body content",
            content_type=content_type,
            work_item_id=work_item_id,
            created_at="2026-01-15T10:00:00+00:00",
        )

    def test_publishes_when_enabled(self) -> None:
        """Scenario: Publishing succeeds when config allows it.

        Given discussions are enabled and discovery type is on
        When I publish a discovery
        Then it returns True
        """
        config = DiscussionsConfig()
        tracker = PublishTracker()
        entry = self._make_entry()
        assert publish_discussion(entry, config, tracker) is True

    def test_returns_false_when_disabled(self) -> None:
        """Scenario: Publishing is skipped when globally disabled.

        Given discussions are disabled
        When I publish any entry
        Then it returns False
        """
        config = DiscussionsConfig(enabled=False)
        tracker = PublishTracker()
        entry = self._make_entry()
        assert publish_discussion(entry, config, tracker) is False

    def test_returns_false_for_disabled_content_type(self) -> None:
        """Scenario: Publishing is skipped when content type is disabled.

        Given discoveries are disabled
        When I publish a discovery
        Then it returns False
        """
        config = DiscussionsConfig(publish_discoveries=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="discovery")
        assert publish_discussion(entry, config, tracker) is False

    def test_returns_false_when_rate_limited(self) -> None:
        """Scenario: Publishing is blocked when rate limit is hit.

        Given WI-1 has hit its max of 2
        When I try to publish for WI-1
        Then it returns False
        """
        config = DiscussionsConfig(max_per_work_item=2)
        tracker = PublishTracker(counts={"WI-1": 2})
        entry = self._make_entry(work_item_id="WI-1")
        assert publish_discussion(entry, config, tracker) is False

    def test_tracks_publish_count(self) -> None:
        """Scenario: Successful publish increments tracker.

        Given a fresh tracker
        When I publish for WI-1
        Then the tracker count for WI-1 becomes 1
        """
        config = DiscussionsConfig()
        tracker = PublishTracker()
        entry = self._make_entry(work_item_id="WI-1")
        publish_discussion(entry, config, tracker)
        assert tracker.counts["WI-1"] == 1

    def test_does_not_track_when_disabled(self) -> None:
        """Scenario: Skipped publishes do not increment tracker.

        Given discussions are disabled
        When I try to publish for WI-1
        Then the tracker remains empty
        """
        config = DiscussionsConfig(enabled=False)
        tracker = PublishTracker()
        entry = self._make_entry(work_item_id="WI-1")
        publish_discussion(entry, config, tracker)
        assert tracker.counts == {}

    def test_improvement_uses_discoveries_toggle(self) -> None:
        """Scenario: 'improvement' type follows publish_discoveries flag.

        Given discoveries are disabled
        When I publish an improvement
        Then it returns False
        """
        config = DiscussionsConfig(publish_discoveries=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="improvement")
        assert publish_discussion(entry, config, tracker) is False

    def test_tangential_idea_uses_discoveries_toggle(self) -> None:
        """Scenario: 'tangential_idea' follows publish_discoveries flag.

        Given discoveries are disabled
        When I publish a tangential_idea
        Then it returns False
        """
        config = DiscussionsConfig(publish_discoveries=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="tangential_idea")
        assert publish_discussion(entry, config, tracker) is False

    def test_unknown_content_type_returns_false(self) -> None:
        """Scenario: Unknown content types are not published.

        Given an entry with an unknown content type
        When I try to publish it
        Then it returns False
        """
        config = DiscussionsConfig()
        tracker = PublishTracker()
        entry = self._make_entry(content_type="nonexistent")
        assert publish_discussion(entry, config, tracker) is False

    def test_publishes_without_work_item_id(self) -> None:
        """Scenario: Entries without work_item_id skip rate limiting.

        Given an entry with no work_item_id
        When I publish it
        Then it succeeds and tracker remains empty
        """
        config = DiscussionsConfig()
        tracker = PublishTracker()
        entry = self._make_entry(work_item_id="")
        assert publish_discussion(entry, config, tracker) is True
        assert tracker.counts == {}

    def test_insight_uses_insights_toggle(self) -> None:
        """Scenario: 'insight' type follows publish_insights flag.

        Given insights are disabled
        When I publish an insight
        Then it returns False
        """
        config = DiscussionsConfig(publish_insights=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="insight")
        assert publish_discussion(entry, config, tracker) is False

    def test_contention_uses_contention_toggle(self) -> None:
        """Scenario: 'contention' type follows publish_contention flag.

        Given contention is disabled
        When I publish a contention
        Then it returns False
        """
        config = DiscussionsConfig(publish_contention=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="contention")
        assert publish_discussion(entry, config, tracker) is False

    def test_retrospective_uses_retrospectives_toggle(self) -> None:
        """Scenario: 'retrospective' follows publish_retrospectives flag.

        Given retrospectives are disabled
        When I publish a retrospective
        Then it returns False
        """
        config = DiscussionsConfig(publish_retrospectives=False)
        tracker = PublishTracker()
        entry = self._make_entry(content_type="retrospective")
        assert publish_discussion(entry, config, tracker) is False


class TestTrackerPersistence:
    """Feature: Tracker save/load roundtrip.

    As an egregore operator
    I want tracker state persisted to disk
    So that rate limits survive across restarts
    """

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Scenario: save_tracker creates a JSON file.

        Given a tracker with some counts
        When I save it to a path
        Then the file exists
        """
        tracker = PublishTracker(counts={"WI-1": 3})
        path = tmp_path / "tracker.json"
        save_tracker(tracker, path)
        assert path.exists()

    def test_save_produces_valid_json(self, tmp_path: Path) -> None:
        """Scenario: Saved file contains valid JSON.

        Given a tracker
        When I save and read the file
        Then the content is valid JSON with counts
        """
        tracker = PublishTracker(counts={"WI-1": 3})
        path = tmp_path / "tracker.json"
        save_tracker(tracker, path)
        data = json.loads(path.read_text())
        assert data["counts"]["WI-1"] == 3

    def test_roundtrip_preserves_counts(self, tmp_path: Path) -> None:
        """Scenario: Save then load preserves all counts.

        Given a tracker with multiple work items
        When I save and load it
        Then all counts are preserved
        """
        original = PublishTracker(counts={"WI-1": 5, "WI-2": 2})
        path = tmp_path / "tracker.json"
        save_tracker(original, path)
        loaded = load_tracker(path)
        assert loaded.counts == original.counts

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Loading a nonexistent file returns empty tracker.

        Given no file on disk
        When I load the tracker
        Then it returns an empty tracker
        """
        path = tmp_path / "nonexistent.json"
        tracker = load_tracker(path)
        assert tracker.counts == {}

    def test_load_corrupt_file_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Loading a corrupt file returns empty tracker.

        Given a file with invalid JSON
        When I load the tracker
        Then it returns an empty tracker instead of crashing
        """
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        tracker = load_tracker(path)
        assert tracker.counts == {}

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Scenario: save_tracker creates parent directories.

        Given a path with nonexistent parent dirs
        When I save the tracker
        Then parent directories are created
        """
        path = tmp_path / "deep" / "nested" / "tracker.json"
        tracker = PublishTracker(counts={"WI-1": 1})
        save_tracker(tracker, path)
        assert path.exists()
