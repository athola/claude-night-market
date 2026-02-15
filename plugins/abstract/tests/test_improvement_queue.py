"""Tests for improvement queue management."""

import json
from pathlib import Path

from abstract.improvement_queue import ImprovementQueue


class TestImprovementQueueInit:
    """Test queue initialization and file management."""

    def test_should_create_queue_file_on_init(self, tmp_path: Path) -> None:
        """Given a directory, when queue is initialized, then queue file is created."""
        queue = ImprovementQueue(tmp_path / "improvement-queue.json")
        assert queue.queue_file.exists()

    def test_should_load_existing_queue(self, tmp_path: Path) -> None:
        """Given an existing queue file, when loaded, then entries are preserved."""
        queue_file = tmp_path / "improvement-queue.json"
        queue_file.write_text(
            json.dumps(
                {
                    "skills": {
                        "abstract:test-skill": {
                            "skill_name": "abstract:test-skill",
                            "stability_gap": 0.42,
                            "flagged_count": 2,
                            "last_flagged": "2026-02-15T04:00:00Z",
                            "execution_ids": ["exec-001", "exec-002"],
                            "status": "monitoring",
                        }
                    }
                }
            )
        )
        queue = ImprovementQueue(queue_file)
        assert "abstract:test-skill" in queue.skills
        assert queue.skills["abstract:test-skill"]["flagged_count"] == 2


class TestFlagSkill:
    """Test flagging skills for degradation."""

    def test_should_increment_flagged_count(self, tmp_path: Path) -> None:
        """Given a clean queue, when a skill is flagged, then count is 1."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )
        assert queue.skills["abstract:test-skill"]["flagged_count"] == 1

    def test_should_accumulate_flags(self, tmp_path: Path) -> None:
        """Given a flagged skill, when flagged again, then count increments."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.40, execution_id="exec-002"
        )
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.45, execution_id="exec-003"
        )
        entry = queue.skills["abstract:test-skill"]
        assert entry["flagged_count"] == 3
        assert entry["stability_gap"] == 0.45  # Latest gap
        assert len(entry["execution_ids"]) == 3

    def test_should_persist_flags_to_disk(self, tmp_path: Path) -> None:
        """Given a flagged skill, when reloaded, then flags persist."""
        queue_file = tmp_path / "queue.json"
        queue = ImprovementQueue(queue_file)
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )

        reloaded = ImprovementQueue(queue_file)
        assert reloaded.skills["abstract:test-skill"]["flagged_count"] == 1


class TestNeedsImprovement:
    """Test improvement trigger detection."""

    def test_should_not_trigger_below_threshold(self, tmp_path: Path) -> None:
        """Given 2 flags, when checked, then no improvement needed."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        queue.flag_skill("abstract:test-skill", stability_gap=0.35, execution_id="e1")
        queue.flag_skill("abstract:test-skill", stability_gap=0.40, execution_id="e2")
        assert queue.needs_improvement("abstract:test-skill") is False

    def test_should_trigger_at_threshold(self, tmp_path: Path) -> None:
        """Given 3 flags, when checked, then improvement needed."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        for i in range(3):
            queue.flag_skill(
                "abstract:test-skill", stability_gap=0.35, execution_id=f"e{i}"
            )
        assert queue.needs_improvement("abstract:test-skill") is True

    def test_should_not_trigger_during_evaluation(self, tmp_path: Path) -> None:
        """Given a skill under evaluation, when checked, then no trigger."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        for i in range(3):
            queue.flag_skill(
                "abstract:test-skill", stability_gap=0.35, execution_id=f"e{i}"
            )
        queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        assert queue.needs_improvement("abstract:test-skill") is False

    def test_get_improvable_skills_returns_only_ready(self, tmp_path: Path) -> None:
        """Given mixed queue, when queried, then only ready skills returned."""
        queue = ImprovementQueue(tmp_path / "queue.json")
        # Skill A: 3 flags, ready
        for i in range(3):
            queue.flag_skill(
                "abstract:skill-a", stability_gap=0.4, execution_id=f"a{i}"
            )
        # Skill B: 2 flags, not ready
        for i in range(2):
            queue.flag_skill(
                "abstract:skill-b", stability_gap=0.35, execution_id=f"b{i}"
            )

        result = queue.get_improvable_skills()
        assert len(result) == 1
        assert result[0] == "abstract:skill-a"
