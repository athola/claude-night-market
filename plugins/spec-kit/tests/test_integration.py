"""Cross-command contract tests for the spec-kit workflow.

The workflow is a chain of markdown commands handing artifacts to each
other. These tests check that each hand-off is stated on both sides: the
command that produces an artifact and the command that consumes it name
the same file, format, flag or rule. They replace tests that wrote
artifacts into tmp_path and read back what they had written.
"""

from __future__ import annotations

import re

from tests._contract import read

SPECIFY = "commands/speckit-specify.md"
CLARIFY = "commands/speckit-clarify.md"
TASKS = "commands/speckit-tasks.md"
IMPLEMENT = "commands/speckit-implement.md"
ANALYZE = "commands/speckit-analyze.md"
CHECKLIST = "commands/speckit-checklist.md"
CONVERGE = "commands/speckit-converge.md"
STARTUP = "commands/speckit-startup.md"
ARTIFACTS = "skills/speckit-orchestrator/modules/artifact-structure.md"


class TestSpeckitIntegration:
    """Hand-offs between the spec-kit commands."""

    class TestCompleteWorkflow:
        """The command order from specification to convergence."""

        def test_specify_to_implement_workflow(self) -> None:
            """Each command names the next one, in specify → clarify → plan → implement → converge order."""
            assert (
                "readiness for the next phase (`/speckit-clarify` or `/speckit-plan`)"
                in read(SPECIFY)
            )
            assert (
                "expected to run (and be completed) BEFORE invoking `/speckit-plan`"
                in read(CLARIFY)
            )
            assert "After implementation, run `/speckit-converge`" in read(IMPLEMENT)

        def test_artifact_consistency(self) -> None:
            """The three artifacts analyze cross-checks are the ones the layout documents."""
            assert "(`spec.md`, `plan.md`, `tasks.md`)" in read(ANALYZE)
            layout = read(ARTIFACTS)
            for artifact in ("spec.md", "plan.md", "tasks.md"):
                assert re.search(rf"^### {re.escape(artifact)} - ", layout, re.M), (
                    artifact
                )

        def test_workflow_state_persistence(self) -> None:
            """Cross-session task state uses the env var the tasks manager is built on."""
            assert 'Use `CLAUDE_CODE_TASK_LIST_ID="speckit-{project}"`' in read(
                IMPLEMENT
            )
            assert 'ENV_VAR_PREFIX = "CLAUDE_CODE_TASK_LIST_ID"' in read(
                "scripts/tasks_manager.py"
            )
            assert (
                "Re-run `/speckit-startup` at the beginning of each new Claude session"
                in read(STARTUP)
            )

    class TestCrossCommandDataFlow:
        """Artifacts one command writes in the format the next one reads."""

        def test_spec_to_task_data_flow(self) -> None:
            """User stories in spec.md become task phases and [US] labels."""
            tasks = read(TASKS)
            assert "One phase per user story (in priority order from spec.md)" in tasks
            assert (
                "[US1], [US2], [US3], etc. (maps to user stories from spec.md)" in tasks
            )

        def test_task_to_progress_data_flow(self) -> None:
            """Implement reports per task and marks it [X] in tasks.md."""
            implement = read(IMPLEMENT)
            assert "- Report progress after each completed task" in implement
            assert "mark the task off as [X] in the tasks file" in implement

        def test_progress_to_checklist_data_flow(self) -> None:
            """Implement's checklist counter matches the lines /speckit-checklist writes."""
            counted = re.search(
                r"Incomplete items: Lines matching `([^`]+)`", read(IMPLEMENT)
            )
            written = re.search(r"`([^`]+) CHK### <requirement item>`", read(CHECKLIST))
            assert counted
            assert written
            # The line /speckit-checklist writes is the line implement counts.
            assert written.group(1) == counted.group(1) == "- [ ]"

    class TestErrorRecovery:
        """What each command does when an earlier step failed or is missing."""

        def test_partial_failure_recovery(self) -> None:
            """A failed parallel task does not discard the ones that succeeded."""
            assert (
                "- For parallel tasks [P], continue with successful tasks, report failed ones"
                in read(IMPLEMENT)
            )

        def test_missing_artifact_recovery(self) -> None:
            """A missing artifact sends the user to the command that makes it."""
            assert (
                "Abort with an error message if any required file is missing "
                "(instruct the user to run missing prerequisite command)."
                in read(ANALYZE)
            )
            assert "instruct user to run `/speckit-specify` first" in read(CLARIFY)

        def test_inconsistent_artifact_recovery(self) -> None:
            """Analyze and converge both rank a constitution conflict highest."""
            assert "Constitution conflicts are automatically CRITICAL" in read(ANALYZE)
            assert "highest-severity finding" in read(CONVERGE)
            assert (
                "If CRITICAL issues exist: Recommend resolving before `/speckit-implement`"
                in read(ANALYZE)
            )

    class TestPerformance:
        """Bounds the commands put on their own output size."""

        def test_analyze_caps_findings_at_50(self) -> None:
            """Analyze caps findings at 50 in both places it states the limit."""
            analyze = read(ANALYZE)
            assert (
                "Limit to 50 findings total; aggregate remainder in overflow summary."
                in analyze
            )
            assert "Limit findings table to 50 rows; summarize overflow" in analyze

        def test_every_generated_task_is_checked_against_the_checklist_format(
            self,
        ) -> None:
            """The tasks command tells the model to validate checkbox, ID, labels and paths."""
            assert (
                "- Format validation: Confirm ALL tasks follow the checklist format "
                "(checkbox, ID, labels, file paths)" in read(TASKS)
            )
