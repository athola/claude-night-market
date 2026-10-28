"""Unit tests for update_plugins_modules.

Tests for Phase 2-4 functionality:
- PerformanceAnalyzer (Phase 2)
- MetaEvaluator (Phase 3)
- KnowledgeQueueChecker (Phase 4)
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from update_plugins_modules import (
    KnowledgeQueueChecker,
    MetaEvaluator,
    PerformanceAnalyzer,
)


class TestPerformanceAnalyzer:
    """
    Feature: Skill performance analysis

    As a plugin maintainer
    I want to analyze skill execution metrics
    So that I can identify unstable or failing skills
    """

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            yield log_dir

    @pytest.mark.unit
    def test_analyze_plugin_with_no_logs(self, temp_log_dir):
        """
        Scenario: Analyzing plugin with no log files

        Given a plugin with no execution logs
        When performance analysis is run
        Then empty results should be returned
        """
        # Arrange
        analyzer = PerformanceAnalyzer(log_dir=temp_log_dir)

        # Act
        result = analyzer.analyze_plugin("test-plugin")

        # Assert
        assert result["unstable_skills"] == []
        assert result["recent_failures"] == []
        assert result["low_success_rate"] == []

    @pytest.mark.unit
    def test_detects_unstable_skills(self, temp_log_dir):
        """
        Scenario: Detecting skills with high stability gap

        Given a skill with stability_gap > 0.3
        When performance analysis is run
        Then the skill should be flagged as unstable
        """
        # Arrange
        log_file = temp_log_dir / "test.jsonl"
        timestamp = datetime.now().isoformat()

        log_entry = {
            "skill": "test-plugin:unstable-skill",
            "timestamp": timestamp,
            "outcome": "success",
            "metrics": {"stability_gap": 0.5},
        }

        log_file.write_text(json.dumps(log_entry))

        analyzer = PerformanceAnalyzer(log_dir=temp_log_dir)

        # Act
        result = analyzer.analyze_plugin("test-plugin")

        # Assert
        assert len(result["unstable_skills"]) == 1
        assert result["unstable_skills"][0]["skill"] == "test-plugin:unstable-skill"
        assert result["unstable_skills"][0]["stability_gap"] == 0.5

    @pytest.mark.unit
    def test_detects_recent_failures(self, temp_log_dir):
        """
        Scenario: Detecting skills with recent failures

        Given a skill with multiple failures in the last 7 days
        When performance analysis is run
        Then the skill should be flagged with failure count
        """
        # Arrange
        log_file = temp_log_dir / "test.jsonl"
        timestamp = datetime.now().isoformat()

        # Create log entries with newlines
        log_entries = []
        for _ in range(3):
            log_entry = {
                "skill": "test-plugin:failing-skill",
                "timestamp": timestamp,
                "outcome": "failure",
            }
            log_entries.append(json.dumps(log_entry))

        log_file.write_text("\n".join(log_entries))

        analyzer = PerformanceAnalyzer(log_dir=temp_log_dir)

        # Act
        result = analyzer.analyze_plugin("test-plugin")

        # Assert
        assert len(result["recent_failures"]) == 1
        assert result["recent_failures"][0]["skill"] == "test-plugin:failing-skill"
        assert result["recent_failures"][0]["failures"] == 3


class TestMetaEvaluator:
    """
    Feature: Meta-evaluation quality checks

    As a plugin maintainer
    I want evaluation skills to practice what they preach
    So that recursive quality is maintained
    """

    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary plugin directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            (plugin_dir / "skills").mkdir(parents=True)
            yield plugin_dir

    @pytest.mark.unit
    def test_identifies_eval_skills(self):
        """
        Scenario: Identifying evaluation-related skills

        Given a list of skill names
        When checking if they are evaluation-related
        Then skills with eval keywords should be identified
        """
        # Arrange
        evaluator = MetaEvaluator()

        # Act & Assert
        assert evaluator._is_eval_skill("code-review")
        assert evaluator._is_eval_skill("test-validator")
        assert evaluator._is_eval_skill("quality-audit")
        assert not evaluator._is_eval_skill("data-processor")
        assert not evaluator._is_eval_skill("helper")

    @pytest.mark.unit
    def test_exit_criteria_section_counts_as_verification(self):
        """
        Scenario: A skill's Exit Criteria are how its work is checked

        Given a skill whose only checking content is an Exit Criteria section
        When its quality is audited
        Then it is not reported as missing verification, since the repo's
        exit-criteria rule makes that section the required check
        """
        evaluator = MetaEvaluator()
        content = (
            "# Room\n\nCapture findings.\n\n## Exit Criteria\n\n- [ ] Entry written\n"
        )

        issues = evaluator._check_skill_quality("room", content)

        assert issues["missing_verification"] == []

    @pytest.mark.unit
    def test_skill_without_any_check_is_reported(self):
        """
        Scenario: A skill that never says how its work is checked

        Given a skill with no Exit Criteria and no checking language
        When its quality is audited
        Then it is reported as missing verification
        """
        evaluator = MetaEvaluator()

        issues = evaluator._check_skill_quality("bare", "# Bare\n\nDo the thing.\n")

        assert issues["missing_verification"] == ["bare"]

    @pytest.mark.unit
    def test_toc_check_disabled(self, temp_plugin_dir):
        """
        Scenario: TOC check is disabled ecosystem-wide

        Given an evaluation skill > 2000 chars without TOC
        When meta-evaluation is run
        Then it should NOT be flagged (TOC removed per 2026-04-08 audit)
        """
        # Arrange
        skill_dir = temp_plugin_dir / "skills" / "long-review"
        skill_dir.mkdir(parents=True)

        # Create a long skill file (>2000 chars) without TOC
        long_content = "# Long Review\n\n" + "Content here. " * 300
        (skill_dir / "SKILL.md").write_text(long_content)

        evaluator = MetaEvaluator()

        # Act
        result = evaluator.check_plugin(temp_plugin_dir)

        # Assert
        assert "long-review" not in result["missing_toc"]

    @pytest.mark.unit
    def test_allows_short_skills_without_toc(self, temp_plugin_dir):
        """
        Scenario: Allowing short skills without TOC

        Given an evaluation skill < 2000 chars without TOC
        When meta-evaluation is run
        Then it should NOT be flagged
        """
        # Arrange
        skill_dir = temp_plugin_dir / "skills" / "quick-check"
        skill_dir.mkdir(parents=True)

        # Create a short skill file
        short_content = "# Quick Check\n\nBrief content here."
        (skill_dir / "SKILL.md").write_text(short_content)

        evaluator = MetaEvaluator()

        # Act
        result = evaluator.check_plugin(temp_plugin_dir)

        # Assert
        assert "quick-check" not in result["missing_toc"]

    @pytest.mark.unit
    def test_detects_missing_verification_steps(self, temp_plugin_dir):
        """
        Scenario: Detecting missing verification steps

        Given an evaluation skill without verification mentions
        When meta-evaluation is run
        Then it should be flagged as missing verification
        """
        # Arrange
        skill_dir = temp_plugin_dir / "skills" / "check-quality"
        skill_dir.mkdir(parents=True)

        # Use content that definitely doesn't match verification patterns
        content = "# Check Quality\n\nJust check things.\nReview and inspect."
        (skill_dir / "SKILL.md").write_text(content)

        evaluator = MetaEvaluator()

        # Act
        result = evaluator.check_plugin(temp_plugin_dir)

        # Assert
        # check-quality should be in missing_verification since it has no verification keywords
        assert "check-quality" in result.get("missing_verification", [])


class TestKnowledgeQueueChecker:
    """
    Feature: Knowledge queue monitoring

    As a knowledge manager
    I want to scan for pending research items
    So that valuable insights aren't lost
    """

    @pytest.fixture
    def temp_queue_dir(self):
        """Create temporary queue directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_dir = Path(tmpdir)
            yield queue_dir

    @pytest.mark.unit
    def test_returns_empty_list_with_no_queue(self, temp_queue_dir):
        """
        Scenario: Checking queue when directory doesn't exist

        Given no queue directory exists
        When queue check is run
        Then empty list should be returned
        """
        # Arrange
        checker = KnowledgeQueueChecker(queue_dir=temp_queue_dir)

        # Act
        result = checker.check_queue()

        # Assert
        assert result == []

    @pytest.mark.unit
    def test_detects_pending_items(self, temp_queue_dir):
        """
        Scenario: Detecting pending research items

        Given a queue with pending items
        When queue check is run
        Then items should be returned with metadata
        """
        # Arrange
        item_file = temp_queue_dir / "research.md"
        content = "---\nstatus: pending\npriority: high\n---\n\nResearch notes"
        item_file.write_text(content)

        checker = KnowledgeQueueChecker(queue_dir=temp_queue_dir)

        # Act
        result = checker.check_queue()

        # Assert
        assert len(result) == 1
        assert result[0]["file"] == "research.md"
        assert result[0]["priority"] == "high"

    @pytest.mark.unit
    def test_skips_non_pending_items(self, temp_queue_dir):
        """
        Scenario: Skipping completed items

        Given a queue with completed items
        When queue check is run
        Then completed items should be excluded
        """
        # Arrange
        completed_file = temp_queue_dir / "done.md"
        content = "---\nstatus: completed\npriority: high\n---\n\nDone"
        completed_file.write_text(content)

        pending_file = temp_queue_dir / "todo.md"
        content = "---\nstatus: pending\npriority: medium\n---\n\nTodo"
        pending_file.write_text(content)

        checker = KnowledgeQueueChecker(queue_dir=temp_queue_dir)

        # Act
        result = checker.check_queue()

        # Assert
        assert len(result) == 1
        assert result[0]["file"] == "todo.md"

    @pytest.mark.unit
    def test_sorts_by_priority_and_age(self, temp_queue_dir):
        """
        Scenario: Sorting items by priority and age

        Given multiple queue items with different priorities
        When queue check is run
        Then items should be sorted high > medium > low
        """
        # Arrange
        # Create low priority item
        low_file = temp_queue_dir / "low.md"
        low_content = "---\nstatus: pending\npriority: low\n---\n\nLow priority"
        low_file.write_text(low_content)
        # Age the low item by setting its mtime, not by sleeping: the sort
        # puts priority before age, and the age must be a known value.
        three_days_ago = time.time() - 3 * 86400
        os.utime(low_file, (three_days_ago, three_days_ago))

        # Create high priority item
        high_file = temp_queue_dir / "high.md"
        high_content = "---\nstatus: pending\npriority: high\n---\n\nHigh priority"
        high_file.write_text(high_content)

        checker = KnowledgeQueueChecker(queue_dir=temp_queue_dir)

        # Act
        result = checker.check_queue()

        # Assert
        assert len(result) == 2
        assert result[0]["priority"] == "high"
        assert result[1]["priority"] == "low"
        assert result[1]["age_days"] == 3
        assert result[0]["age_days"] == 0


class TestLogTimestampsWithAnOffset:
    """Logger output carries a UTC offset."""

    @pytest.mark.unit
    def test_offset_timestamps_are_compared_with_the_cutoff(
        self, tmp_path: Path
    ) -> None:
        """'...+00:00' entries are analyzed, and old ones are excluded."""
        now = datetime.now(timezone.utc)
        entries = [
            {
                "skill": "sanctum:stack-create",
                "timestamp": now.isoformat(),
                "outcome": "failure",
            },
            {
                "skill": "sanctum:stack-create",
                "timestamp": (now - timedelta(days=30)).isoformat(),
                "outcome": "success",
            },
        ]
        (tmp_path / "2026-09-08.jsonl").write_text(
            "\n".join(json.dumps(entry) for entry in entries) + "\n"
        )

        result = PerformanceAnalyzer(log_dir=tmp_path).analyze_plugin("sanctum")

        (low,) = result["low_success_rate"]
        assert low["skill"] == "sanctum:stack-create"
        assert low["success_rate"] == 0.0

    @pytest.mark.unit
    def test_naive_timestamps_are_read_as_utc(self, tmp_path: Path) -> None:
        """An entry without an offset still compares against the cutoff."""
        stamp = (datetime.now(timezone.utc) - timedelta(days=30)).replace(tzinfo=None)
        entry = {
            "skill": "sanctum:stack-create",
            "timestamp": stamp.isoformat(),
            "outcome": "failure",
        }
        (tmp_path / "old.jsonl").write_text(json.dumps(entry) + "\n")

        result = PerformanceAnalyzer(log_dir=tmp_path).analyze_plugin("sanctum")

        assert result["low_success_rate"] == []


@pytest.mark.parametrize("timestamp", ["", "yesterday-ish"])
def test_log_entry_with_unreadable_timestamp_is_still_counted(
    tmp_path: Path, timestamp: str
) -> None:
    """An entry whose timestamp is empty or unparsable is not dropped as old.

    GIVEN a skill log entry for the plugin with a failure outcome
    AND an empty or unparsable timestamp
    WHEN the plugin is analyzed
    THEN the failure appears in the recent failures.
    """
    entry = {"skill": "demo:skill", "timestamp": timestamp, "outcome": "failure"}
    (tmp_path / "log.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")

    report = PerformanceAnalyzer(log_dir=tmp_path).analyze_plugin("demo")

    assert report["recent_failures"] == [{"skill": "demo:skill", "failures": 1}]


def test_log_entry_older_than_the_window_is_ignored(tmp_path: Path) -> None:
    """A readable timestamp still excludes entries before the cutoff.

    GIVEN a failure logged 30 days ago
    WHEN the plugin is analyzed over 7 days
    THEN no failure is reported.
    """
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    entry = {"skill": "demo:skill", "timestamp": old, "outcome": "failure"}
    (tmp_path / "log.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")

    report = PerformanceAnalyzer(log_dir=tmp_path).analyze_plugin("demo", days=7)

    assert report["recent_failures"] == []


class TestKnowledgeQueueReadsMemoryPalaceStaging:
    """The checker reads where memory-palace writes captures today."""

    @pytest.mark.unit
    def test_default_dir_is_the_palace_staging_dir(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MEMORY_PALACE_DATA_DIR", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        staging = (
            tmp_path
            / ".claude"
            / "plugins"
            / "data"
            / "memory-palace-claude-night-market"
            / "data"
            / "staging"
        )
        staging.mkdir(parents=True)

        assert KnowledgeQueueChecker().queue_dir == staging

    @pytest.mark.unit
    def test_the_relocation_variable_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MEMORY_PALACE_DATA_DIR", str(tmp_path / "palace"))
        expected = tmp_path / "palace" / "data" / "staging"
        assert KnowledgeQueueChecker().queue_dir == expected

    @pytest.mark.unit
    def test_a_capture_awaiting_review_is_pending(self, tmp_path):
        (tmp_path / "webfetch-1.md").write_text(
            "---\nstatus: pending_review\npriority: medium\n---\n\n# Title\n"
        )
        found = KnowledgeQueueChecker(queue_dir=tmp_path).check_queue()
        assert [item["file"] for item in found] == ["webfetch-1.md"]
