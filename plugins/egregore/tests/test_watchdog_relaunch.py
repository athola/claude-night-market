"""What the watchdog's relaunch command must carry, and why.

Both requirements here were found by running the watchdog against a real
repository rather than by reading it. A relaunch is the one command in
egregore nobody watches happen, so the properties that make it
observable are worth pinning.
"""

from __future__ import annotations

from pathlib import Path

WATCHDOG = Path(__file__).resolve().parent.parent / "scripts" / "watchdog.sh"


def _relaunch_line() -> str:
    """Return the line that actually starts the session."""
    for line in WATCHDOG.read_text().splitlines():
        if "claude -p" in line:
            return line
    raise AssertionError("watchdog.sh no longer launches claude")


class TestTheRelaunchIsObservable:
    """A relaunch that leaves no evidence is indistinguishable from none."""

    def test_it_asks_for_structured_output(self) -> None:
        """The default text format is swallowed when a Stop hook blocks.

        Measured against a real project holding an active work item: the
        default format wrote 1 byte to the log, while
        ``--output-format json`` wrote a full result object recording
        ten turns and the dollar cost. The log is the only record of what
        the night did, so it has to be the format that survives.
        """
        assert "--output-format json" in _relaunch_line()

    def test_it_closes_stdin(self) -> None:
        """Hooks read stdin, and nohup leaves it attached to nothing.

        Every hook invocation then waits three seconds and prints a
        warning onto the same stream as the result, which is enough to
        make the JSON unparseable. Redirecting from /dev/null is the
        fix the CLI's own warning recommends.
        """
        assert "< /dev/null" in _relaunch_line()

    def test_it_still_runs_in_the_background(self) -> None:
        """The watchdog must not block its own timer slot."""
        line = _relaunch_line()
        assert line.rstrip().endswith("&")
        assert "nohup" in line

    def test_it_still_records_the_pid(self) -> None:
        """The pidfile is how the next tick knows a session is alive."""
        assert 'echo $! > "$PIDFILE"' in WATCHDOG.read_text()
