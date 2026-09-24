"""Tests for ``night_run.main``: the gate first, then the walk, then the proof.

``run_item`` and ``write_proof`` had no production caller; the only
thing that ever walked an item was a test. ``main`` is the entry the
watchdog can launch, and it refuses to walk anything the handoff gate
does not admit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import handoff_gate
import night_run
import pytest

from tests.test_handoff_gate import write_item
from tests.test_night_run import FakeRunner

if TYPE_CHECKING:
    from pathlib import Path


def _scripted(**_: object) -> tuple[str, str, str]:
    return ("PASS", "scripted babysitter", "")


class TestTheGateComesFirst:
    """Feature: no valid handoff, no run."""

    def test_a_refused_item_runs_nothing(self, tmp_path: Path) -> None:
        """A directory missing three of the four documents exits with the gate's code."""
        item = tmp_path / "items" / "NS-001"
        item.mkdir(parents=True)
        (item / "handoff.md").write_text(
            "---\nschema: nightshift/handoff@1\nitem: NS-001\n---\n"
        )
        runner = FakeRunner({})
        code = night_run.main(
            ["--item-dir", str(item), "--root", str(tmp_path)],
            runner=runner,
            babysitter=_scripted,
        )
        assert code == handoff_gate.MISSING
        assert runner.calls == []
        assert not (item / "proof.md").exists()


class TestAnAdmittedItemIsWalked:
    """Feature: an item the gate admits is walked and leaves a proof."""

    def test_the_walk_leaves_a_proof(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The known-good item runs commands and writes proof.md beside itself."""
        item = write_item(tmp_path)
        runner = FakeRunner({})
        code = night_run.main(
            ["--item-dir", str(item), "--root", str(tmp_path)],
            runner=runner,
            babysitter=_scripted,
        )
        assert code == 0
        proof = item / "proof.md"
        assert proof.exists()
        assert runner.calls, "the walk never ran a command"
        assert str(proof) in capsys.readouterr().out
        assert "# Proof: NS-001" in proof.read_text()


class TestABrokenWalkIsNotARefusal:
    """Feature: a walk that broke after side effects is told apart from a refusal."""

    def test_a_broken_walk_exits_distinct_code(self, tmp_path: Path) -> None:
        """A failed worktree setup exits with a code no gate refusal uses."""
        item = write_item(tmp_path)
        runner = FakeRunner({"worktree add": (128, "fatal: branch exists")})
        code = night_run.main(
            ["--item-dir", str(item), "--root", str(tmp_path)],
            runner=runner,
            babysitter=_scripted,
        )
        gate_codes = {
            handoff_gate.MISSING,
            handoff_gate.MALFORMED,
            handoff_gate.UNSAFE,
            handoff_gate.INCOHERENT,
        }
        assert code == night_run.WALK_BROKEN_EXIT
        assert code not in gate_codes | {0}
        assert "setup_failed" in (item / "proof.md").read_text()
