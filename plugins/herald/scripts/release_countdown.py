#!/usr/bin/env python3
"""Hold a release for a window anyone can pause and nobody can skip.

Anyone may start a release. The release announces itself, then waits,
and during the wait anyone with triage access can stop it by opening an
issue that carries the pause label. After the window the release
leaves. There is no flag to shorten or skip the window: the floor of
one minute exists so a zero cannot substitute for a skip.

GitHub's environment wait timer is not this. Administrators bypass it
by default, nothing in it lets anyone pause, and on the Free, Pro and
Team plans private repositories do not get it (see ADR-0029).

The countdown fails closed. An announcement that did not go out, or a
pause check that could not run, stops the release, because a window
nobody saw gives nobody a chance to step in.

Exit 0 when the release may leave, 2 when it failed closed, 3 when it
was paused. The webhook URL comes from ``RELEASE_WEBHOOK_URL``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional

from notify import send_text

DEPARTED = 0
FAILED_CLOSED = 2
PAUSED = 3

MIN_MINUTES = 1
MAX_MINUTES = 60
DEFAULT_PAUSE_LABEL = "release:pause"
WEBHOOK_ENV = "RELEASE_WEBHOOK_URL"


def open_pause_issues(repo: str, label: str) -> Optional[bool]:
    """Whether an open issue in ``repo`` carries ``label``.

    None means the lookup failed. The countdown reads that as "a pause
    cannot be ruled out", never as "not paused".
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--label",
                label,
                "--state",
                "open",
                "--json",
                "number",
                "--jq",
                "length",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip()) > 0
    except ValueError:
        return None


@dataclass(frozen=True)
class Window:
    """One release's countdown: what leaves, how long it waits, how to pause."""

    minutes: int
    release: str
    pause_hint: str = f"open an issue labeled `{DEFAULT_PAUSE_LABEL}`"
    poll_seconds: int = 30


def run_countdown(
    window: Window,
    announce: Callable[[str], bool],
    paused: Callable[[], Optional[bool]],
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Announce the release, wait out the window, and return how it ended."""
    minutes, release = window.minutes, window.release
    if not MIN_MINUTES <= minutes <= MAX_MINUTES:
        raise ValueError(
            f"the window must be between {MIN_MINUTES} and {MAX_MINUTES} "
            f"minutes, got {minutes}"
        )
    if not announce(
        f"{release} departs in {minutes} minutes. Review the changelog now. "
        f"To pause, {window.pause_hint}."
    ):
        return FAILED_CLOSED

    deadline = clock() + minutes * 60
    while True:
        state = paused()
        if state is None:
            announce(f"{release} stopped: the pause check failed, so it did not leave.")
            return FAILED_CLOSED
        if state:
            restart = "Close the pause issue and re-run to restart the window."
            announce(f"{release} paused. {restart}")
            return PAUSED
        remaining = deadline - clock()
        if remaining <= 0:
            break
        sleep(min(window.poll_seconds, remaining))

    announce(f"{release} window closed with no pause. The release is departing.")
    return DEPARTED


def main(argv: Optional[list[str]] = None) -> int:
    """Run the countdown for one release."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--minutes",
        type=int,
        required=True,
        help=f"window length, {MIN_MINUTES} to {MAX_MINUTES}",
    )
    parser.add_argument("--release", required=True, help="release name, e.g. v1.2.3")
    parser.add_argument(
        "--repo", required=True, help="owner/name whose issues hold the pause"
    )
    parser.add_argument(
        "--pause-label",
        default=DEFAULT_PAUSE_LABEL,
        help=f"issue label that pauses (default {DEFAULT_PAUSE_LABEL})",
    )
    parser.add_argument(
        "--webhook-format",
        choices=("slack", "discord", "generic"),
        default="slack",
        help="webhook payload shape (default slack)",
    )
    args = parser.parse_args(argv)

    url = os.environ.get(WEBHOOK_ENV, "")
    if not url:
        print(
            f"{WEBHOOK_ENV} is not set. The countdown will not run unannounced.",
            file=sys.stderr,
        )
        return FAILED_CLOSED

    def announce(message: str) -> bool:
        print(message)
        return send_text(url, message, args.webhook_format, source="release")

    try:
        window = Window(
            minutes=args.minutes,
            release=args.release,
            pause_hint=f"open an issue in {args.repo} labeled `{args.pause_label}`",
        )
        return run_countdown(
            window,
            announce=announce,
            paused=lambda: open_pause_issues(args.repo, args.pause_label),
        )
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return FAILED_CLOSED


if __name__ == "__main__":
    sys.exit(main())
