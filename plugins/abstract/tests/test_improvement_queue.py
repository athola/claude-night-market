"""Tests for improvement queue management."""

import json
from pathlib import Path

import pytest

from abstract.improvement_queue import ImprovementQueue, QueueEntry


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
        assert queue.skills["abstract:test-skill"].flagged_count == 2


class TestFlagSkill:
    """Test flagging skills for degradation."""

    def test_should_increment_flagged_count(
        self, fresh_queue: ImprovementQueue
    ) -> None:
        """Given a clean queue, when a skill is flagged, then count is 1."""
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )
        assert fresh_queue.skills["abstract:test-skill"].flagged_count == 1

    def test_should_accumulate_flags(self, fresh_queue: ImprovementQueue) -> None:
        """Given a flagged skill, when flagged again, then count increments."""
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.40, execution_id="exec-002"
        )
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.45, execution_id="exec-003"
        )
        entry = fresh_queue.skills["abstract:test-skill"]
        assert entry.flagged_count == 3
        assert entry.stability_gap == 0.45  # Latest gap
        assert len(entry.execution_ids) == 3

    def test_should_persist_flags_to_disk(self, tmp_path: Path) -> None:
        """Given a flagged skill, when reloaded, then flags persist."""
        queue_file = tmp_path / "queue.json"
        queue = ImprovementQueue(queue_file)
        queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="exec-001"
        )

        reloaded = ImprovementQueue(queue_file)
        assert reloaded.skills["abstract:test-skill"].flagged_count == 1


class TestNeedsImprovement:
    """Test improvement trigger detection."""

    def test_should_not_trigger_below_threshold(
        self, fresh_queue: ImprovementQueue
    ) -> None:
        """Given 2 flags, when checked, then no improvement needed."""
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.35, execution_id="e1"
        )
        fresh_queue.flag_skill(
            "abstract:test-skill", stability_gap=0.40, execution_id="e2"
        )
        assert fresh_queue.needs_improvement("abstract:test-skill") is False

    def test_should_trigger_at_threshold(self, flagged_queue: ImprovementQueue) -> None:
        """Given 3 flags, when checked, then improvement needed."""
        assert flagged_queue.needs_improvement("abstract:test-skill") is True

    def test_should_not_trigger_during_evaluation(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given a skill under evaluation, when checked, then no trigger."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        assert flagged_queue.needs_improvement("abstract:test-skill") is False

    def test_get_improvable_skills_returns_only_ready(
        self, fresh_queue: ImprovementQueue
    ) -> None:
        """Given mixed queue, when queried, then only ready skills returned."""
        # Skill A: 3 flags, ready
        for i in range(3):
            fresh_queue.flag_skill(
                "abstract:skill-a", stability_gap=0.4, execution_id=f"a{i}"
            )
        # Skill B: 2 flags, not ready
        for i in range(2):
            fresh_queue.flag_skill(
                "abstract:skill-b", stability_gap=0.35, execution_id=f"b{i}"
            )

        result = fresh_queue.get_improvable_skills()
        assert len(result) == 1
        assert result[0] == "abstract:skill-a"


class TestEvaluationWindow:
    """Test re-evaluation timer tracking."""

    def test_should_track_eval_executions(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given an evaluating skill, when execution recorded, then count increments."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        flagged_queue.record_eval_execution("abstract:test-skill", stability_gap=0.10)
        assert flagged_queue.skills["abstract:test-skill"].eval_executions == 1

    def test_should_not_complete_before_target(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given 9 eval executions, when checked, then not ready for decision."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        for _ in range(9):
            flagged_queue.record_eval_execution(
                "abstract:test-skill", stability_gap=0.10
            )
        assert flagged_queue.is_eval_complete("abstract:test-skill") is False

    def test_should_complete_at_target(self, flagged_queue: ImprovementQueue) -> None:
        """Given 10 eval executions, when checked, then ready for decision."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        for _ in range(10):
            flagged_queue.record_eval_execution(
                "abstract:test-skill", stability_gap=0.10
            )
        assert flagged_queue.is_eval_complete("abstract:test-skill") is True


class TestEvalDecision:
    """Test evaluation decision logic."""

    def test_should_promote_on_improvement(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given improved metrics after eval, when decided, then status is promoted."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.35)
        for _ in range(10):
            flagged_queue.record_eval_execution(
                "abstract:test-skill", stability_gap=0.10
            )
        decision = flagged_queue.evaluate("abstract:test-skill")
        assert decision == "promote"
        assert flagged_queue.skills["abstract:test-skill"].status == "promoted"

    def test_should_flag_for_review_on_regression(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given worse metrics after eval, when decided, then pending_rollback_review."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        for _ in range(10):
            flagged_queue.record_eval_execution(
                "abstract:test-skill", stability_gap=0.40
            )
        decision = flagged_queue.evaluate("abstract:test-skill")
        assert decision == "pending_rollback_review"
        assert (
            flagged_queue.skills["abstract:test-skill"].status
            == "pending_rollback_review"
        )

    def test_should_flag_for_review_on_no_change(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given same metrics after eval, when decided, then pending_rollback_review."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.35)
        for _ in range(10):
            flagged_queue.record_eval_execution(
                "abstract:test-skill", stability_gap=0.35
            )
        decision = flagged_queue.evaluate("abstract:test-skill")
        assert decision == "pending_rollback_review"


class TestReturnValues:
    """Test that bool return values are asserted and stderr warnings emitted."""

    def test_start_evaluation_returns_true_on_success(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given a known skill, when start_evaluation called, then returns True."""
        result = flagged_queue.start_evaluation(
            "abstract:test-skill", baseline_gap=0.15
        )
        assert result is True

    def test_start_evaluation_returns_false_for_unknown_skill(
        self, fresh_queue: ImprovementQueue, capsys
    ) -> None:
        """Given an unknown skill, when start_evaluation called, then returns False."""
        result = fresh_queue.start_evaluation("nonexistent:skill", baseline_gap=0.15)
        assert result is False
        captured = capsys.readouterr()
        assert "unknown skill" in captured.err
        assert "nonexistent:skill" in captured.err

    def test_record_eval_execution_returns_true_on_success(
        self, flagged_queue: ImprovementQueue
    ) -> None:
        """Given an evaluating skill, when execution recorded, then returns True."""
        flagged_queue.start_evaluation("abstract:test-skill", baseline_gap=0.15)
        result = flagged_queue.record_eval_execution(
            "abstract:test-skill", stability_gap=0.10
        )
        assert result is True

    def test_record_eval_execution_returns_false_for_unknown_skill(
        self, fresh_queue: ImprovementQueue, capsys
    ) -> None:
        """Given an unknown skill, when execution recorded, then returns False."""
        result = fresh_queue.record_eval_execution(
            "nonexistent:skill", stability_gap=0.1
        )
        assert result is False
        captured = capsys.readouterr()
        assert "unknown skill" in captured.err

    def test_record_eval_execution_returns_false_for_wrong_status(
        self, flagged_queue: ImprovementQueue, capsys
    ) -> None:
        """Given a non-evaluating skill, when execution recorded, then returns False."""
        result = flagged_queue.record_eval_execution(
            "abstract:test-skill", stability_gap=0.10
        )
        assert result is False
        captured = capsys.readouterr()
        assert "expected 'evaluating'" in captured.err

    def test_evaluate_returns_unknown_for_missing_skill(
        self, fresh_queue: ImprovementQueue, capsys
    ) -> None:
        """Given an unknown skill, when evaluate called, then returns 'unknown'."""
        result = fresh_queue.evaluate("nonexistent:skill")
        assert result == "unknown"
        captured = capsys.readouterr()
        assert "unknown skill" in captured.err


class TestQueueEntry:
    """The entry type makes an evaluating entry without eval_start unbuildable."""

    def test_evaluating_entry_without_eval_start_cannot_be_built(self) -> None:
        with pytest.raises(ValueError, match="eval_start"):
            QueueEntry(skill_name="abstract:s", status="evaluating")

    def test_unknown_status_cannot_be_built(self) -> None:
        with pytest.raises(ValueError, match="status"):
            QueueEntry.from_dict("abstract:s", {"status": "done"})

    def test_evaluating_entry_with_eval_start_is_built(self) -> None:
        entry = QueueEntry(
            skill_name="abstract:s",
            status="evaluating",
            eval_start="2026-01-01T00:00:00+00:00",
        )
        assert entry.eval_target == ImprovementQueue.EVAL_TARGET

    def test_from_dict_rejects_a_non_object(self) -> None:
        with pytest.raises(ValueError, match="not an object"):
            QueueEntry.from_dict("abstract:s", ["monitoring"])

    def test_from_dict_takes_skill_name_from_the_key_when_absent(self) -> None:
        entry = QueueEntry.from_dict("abstract:s", {"flagged_count": 2})
        assert entry.skill_name == "abstract:s"
        assert entry.flagged_count == 2

    def test_from_dict_ignores_keys_it_does_not_declare(self) -> None:
        entry = QueueEntry.from_dict("abstract:s", {"evaluating": True})
        assert entry.status == "monitoring"

    def test_monitoring_entry_is_stored_without_evaluation_fields(self) -> None:
        stored = QueueEntry(skill_name="abstract:s", stability_gap=0.4).to_dict()
        assert set(stored) == {
            "skill_name",
            "stability_gap",
            "flagged_count",
            "last_flagged",
            "execution_ids",
            "status",
        }

    def test_evaluating_entry_round_trips_through_its_stored_form(self) -> None:
        entry = QueueEntry(skill_name="abstract:s")
        entry.begin_evaluation(0.5, 10, 7, "1.1.0", "added checks")
        assert QueueEntry.from_dict("abstract:s", entry.to_dict()) == entry


class TestQueueFileCompatibility:
    """Files written before QueueEntry load, and an invalid entry is set aside."""

    def test_file_in_the_old_format_loads_and_is_saved_unchanged(
        self, tmp_path: Path
    ) -> None:
        queue_file = tmp_path / "improvement-queue.json"
        old = {
            "skill_name": "abstract:s",
            "stability_gap": 0.4,
            "flagged_count": 1,
            "last_flagged": "2026-02-15T04:00:00Z",
            "execution_ids": ["e1"],
            "status": "monitoring",
        }
        queue_file.write_text(json.dumps({"skills": {"abstract:s": old}}))

        queue = ImprovementQueue(queue_file)
        queue.flag_skill("abstract:other", 0.1, "e2")

        stored = json.loads(queue_file.read_text())["skills"]
        assert stored["abstract:s"] == old

    def test_evaluating_entry_without_eval_start_sets_the_file_aside(
        self, tmp_path: Path
    ) -> None:
        queue_file = tmp_path / "improvement-queue.json"
        queue_file.write_text(
            json.dumps({"skills": {"abstract:s": {"status": "evaluating"}}})
        )

        queue = ImprovementQueue(queue_file)

        assert "abstract:s" not in queue.skills
        assert list(tmp_path.glob("improvement-queue.json.corrupt-*"))


class TestAbandonEvaluation:
    """An evaluation with nothing left to judge is closed without a verdict."""

    @pytest.mark.unit
    def test_abandoned_window_returns_the_skill_to_monitoring(
        self, tmp_path: Path
    ) -> None:
        queue = ImprovementQueue(tmp_path / "queue.json")
        queue.flag_skill("abstract:s", 0.6, "exec-1")
        queue.start_evaluation("abstract:s", 0.6, history_position=20)

        assert queue.abandon_evaluation("abstract:s", "history reset")

        stored = ImprovementQueue(tmp_path / "queue.json").skills["abstract:s"]
        assert stored.status == "monitoring"
        assert stored.eval_start is None
        assert stored.eval_history_start == 0
        assert "eval_start" not in stored.to_dict()

    @pytest.mark.unit
    def test_a_skill_that_is_not_evaluating_is_left_alone(self, tmp_path: Path) -> None:
        queue = ImprovementQueue(tmp_path / "queue.json")
        queue.flag_skill("abstract:s", 0.6, "exec-1")

        assert not queue.abandon_evaluation("abstract:s", "history reset")
        assert not queue.abandon_evaluation("abstract:unknown", "history reset")
