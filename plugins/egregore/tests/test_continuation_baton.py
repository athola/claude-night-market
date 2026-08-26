"""The loop's continuation signal, made observable from outside the session.

ADR-0022 records the dependency: egregore continues because its Stop
hook returns ``{"decision": "block", "reason": ...}`` and the harness
feeds the reason back as the next instruction. It also records the part
nobody could do anything about: "no test can cover the harness end of
it, so the first symptom of an upstream change is a loop that stops
after one turn."

That sentence is the defect this module addresses. Not the dependency,
which stands. The *silence*. A loop that stopped after one turn and a
loop that finished its work look identical from outside, so the failure
mode ADR-0022 names is undetectable by construction.

The baton makes it detectable. At each stop the session writes down
what it just finished, what comes next, and by when the next turn
should have started. A turn that happens advances the sequence. A turn
that does not leaves a baton past its deadline with its sequence
unmoved, which is a fact an external process can read without knowing
anything about harness internals.

The distinction the tests below exist to pin: stranded means *stalled*,
not *old*. A baton that kept advancing is healthy no matter how long
ago the run started, and a baton written seconds ago is stranded the
moment its own deadline passes with no successor. Age is not the
signal; a missed handoff is.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest
from scripts.continuation_baton import (
    BATON_VERSION,
    Baton,
    advance_baton,
    clear_baton,
    is_stranded,
    read_baton,
    write_baton,
)


@pytest.fixture
def baton_path(tmp_path: Path) -> Path:
    """Return a baton path under a temp dir, never the live one."""
    return tmp_path / "baton.json"


def _baton(sequence: int = 1, deadline: float = 2000.0) -> Baton:
    """Build a baton for unit ``sequence`` due by ``deadline``."""
    return Baton(
        sequence=sequence,
        unit="implement-the-parser",
        next_prompt="Continue the pipeline from .egregore/manifest.json",
        written_at=1000.0,
        deadline=deadline,
    )


class TestRoundTrip:
    """Persistence, and how a damaged or absent file behaves."""

    def test_a_written_baton_reads_back(self, baton_path: Path) -> None:
        """The next process over reads what the session put down."""
        write_baton(_baton(), baton_path)

        assert read_baton(baton_path).unit == "implement-the-parser"

    def test_the_file_carries_a_version(self, baton_path: Path) -> None:
        """A later shape change must be able to recognise this one."""
        write_baton(_baton(), baton_path)

        assert json.loads(baton_path.read_text())["version"] == BATON_VERSION

    def test_absent_baton_reads_as_none(self, baton_path: Path) -> None:
        """No baton means no claim, which is the state before a run."""
        assert read_baton(baton_path) is None

    def test_corrupt_baton_reads_as_none(self, baton_path: Path) -> None:
        """A truncated write must not strand a healthy run.

        Reading a damaged baton as "no claim" errs toward not
        relaunching. The opposite default would let a corrupt file
        spawn sessions.
        """
        baton_path.write_text("{ truncated")

        assert read_baton(baton_path) is None


class TestDamageIsReadAsNoClaim:
    """A baton that parses into the wrong shape must not strand a run.

    Every damage case answers None, and None means "nothing was handed
    off". That default is chosen: the opposite would let a corrupt or
    future-shaped file relaunch sessions.
    """

    def test_an_unfamiliar_version_reads_as_no_baton(self, baton_path: Path) -> None:
        """A later schema is not half-read by an earlier reader.

        The body here is a **complete and valid** baton, so the version
        check is the only thing that can reject it. An earlier version
        of this test used a partial body, which the field-shape guard
        rejected on its own: the test passed with the version check
        deleted, which is LL-006's failure repeating one commit later.
        """
        baton_path.write_text(
            json.dumps(
                {
                    "version": BATON_VERSION + 1,
                    "baton": asdict(_baton(sequence=9, deadline=2000.0)),
                }
            )
        )

        assert read_baton(baton_path) is None
        assert not is_stranded(baton_path, now=9999.0)

    def test_a_baton_missing_its_fields_reads_as_no_baton(
        self, baton_path: Path
    ) -> None:
        """A partial record is not a claim about anything."""
        baton_path.write_text(
            json.dumps({"version": BATON_VERSION, "baton": {"sequence": 1}})
        )

        assert read_baton(baton_path) is None

    def test_a_payload_with_no_baton_key_reads_as_no_baton(
        self, baton_path: Path
    ) -> None:
        """The envelope can be right while the contents are absent."""
        baton_path.write_text(json.dumps({"version": BATON_VERSION}))

        assert read_baton(baton_path) is None

    def test_a_non_object_payload_reads_as_no_baton(self, baton_path: Path) -> None:
        """Valid JSON that is not a mapping is still not a baton."""
        baton_path.write_text(json.dumps(["not", "an", "object"]))

        assert read_baton(baton_path) is None


class TestStrandedMeansStalledNotOld:
    """The distinction the mechanism exists to make."""

    def test_a_baton_past_its_deadline_is_stranded(self, baton_path: Path) -> None:
        """The session put it down and no turn picked it up."""
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)

        assert is_stranded(baton_path, now=2000.1)

    def test_a_baton_inside_its_deadline_is_not_stranded(
        self, baton_path: Path
    ) -> None:
        """The next turn still has time to start."""
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)

        assert not is_stranded(baton_path, now=1999.9)

    def test_an_advancing_baton_is_never_stranded(self, baton_path: Path) -> None:
        """A long healthy run must not read as a stalled one.

        This is the assertion that separates this mechanism from a
        timeout. Age is not the signal. The run below is well past the
        first deadline and is fine, because each turn advanced the
        sequence and set a new deadline.
        """
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)
        advance_baton(baton_path, unit="parse-the-input", now=1900.0, deadline=3000.0)
        advance_baton(baton_path, unit="write-the-tests", now=2900.0, deadline=4000.0)

        assert not is_stranded(baton_path, now=3999.0)
        assert read_baton(baton_path).sequence == 3

    def test_advancing_past_a_stranded_deadline_clears_it(
        self, baton_path: Path
    ) -> None:
        """A late turn that arrives is a recovery, not a failure."""
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)
        assert is_stranded(baton_path, now=2500.0)

        advance_baton(baton_path, unit="parse-the-input", now=2400.0, deadline=5000.0)

        assert not is_stranded(baton_path, now=2500.0)

    def test_staleness_is_measured_from_the_deadline_not_the_write(
        self, baton_path: Path
    ) -> None:
        """A timeout on write age must not be able to impersonate this.

        An earlier implementation recorded the deadline as the write
        time. That made the fields equal, and every other test here
        passed with the deadline check replaced by "older than a fixed
        interval". The revert test is what caught it.

        This baton is written at 1000 and due at 9000. Any rule keyed
        to how long ago it was written strands it early; only the
        deadline gives the right answer at both ends.
        """
        write_baton(
            Baton(
                sequence=1,
                unit="long-unit",
                next_prompt="Continue",
                written_at=1000.0,
                deadline=9000.0,
            ),
            baton_path,
        )

        assert not is_stranded(baton_path, now=5000.0)
        assert is_stranded(baton_path, now=9000.1)

    def test_no_baton_is_not_stranded(self, baton_path: Path) -> None:
        """Nothing was handed off, so nothing was dropped."""
        assert not is_stranded(baton_path, now=9999.0)

    def test_a_cleared_baton_is_not_stranded(self, baton_path: Path) -> None:
        """Finishing the work is the other way a run ends.

        Without this, every completed run would look stranded forever
        and the watchdog would relaunch it.
        """
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)

        clear_baton(baton_path)

        assert not is_stranded(baton_path, now=9999.0)
        assert read_baton(baton_path) is None


class TestTheRelaunchCarriesTheSessionsOwnInstruction:
    """What the external layer relaunches with."""

    def test_a_stranded_baton_carries_the_next_prompt(self, baton_path: Path) -> None:
        """The session said what came next; the watchdog does not guess.

        The existing watchdog falls back to a generic prompt when no
        relaunch file exists. A baton written at the moment of handoff
        knows the actual next unit, so the resumed session does not
        rediscover it.
        """
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)

        stranded = read_baton(baton_path)

        assert stranded.next_prompt.startswith("Continue the pipeline")

    def test_advance_carries_the_prompt_forward_by_default(
        self, baton_path: Path
    ) -> None:
        """A turn that does not restate the next prompt keeps the old one."""
        write_baton(_baton(sequence=1, deadline=2000.0), baton_path)

        advance_baton(baton_path, unit="parse-the-input", now=1900.0, deadline=3000.0)

        assert read_baton(baton_path).next_prompt.startswith("Continue the pipeline")

    def test_advance_on_a_missing_baton_starts_the_sequence(
        self, baton_path: Path
    ) -> None:
        """A first stop with no prior baton is an ordinary start."""
        advance_baton(
            baton_path,
            unit="first-unit",
            now=1000.0,
            deadline=3000.0,
            next_prompt="Resume from the manifest",
        )

        assert read_baton(baton_path).sequence == 1
