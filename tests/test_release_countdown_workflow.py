"""The publish workflow's release window is opt-in, fails closed, and is safe.

ADR-0029 adds a countdown anyone can pause. In this repository it runs
only when a repository variable turns it on, and the release build waits
for it. These tests hold the wiring that makes that true, because a
wrong ``if`` either skips the window silently or blocks every release.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "cross-framework-publish.yml"
)


@pytest.fixture(scope="module")
def jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]


def test_countdown_runs_only_when_the_repository_turns_it_on(jobs: dict) -> None:
    """GIVEN the RELEASE_COUNTDOWN_MINUTES variable is unset
    WHEN a release runs
    THEN the countdown is skipped, and a dry run never counts down.
    """
    condition = jobs["countdown"]["if"]
    assert "vars.RELEASE_COUNTDOWN_MINUTES != ''" in condition
    assert "inputs.dry_run != true" in condition


def test_the_build_waits_for_the_window_and_stops_when_it_does_not_pass(
    jobs: dict,
) -> None:
    """GIVEN the countdown paused or failed
    WHEN build-and-release is scheduled
    THEN it does not run, while a skipped countdown lets it run.
    """
    build = jobs["build-and-release"]
    assert build["needs"] == "countdown"
    assert "needs.countdown.result == 'success'" in build["if"]
    assert "needs.countdown.result == 'skipped'" in build["if"]
    assert "!cancelled()" in build["if"]
    assert "failure" not in build["if"]


def test_countdown_can_read_issues_and_outlasts_the_longest_window(
    jobs: dict,
) -> None:
    """GIVEN the pause lives in issues and a window may run 60 minutes
    WHEN the job is configured
    THEN it can read issues, and its timeout exceeds the window.
    """
    countdown = jobs["countdown"]
    assert countdown["permissions"]["issues"] == "read"
    assert countdown["timeout-minutes"] > 60


def test_no_expression_is_interpolated_into_the_countdown_shell(jobs: dict) -> None:
    """GIVEN the tag name and variables reach the countdown
    WHEN its run step is read
    THEN they arrive through env, never as ${{ }} inside the script.
    """
    for step in jobs["countdown"]["steps"]:
        assert "${{" not in step.get("run", "")
