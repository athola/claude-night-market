"""Tests for the stewardship action tracker.

Feature: Stewardship Action Tracking

    As a plugin contributor
    I want stewardship actions to be recorded
    So that plugin health can reflect improvement velocity
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from stewardship_tracker import read_actions, record_action


class TestRecordAction:
    """Test recording stewardship actions to JSONL file."""

    @pytest.mark.unit
    def test_records_valid_jsonl_entry(self, tmp_path: Path) -> None:
        """Scenario: Recording a stewardship action.

        Given a stewardship tracker with a writable directory
        When a stewardship action is recorded
        Then a valid JSON line is appended to the actions file
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="plugins/sanctum/README.md",
            description="Updated stewardship section",
        )

        actions_file = actions_dir / "actions.jsonl"
        assert actions_file.exists()

        line = actions_file.read_text().strip()
        entry = json.loads(line)

        assert entry["plugin"] == "sanctum"
        assert entry["action_type"] == "doc-update"
        assert entry["file"] == "plugins/sanctum/README.md"
        assert entry["description"] == "Updated stewardship section"
        assert "timestamp" in entry

    @pytest.mark.unit
    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        """Scenario: Directory does not exist.

        Given the stewardship directory does not exist
        When an action is recorded
        Then the directory is created automatically
        """
        actions_dir = tmp_path / "nonexistent" / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="leyline",
            action_type="test-addition",
            file_path="plugins/leyline/tests/test_new.py",
            description="Added missing test",
        )

        assert actions_dir.exists()
        assert (actions_dir / "actions.jsonl").exists()

    @pytest.mark.unit
    def test_appends_without_overwriting(self, tmp_path: Path) -> None:
        """Scenario: Multiple actions recorded.

        Given an existing actions file with one entry
        When a second action is recorded
        Then both entries exist in the file
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="First action",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="Second action",
        )

        lines = (actions_dir / "actions.jsonl").read_text().strip().split("\n")
        expected_line_count = 2
        assert len(lines) == expected_line_count

        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["plugin"] == "sanctum"
        assert second["plugin"] == "imbue"


class TestReadActions:
    """Test reading and querying stewardship actions."""

    @pytest.mark.unit
    def test_reads_actions_for_plugin(self, tmp_path: Path) -> None:
        """Scenario: Querying actions by plugin.

        Given actions recorded for multiple plugins
        When querying actions for a specific plugin
        Then only that plugin's actions are returned
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="Sanctum update",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="test-addition",
            file_path="test.py",
            description="Imbue test",
        )

        sanctum_actions = read_actions(actions_dir, plugin="sanctum")
        assert len(sanctum_actions) == 1
        assert sanctum_actions[0]["plugin"] == "sanctum"

    @pytest.mark.unit
    def test_reads_all_actions_when_no_filter(self, tmp_path: Path) -> None:
        """Scenario: Querying all actions.

        Given actions recorded for multiple plugins
        When querying without a filter
        Then all actions are returned
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="First",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="test-addition",
            file_path="test.py",
            description="Second",
        )

        expected_count = 2
        all_actions = read_actions(actions_dir)
        assert len(all_actions) == expected_count

    @pytest.mark.unit
    def test_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """Scenario: No actions file exists.

        Given the stewardship directory is empty
        When querying actions
        Then an empty list is returned
        """
        actions_dir = tmp_path / "empty"
        result = read_actions(actions_dir)
        assert result == []

    @pytest.mark.unit
    def test_handles_corrupt_line_gracefully(self, tmp_path: Path) -> None:
        """Scenario: Corrupt line in actions file.

        Given an actions file with one valid and one corrupt line
        When reading actions
        Then only the valid entry is returned
        """
        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        actions_file = actions_dir / "actions.jsonl"
        actions_file.write_text(
            '{"plugin":"sanctum","action_type":"fix","file":"x","description":"ok","timestamp":"t"}\n'
            "not valid json\n"
        )

        result = read_actions(actions_dir)
        assert len(result) == 1
        assert result[0]["plugin"] == "sanctum"


class TestRecordActionVirtue:
    """Test the optional virtue parameter for record_action."""

    @pytest.mark.unit
    def test_record_action_without_virtue_unchanged(self, tmp_path: Path) -> None:
        """Verify existing behavior is preserved when virtue is omitted.

        Given a stewardship tracker
        When record_action is called without virtue
        Then the JSONL entry contains no virtue field
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="No virtue here",
        )

        line = (actions_dir / "actions.jsonl").read_text().strip()
        entry = json.loads(line)

        assert "virtue" not in entry
        assert entry["plugin"] == "sanctum"

    @pytest.mark.unit
    def test_record_action_with_virtue_included_in_jsonl(self, tmp_path: Path) -> None:
        """Verify virtue field appears in JSONL when virtue is provided.

        Given a stewardship tracker
        When record_action is called with virtue="clarity"
        Then the virtue field appears in the JSONL entry
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="leyline",
            action_type="test-addition",
            file_path="tests/test_foo.py",
            description="Added missing tests",
            virtue="clarity",
        )

        line = (actions_dir / "actions.jsonl").read_text().strip()
        entry = json.loads(line)

        assert entry["virtue"] == "clarity"

    @pytest.mark.unit
    def test_record_action_virtue_none_omits_field(self, tmp_path: Path) -> None:
        """Verify virtue field is absent when virtue=None is passed explicitly.

        Given a stewardship tracker
        When record_action is called with virtue=None
        Then the JSONL entry does not contain a virtue field
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="Fixed typo",
            virtue=None,
        )

        line = (actions_dir / "actions.jsonl").read_text().strip()
        entry = json.loads(line)

        assert "virtue" not in entry


class TestReadActionsVirtueFilter:
    """Test virtue-based filtering in read_actions."""

    @pytest.mark.unit
    def test_read_actions_filter_by_virtue(self, tmp_path: Path) -> None:
        """Verify only matching virtue entries are returned when filtering.

        Given actions recorded with different virtues
        When read_actions is called with virtue="clarity"
        Then only entries with virtue=="clarity" are returned
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="With clarity virtue",
            virtue="clarity",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="With courage virtue",
            virtue="courage",
        )

        result = read_actions(actions_dir, virtue="clarity")

        assert len(result) == 1
        assert result[0]["virtue"] == "clarity"
        assert result[0]["plugin"] == "sanctum"

    @pytest.mark.unit
    def test_read_actions_no_virtue_filter_returns_all(self, tmp_path: Path) -> None:
        """Verify default behavior returns all entries when no virtue is given.

        Given actions recorded with and without virtues
        When read_actions is called without a virtue argument
        Then all entries are returned
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="With virtue",
            virtue="clarity",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="Without virtue",
        )

        result = read_actions(actions_dir)

        expected_count = 2
        assert len(result) == expected_count

    @pytest.mark.unit
    def test_read_actions_virtue_filter_with_mixed_entries(
        self, tmp_path: Path
    ) -> None:
        """Verify entries without a virtue field are excluded when filtering.

        Given entries where some lack a virtue field and some have a virtue
        When read_actions is called with a virtue filter
        Then entries lacking the virtue field are excluded
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="Has virtue",
            virtue="clarity",
        )
        record_action(
            base_dir=actions_dir,
            plugin="leyline",
            action_type="test-addition",
            file_path="tests/test_x.py",
            description="No virtue field",
        )
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="Different virtue",
            virtue="courage",
        )

        result = read_actions(actions_dir, virtue="clarity")

        assert len(result) == 1
        assert result[0]["plugin"] == "sanctum"
        assert result[0]["virtue"] == "clarity"


class TestCombinedFilters:
    """Test combined plugin and virtue filtering."""

    @pytest.mark.unit
    def test_read_actions_combined_plugin_and_virtue_filter(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Filtering by both plugin and virtue.

        Given actions with various plugin/virtue combinations
        When read_actions is called with both plugin and virtue
        Then only entries matching both criteria are returned
        """
        actions_dir = tmp_path / "stewardship"
        # Matches both filters
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="Target entry",
            virtue="clarity",
        )
        # Matches plugin only
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="test-addition",
            file_path="test.py",
            description="Wrong virtue",
            virtue="courage",
        )
        # Matches virtue only
        record_action(
            base_dir=actions_dir,
            plugin="imbue",
            action_type="typo-fix",
            file_path="SKILL.md",
            description="Wrong plugin",
            virtue="clarity",
        )
        # Matches neither
        record_action(
            base_dir=actions_dir,
            plugin="leyline",
            action_type="refactor",
            file_path="src/lib.py",
            description="No match",
            virtue="foresight",
        )

        result = read_actions(actions_dir, plugin="sanctum", virtue="clarity")

        assert len(result) == 1
        assert result[0]["plugin"] == "sanctum"
        assert result[0]["virtue"] == "clarity"
        assert result[0]["description"] == "Target entry"


class TestEdgeCases:
    """Test edge cases in JSONL reading."""

    @pytest.mark.unit
    def test_read_actions_skips_empty_lines(self, tmp_path: Path) -> None:
        """Scenario: JSONL file contains empty lines.

        Given an actions file with empty lines between entries
        When reading actions
        Then only valid entries are returned and empty lines are skipped
        """
        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        actions_file = actions_dir / "actions.jsonl"
        actions_file.write_text(
            '{"plugin":"sanctum","action_type":"fix","file":"x","description":"first","timestamp":"t"}\n'
            "\n"
            "\n"
            '{"plugin":"imbue","action_type":"fix","file":"y","description":"second","timestamp":"t"}\n'
        )

        result = read_actions(actions_dir)

        expected_count = 2
        assert len(result) == expected_count
        assert result[0]["plugin"] == "sanctum"
        assert result[1]["plugin"] == "imbue"

    @pytest.mark.unit
    def test_read_actions_handles_os_error(self, tmp_path: Path) -> None:
        """Scenario: File exists but cannot be read.

        Given an actions file that triggers an OSError
        When reading actions
        Then an empty list is returned gracefully
        """
        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        actions_file = actions_dir / "actions.jsonl"
        actions_file.write_text("valid content\n")
        # Remove read permission to trigger OSError
        actions_file.chmod(0o000)

        result = read_actions(actions_dir)

        assert result == []

        # Restore permissions for cleanup
        actions_file.chmod(0o644)

    @pytest.mark.unit
    def test_record_action_timestamp_is_iso_format(self, tmp_path: Path) -> None:
        """Scenario: Timestamp follows ISO 8601 format.

        Given a stewardship tracker
        When an action is recorded
        Then the timestamp is a valid ISO 8601 string
        """
        actions_dir = tmp_path / "stewardship"
        record_action(
            base_dir=actions_dir,
            plugin="sanctum",
            action_type="doc-update",
            file_path="README.md",
            description="Check timestamp format",
        )

        line = (actions_dir / "actions.jsonl").read_text().strip()
        entry = json.loads(line)

        # Should not raise ValueError if format is valid
        parsed = datetime.fromisoformat(entry["timestamp"])
        assert parsed.tzinfo is not None
