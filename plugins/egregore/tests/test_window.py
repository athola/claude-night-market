"""Tests for learning when a usage window renews.

The research constraint that shapes this module: Anthropic does not
publicly document the 5-hour window's reset semantics (rolling from
first message, or fixed clock) nor the weekly reset day. So nothing here
computes a reset time from an assumed window length. Every reset instant
is read from what the API actually returned, and when the API says
nothing, the module says it does not know rather than guessing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import window
from budget import Budget, is_in_cooldown

NOW = datetime(2026, 8, 23, 3, 0, 0, tzinfo=timezone.utc)


class TestClassify:
    """A rate limit and a spend cap need different responses."""

    def test_a_plain_rate_limit(self) -> None:
        assert window.classify("API Error: Request rejected (429)") == "rate_limit"

    def test_a_spend_cap_is_not_a_rate_limit(self) -> None:
        text = (
            "You have reached your API usage limits: "
            "You will regain access on 2026-09-01 at 00:00 UTC."
        )
        assert window.classify(text) == "spend_limit"

    def test_the_documented_spend_error_code(self) -> None:
        assert window.classify('"error_code": "enforced_spend_limit_reached"') == (
            "spend_limit"
        )

    def test_an_unrelated_failure_is_neither(self) -> None:
        assert window.classify("ModuleNotFoundError: no module named x") is None

    def test_a_529_is_capacity_not_quota(self) -> None:
        assert window.classify("API Error: Overloaded (529)") == "capacity"


class TestParseReset:
    """The reset instant comes from the response, never from a guess."""

    def test_retry_after_seconds(self) -> None:
        got = window.parse_reset({"retry-after": "1800"}, "", now=NOW)
        assert got == NOW + timedelta(seconds=1800)

    def test_rfc3339_token_reset_header(self) -> None:
        got = window.parse_reset(
            {"anthropic-ratelimit-tokens-reset": "2026-08-23T05:30:00Z"}, "", now=NOW
        )
        assert got == datetime(2026, 8, 23, 5, 30, tzinfo=timezone.utc)

    def test_the_latest_reset_header_wins(self) -> None:
        """Capacity returns only when every exhausted limit has reset."""
        got = window.parse_reset(
            {
                "anthropic-ratelimit-tokens-reset": "2026-08-23T05:30:00Z",
                "anthropic-ratelimit-requests-reset": "2026-08-23T04:00:00Z",
            },
            "",
            now=NOW,
        )
        assert got == datetime(2026, 8, 23, 5, 30, tzinfo=timezone.utc)

    def test_spend_cap_message_text(self) -> None:
        """A spend-cap 429 carries no retry-after; the time is in the prose."""
        text = "You will regain access on 2026-09-01 at 00:00 UTC."
        assert window.parse_reset({}, text, now=NOW) == datetime(
            2026, 9, 1, 0, 0, tzinfo=timezone.utc
        )

    def test_nothing_parseable_returns_none(self) -> None:
        assert window.parse_reset({}, "API Error: Request rejected (429)", NOW) is None

    def test_a_reset_already_in_the_past_returns_none(self) -> None:
        got = window.parse_reset(
            {"anthropic-ratelimit-tokens-reset": "2026-08-23T02:00:00Z"}, "", now=NOW
        )
        assert got is None


class TestRecordAgainstBudget:
    """The reset instant lands in the cooldown the watchdog already reads."""

    def test_a_parsed_reset_becomes_cooldown_until(self) -> None:
        budget = Budget()
        reset = NOW + timedelta(hours=2)
        window.record_reset(budget, reset)
        assert budget.cooldown_until == reset.isoformat()

    def test_the_recorded_cooldown_is_one_the_watchdog_honors(self) -> None:
        """`is_in_cooldown` reads the wall clock, so use a real future."""
        budget = Budget()
        reset = datetime.now(timezone.utc) + timedelta(hours=2)
        window.record_reset(budget, reset)
        assert is_in_cooldown(budget)

    def test_the_rate_limit_timestamp_is_recorded_too(self) -> None:
        budget = Budget()
        window.record_reset(budget, NOW + timedelta(hours=2), now=NOW)
        assert budget.last_rate_limit_at == NOW.isoformat()

    def test_an_unknown_reset_falls_back_to_a_named_default(self) -> None:
        """When the API said nothing, wait a stated interval, not forever."""
        budget = Budget()
        window.record_reset(budget, None, now=NOW)
        expected = NOW + timedelta(minutes=window.UNKNOWN_RESET_WAIT_MINUTES)
        assert budget.cooldown_until == expected.isoformat()


class TestResumeSchedule:
    """Turning a reset instant into something a scheduler can fire on."""

    def test_a_one_shot_cron_for_the_reset_minute(self) -> None:
        reset = datetime(2026, 8, 23, 5, 30, tzinfo=timezone.utc)
        assert window.cron_for(reset) == "30 5 23 8 *"

    def test_the_cron_is_nudged_past_the_boundary(self) -> None:
        """Firing exactly at the reset instant risks a second refusal."""
        reset = datetime(2026, 8, 23, 5, 30, tzinfo=timezone.utc)
        assert window.cron_for(reset, grace_minutes=3) == "33 5 23 8 *"

    def test_grace_can_roll_the_hour(self) -> None:
        reset = datetime(2026, 8, 23, 5, 59, tzinfo=timezone.utc)
        assert window.cron_for(reset, grace_minutes=2) == "1 6 23 8 *"


class TestUnattendedEnvironment:
    """What an unattended run should set, from the documentation."""

    def test_the_retry_watchdog_is_enabled(self) -> None:
        env = window.unattended_env({})
        assert env["CLAUDE_CODE_RETRY_WATCHDOG"] == "1"

    def test_an_operators_existing_setting_is_not_overwritten(self) -> None:
        env = window.unattended_env({"CLAUDE_CODE_RETRY_WATCHDOG": "0"})
        assert env["CLAUDE_CODE_RETRY_WATCHDOG"] == "0"


def test_module_states_that_window_length_is_undocumented() -> None:
    """The one thing this module must never do is assume a window length."""
    flat = " ".join((window.__doc__ or "").split()).lower()
    assert "not publicly documented" in flat


@pytest.mark.parametrize("bad", ["not-a-date", "", "2026-13-45T99:99:99Z"])
def test_malformed_timestamps_do_not_crash(bad: str) -> None:
    assert (
        window.parse_reset({"anthropic-ratelimit-tokens-reset": bad}, "", NOW) is None
    )


class TestPlanResume:
    """Which mechanism can actually fire a resume when the window renews.

    The harness contract decides this, not preference. ``CronCreate``
    schedules a prompt in the running session only: its own description
    says jobs "live only in this Claude session", that nothing is
    written to disk, and that the ``durable`` parameter "has no effect".
    A night run that stops on a usage limit is the case where the
    session does not survive, so the only mechanism left is the OS timer
    that ``watchdog.sh`` already runs.
    """

    RESET = datetime(2026, 8, 23, 5, 30, 0, tzinfo=timezone.utc)

    def test_the_watchdog_carries_it_when_the_session_will_not(self) -> None:
        plan = window.plan_resume(
            self.RESET, session_survives=False, watchdog_installed=True, now=NOW
        )
        assert plan.mechanism == window.WATCHDOG
        assert plan.cron is None

    def test_cron_is_refused_when_the_session_will_not_survive(self) -> None:
        """The documented failure: a session-only job cannot outlive exit."""
        plan = window.plan_resume(
            self.RESET, session_survives=False, watchdog_installed=False, now=NOW
        )
        assert plan.mechanism == window.NOTHING
        assert "session" in plan.why.lower()

    def test_cron_is_offered_only_to_a_surviving_session(self) -> None:
        plan = window.plan_resume(
            self.RESET, session_survives=True, watchdog_installed=False, now=NOW
        )
        assert plan.mechanism == window.CRON
        assert plan.cron is not None

    def test_the_cron_pins_the_day_and_month(self) -> None:
        """A one-shot must pin day-of-month and month.

        The prose in ``modules/budget.md`` showed ``"<min> <hour> * * *"``,
        which is a daily expression. Left unpinned, a reset instant more
        than a day out fires on the wrong day.
        """
        plan = window.plan_resume(
            self.RESET, session_survives=True, watchdog_installed=False, now=NOW
        )
        assert plan.cron is not None
        fields = plan.cron.split()
        assert fields[2] != "*"
        assert fields[3] != "*"

    def test_a_durable_timer_beats_a_session_job_when_both_exist(self) -> None:
        """A coarse timer that fires beats an exact one that may not."""
        plan = window.plan_resume(
            self.RESET, session_survives=True, watchdog_installed=True, now=NOW
        )
        assert plan.mechanism == window.WATCHDOG

    def test_the_grace_period_pushes_the_fire_time_past_the_boundary(self) -> None:
        plan = window.plan_resume(
            self.RESET,
            session_survives=True,
            watchdog_installed=False,
            grace_minutes=3,
            now=NOW,
        )
        assert plan.fire_at == self.RESET + timedelta(minutes=3)

    def test_a_weekly_window_is_never_given_to_a_session_job(self) -> None:
        """A reset days away outlives any session, attended or not."""
        far = NOW + timedelta(days=4)
        plan = window.plan_resume(
            far, session_survives=True, watchdog_installed=False, now=NOW
        )
        assert plan.mechanism == window.NOTHING
        assert "7 days" in plan.why or "outlive" in plan.why.lower()
