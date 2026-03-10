"""Tests for the stewardship action tracker.

Feature: Stewardship Action Tracking

    As a plugin contributor
    I want stewardship actions to be recorded
    So that plugin health can reflect improvement velocity
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from stewardship_tracker import read_actions, record_action


class TestRecordAction:
    """Test recording stewardship actions to JSONL file."""

    @pytest.mark.unit
    def test_records_valid_jsonl_entry(self, tmp_path: Path) -> None:
        """Scenario: Recording a stewardship action
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
        """Scenario: Directory does not exist
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
        """Scenario: Multiple actions recorded
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
        assert len(lines) == 2

        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["plugin"] == "sanctum"
        assert second["plugin"] == "imbue"


class TestReadActions:
    """Test reading and querying stewardship actions."""

    @pytest.mark.unit
    def test_reads_actions_for_plugin(self, tmp_path: Path) -> None:
        """Scenario: Querying actions by plugin
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
        """Scenario: Querying all actions
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

        all_actions = read_actions(actions_dir)
        assert len(all_actions) == 2

    @pytest.mark.unit
    def test_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """Scenario: No actions file exists
        Given the stewardship directory is empty
        When querying actions
        Then an empty list is returned
        """
        actions_dir = tmp_path / "empty"
        result = read_actions(actions_dir)
        assert result == []

    @pytest.mark.unit
    def test_handles_corrupt_line_gracefully(self, tmp_path: Path) -> None:
        """Scenario: Corrupt line in actions file
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
