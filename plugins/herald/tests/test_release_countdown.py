"""Tests for release_countdown.py: a release window anyone can pause.

The countdown announces a release, waits, and checks for a pause the
whole time. It has no skip. It fails closed: an announcement nobody
received, or a pause check that could not run, stops the release,
because a window nobody saw gives nobody a chance to step in.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest
import release_countdown
from notify import send_text
from release_countdown import (
    DEPARTED,
    FAILED_CLOSED,
    PAUSED,
    Window,
    main,
    open_pause_issues,
    run_countdown,
)


class FakeClock:
    """A clock the countdown advances by sleeping, so no test waits."""

    def __init__(self) -> None:
        """Start at zero with nothing slept."""
        self.now = 0.0
        self.slept = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds
        self.slept += seconds


def _run(
    clock: FakeClock, paused, announce=None, minutes: int = 15
) -> tuple[int, list[str]]:
    sent: list[str] = []

    def record(message: str) -> bool:
        sent.append(message)
        return True

    code = run_countdown(
        Window(minutes=minutes, release="v1.2.3"),
        announce=announce or record,
        paused=paused,
        clock=clock.time,
        sleep=clock.sleep,
    )
    return code, sent


class TestRunCountdown:
    """The countdown's outcomes."""

    def test_an_unpaused_window_departs_after_the_full_wait(self) -> None:
        """GIVEN nobody pauses
        WHEN the countdown runs for 15 minutes
        THEN it waits the whole window, then departs and says so.
        """
        clock = FakeClock()
        code, sent = _run(clock, paused=lambda: False)
        assert code == DEPARTED
        assert clock.slept >= 15 * 60
        assert "15 minutes" in sent[0] and "v1.2.3" in sent[0]
        assert "departing" in sent[-1]

    def test_a_pause_inside_the_window_stops_the_release_early(self) -> None:
        """GIVEN someone pauses five minutes in
        WHEN the next check sees it
        THEN the release stops at once and the channel hears why.
        """
        clock = FakeClock()
        code, sent = _run(clock, paused=lambda: clock.now >= 5 * 60)
        assert code == PAUSED
        assert clock.slept < 6 * 60
        assert "paused" in sent[-1]

    def test_a_pause_landing_after_the_last_poll_is_still_caught(self) -> None:
        """GIVEN a pause that appears only at the final recheck
        WHEN the window ends
        THEN the release does not leave.
        """
        clock = FakeClock()
        code, _ = _run(clock, paused=lambda: clock.now >= 15 * 60)
        assert code == PAUSED

    def test_a_failed_announcement_fails_closed_without_waiting(self) -> None:
        """GIVEN the Slack announcement could not be sent
        WHEN the countdown starts
        THEN it stops at once, since nobody was told to look.
        """
        clock = FakeClock()
        code, _ = _run(clock, paused=lambda: False, announce=lambda message: False)
        assert code == FAILED_CLOSED
        assert clock.slept == 0

    def test_a_pause_check_that_cannot_run_fails_closed(self) -> None:
        """GIVEN the pause lookup errors partway through
        WHEN the countdown polls
        THEN the release stops, because a pause could not be ruled out.
        """
        clock = FakeClock()
        code, _ = _run(clock, paused=lambda: None if clock.now >= 60 else False)
        assert code == FAILED_CLOSED

    @pytest.mark.parametrize("minutes", [0, 61])
    def test_a_window_outside_one_to_sixty_minutes_is_refused(
        self, minutes: int
    ) -> None:
        """GIVEN a zero or over-long window
        WHEN the countdown is asked to run it
        THEN it refuses, so a zero cannot stand in for a skip.
        """
        with pytest.raises(ValueError, match="1 and 60"):
            _run(FakeClock(), paused=lambda: False, minutes=minutes)


class TestOpenPauseIssues:
    """Reading the pause signal from GitHub issues."""

    def test_counts_open_issues_carrying_the_label(self) -> None:
        """GIVEN gh lists two open issues with the pause label
        WHEN the pause check reads them
        THEN it reports a pause.
        """
        done = MagicMock(returncode=0, stdout="2\n", stderr="")
        with patch("release_countdown.subprocess.run", return_value=done) as run:
            assert open_pause_issues("o/r", "release:pause") is True
        argv = run.call_args.args[0]
        assert "--label" in argv and "release:pause" in argv

    def test_a_gh_failure_is_unknown_not_unpaused(self) -> None:
        """GIVEN gh exits nonzero
        WHEN the pause check runs
        THEN it returns None, which the countdown treats as fail closed.
        """
        failed = MagicMock(returncode=1, stdout="", stderr="HTTP 502")
        with patch("release_countdown.subprocess.run", return_value=failed):
            assert open_pause_issues("o/r", "release:pause") is None

    def test_a_missing_gh_is_unknown(self) -> None:
        """GIVEN gh is not installed
        WHEN the pause check runs
        THEN it returns None.
        """
        with patch("release_countdown.subprocess.run", side_effect=FileNotFoundError):
            assert open_pause_issues("o/r", "release:pause") is None


class TestMain:
    """The command-line entry point."""

    def test_no_webhook_configured_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN no webhook URL in the environment
        WHEN the countdown is started
        THEN it exits FAILED_CLOSED and names the variable to set.
        """
        monkeypatch.delenv("RELEASE_WEBHOOK_URL", raising=False)
        code = main(["--minutes", "15", "--release", "v1", "--repo", "o/r"])
        assert code == FAILED_CLOSED
        assert "RELEASE_WEBHOOK_URL" in capsys.readouterr().err

    def test_there_is_no_skip_option(self) -> None:
        """GIVEN a request to skip the window
        WHEN the arguments are parsed
        THEN argparse rejects it, because the window cannot be overridden.
        """
        with pytest.raises(SystemExit):
            main(["--minutes", "15", "--release", "v1", "--repo", "o/r", "--skip"])


class TestSendText:
    """herald's plain-text webhook helper."""

    @patch("subprocess.run")
    def test_slack_text_carries_the_source_label(self, run: MagicMock) -> None:
        """GIVEN a Slack webhook
        WHEN plain text is sent
        THEN the payload is Slack's text field, prefixed with the source.
        """
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        with patch("notify.validate_webhook_url", return_value="203.0.113.7"):
            assert send_text("https://hooks.slack.com/x", "hello", "slack", "release")
        payload = run.call_args.args[0][run.call_args.args[0].index("-d") + 1]
        assert '"text": "[release] hello"' in payload

    @patch("subprocess.run")
    def test_a_rejected_url_sends_nothing(self, run: MagicMock) -> None:
        """GIVEN a webhook URL that fails validation
        WHEN text is sent
        THEN it returns False and curl never runs.
        """
        assert send_text("http://127.0.0.1/x", "hello") is False
        run.assert_not_called()


class TestMainRuns:
    """The entry point with a webhook configured, on a clock no test waits on."""

    @pytest.fixture
    def fast(self, monkeypatch: pytest.MonkeyPatch) -> FakeClock:
        """Run main's countdown on a fake clock and a configured webhook."""
        clock = FakeClock()
        real = release_countdown.run_countdown
        monkeypatch.setattr(
            release_countdown,
            "run_countdown",
            lambda window, announce, paused: real(
                window, announce, paused, clock=clock.time, sleep=clock.sleep
            ),
        )
        monkeypatch.setenv("RELEASE_WEBHOOK_URL", "https://hooks.slack.com/x")
        return clock

    def test_an_unpaused_release_departs_and_is_announced_as_release(
        self, fast: FakeClock
    ) -> None:
        """GIVEN a webhook and no pause issue
        WHEN main runs a one-minute window
        THEN it exits DEPARTED and every message goes out labeled release.
        """
        with patch("release_countdown.send_text", return_value=True) as send:
            with patch("release_countdown.open_pause_issues", return_value=False):
                code = main(["--minutes", "1", "--release", "v9", "--repo", "o/r"])
        assert code == DEPARTED
        assert all(c.kwargs["source"] == "release" for c in send.call_args_list)
        assert "o/r" in send.call_args_list[0].args[1]

    def test_a_pause_issue_makes_main_exit_paused(self, fast: FakeClock) -> None:
        """GIVEN an open pause issue
        WHEN main runs
        THEN it exits PAUSED.
        """
        with patch("release_countdown.send_text", return_value=True):
            with patch("release_countdown.open_pause_issues", return_value=True):
                code = main(["--minutes", "1", "--release", "v9", "--repo", "o/r"])
        assert code == PAUSED

    def test_a_zero_minute_window_fails_closed_before_announcing(
        self, fast: FakeClock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN --minutes 0
        WHEN main runs
        THEN it fails closed, says why, and announces nothing.
        """
        with patch("release_countdown.send_text") as send:
            code = main(["--minutes", "0", "--release", "v9", "--repo", "o/r"])
        assert code == FAILED_CLOSED
        assert "1 and 60" in capsys.readouterr().err
        send.assert_not_called()


def test_gh_output_that_is_not_a_count_is_unknown() -> None:
    """GIVEN gh prints something other than a number
    WHEN the pause check reads it
    THEN it returns None rather than guessing unpaused.
    """
    odd = MagicMock(returncode=0, stdout="null\n", stderr="")
    with patch("release_countdown.subprocess.run", return_value=odd):
        assert open_pause_issues("o/r", "release:pause") is None


@pytest.mark.parametrize(
    ("webhook_format", "expected"),
    [("discord", '"content": "[release] hi"'), ("generic", '"detail": "hi"')],
)
@patch("subprocess.run")
def test_send_text_shapes_discord_and_generic_payloads(
    run: MagicMock, webhook_format: str, expected: str
) -> None:
    """GIVEN a Discord or generic webhook
    WHEN text is sent
    THEN the payload uses that format's field.
    """
    run.return_value = subprocess.CompletedProcess([], 0, "", "")
    with patch("notify.validate_webhook_url", return_value="203.0.113.7"):
        assert send_text("https://example.com/x", "hi", webhook_format, "release")
    argv = run.call_args.args[0]
    assert expected in argv[argv.index("-d") + 1]
