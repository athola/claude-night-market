"""Integration test for the full homeostatic monitoring loop.

Simulates:
1. Skill executes successfully several times
2. Skill starts degrading (stability gap rises)
3. Monitor flags it 3 times
4. Skill becomes eligible for improvement
5. Evaluation window opens
6. Regression detected -> pending_rollback_review status
"""

from pathlib import Path

from abstract.experience_library import ExperienceLibrary
from abstract.improvement_queue import ImprovementQueue
from abstract.rollback_reviewer import RollbackReviewer


class TestFullDegradationLoop:
    """End-to-end test of the degradation -> review loop."""

    def test_full_loop_degradation_to_review(self, tmp_path: Path) -> None:
        """Given a degrading skill, when full loop runs, then flagged for review."""
        queue_file = tmp_path / "improvement-queue.json"
        queue = ImprovementQueue(queue_file)

        # Phase 1: Skill degrades, gets flagged 3 times
        for i in range(3):
            queue.flag_skill(
                "abstract:degrading-skill",
                stability_gap=0.35 + (i * 0.05),
                execution_id=f"exec-{i}",
            )

        assert queue.needs_improvement("abstract:degrading-skill") is True
        improvable = queue.get_improvable_skills()
        assert "abstract:degrading-skill" in improvable

        # Phase 2: Improvement applied, evaluation starts
        queue.start_evaluation("abstract:degrading-skill", baseline_gap=0.15)
        assert queue.needs_improvement("abstract:degrading-skill") is False

        # Phase 3: Evaluation window -- skill shows regression
        for _ in range(10):
            queue.record_eval_execution("abstract:degrading-skill", stability_gap=0.40)

        assert queue.is_eval_complete("abstract:degrading-skill") is True

        # Phase 4: Decision -- regression detected
        decision = queue.evaluate("abstract:degrading-skill")
        assert decision == "pending_rollback_review"
        entry = queue.skills["abstract:degrading-skill"]
        assert entry["status"] == "pending_rollback_review"
        assert "regression_detected" in entry

    def test_full_loop_degradation_to_promotion(self, tmp_path: Path) -> None:
        """Given a degrading skill that improves, when loop runs, then promoted."""
        queue_file = tmp_path / "improvement-queue.json"
        queue = ImprovementQueue(queue_file)

        # Phase 1: Flag 3 times
        for i in range(3):
            queue.flag_skill(
                "abstract:improving-skill",
                stability_gap=0.40,
                execution_id=f"exec-{i}",
            )

        # Phase 2: Start evaluation
        queue.start_evaluation("abstract:improving-skill", baseline_gap=0.35)

        # Phase 3: Skill improves during evaluation
        for _ in range(10):
            queue.record_eval_execution("abstract:improving-skill", stability_gap=0.10)

        # Phase 4: Promoted
        decision = queue.evaluate("abstract:improving-skill")
        assert decision == "promote"

        # Phase 5: Store success in experience library
        lib = ExperienceLibrary(tmp_path / "experience-library")
        stored = lib.store(
            skill_ref="abstract:improving-skill",
            task_description="Auto-improvement: added error handling",
            approach_taken="Improved error handling based on failure logs",
            outcome="success",
            duration_ms=5000,
            tools_used=["Read", "Write", "Bash"],
            key_decisions=["Added try-except blocks for file operations"],
        )
        assert stored is True
        entries = lib.list_entries("abstract:improving-skill")
        assert len(entries) == 1

    def test_rollback_reviewer_generates_valid_issue(self) -> None:
        """Given regression data, when issue generated, then valid body."""
        reviewer = RollbackReviewer()
        body = reviewer.generate_issue_body(
            skill_name="abstract:degrading-skill",
            baseline_gap=0.15,
            current_gap=0.40,
            improvement_diff="diff --git a/skills/...",
            rollback_command="git revert abc123 --no-edit",
        )
        assert "abstract:degrading-skill" in body
        assert "0.150" in body
        assert "0.400" in body
        assert "git revert" in body
