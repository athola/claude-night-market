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
