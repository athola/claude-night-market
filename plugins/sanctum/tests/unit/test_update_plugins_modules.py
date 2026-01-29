"""Unit tests for update_plugins_modules.

Tests for Phase 2-4 functionality:
- PerformanceAnalyzer (Phase 2)
- MetaEvaluator (Phase 3)
- KnowledgeQueueChecker (Phase 4)
"""

import json
import tempfile
from datetime import datetime
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
    def test_detects_missing_toc_in_long_skills(self, temp_plugin_dir):
        """
        Scenario: Detecting missing TOC in long skills

        Given an evaluation skill > 2000 chars without TOC
        When meta-evaluation is run
        Then it should be flagged as missing TOC
        """
        # Arrange
        skill_dir = temp_plugin_dir / "skills" / "long-review"
        skill_dir.mkdir(parents=True)

        # Create a long skill file (>2000 chars) without TOC
        long_content = "# Long Review\n\n" + "Content here. " * 300
        (skill_dir / "SKILL.md").write_text(long_content)

        evaluator = MetaEvaluator()

        # Act
        result = evaluator.check_plugin("test", temp_plugin_dir)

        # Assert
        assert "long-review" in result["missing_toc"]

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
        result = evaluator.check_plugin("test", temp_plugin_dir)

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
        result = evaluator.check_plugin("test", temp_plugin_dir)

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
        import time

        # Create low priority item
        low_file = temp_queue_dir / "low.md"
        low_content = "---\nstatus: pending\npriority: low\n---\n\nLow priority"
        low_file.write_text(low_content)
        time.sleep(0.01)  # Ensure different timestamps

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
