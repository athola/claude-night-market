"""Tests for the skill-graph dangling-reference ratchet guard.

The guard reuses ``plugins/abstract/scripts/skill_graph.py`` to count
genuine broken ``Skill(plugin:name)`` references (the ``bugs`` category,
not the legitimate ``external`` cross-marketplace refs or template
``placeholders``) and fails a commit only when that count rises above a
committed baseline. This stops new breakage without forcing a cleanup of
pre-existing dangling refs.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_skill_graph_drift import (
    count_dangling_bugs,
    count_uncalled_libraries,
    evaluate_drift,
    evaluate_uncalled,
)


def _report(
    bugs: int,
    external: int = 0,
    placeholders: int = 0,
    uncalled: int = 0,
) -> dict:
    """Build a minimal skill_graph report with the given category sizes."""
    return {
        "dangling_refs": {
            "bugs": [{"source": f"s{i}", "target": f"t{i}"} for i in range(bugs)],
            "external": [{"source": "a", "target": "superpowers:x"}] * external,
            "placeholders": [{"source": "b", "target": "plugin:name"}] * placeholders,
        },
        "uncalled_libraries": [f"plugin:lib{i}" for i in range(uncalled)],
    }


class TestCountDanglingBugs:
    """Only the genuine-bug category is counted."""

    def test_counts_only_bugs(self) -> None:
        """External and placeholder refs are excluded from the count."""
        report = _report(bugs=3, external=20, placeholders=2)
        assert count_dangling_bugs(report) == 3

    def test_zero_when_no_bugs(self) -> None:
        """A clean graph counts zero."""
        assert count_dangling_bugs(_report(bugs=0, external=5)) == 0

    def test_missing_keys_are_safe(self) -> None:
        """A malformed report degrades to zero rather than raising."""
        assert count_dangling_bugs({}) == 0


class TestEvaluateDrift:
    """The ratchet comparison."""

    def test_equal_to_baseline_passes(self) -> None:
        """At the baseline, the commit is allowed."""
        ok, _ = evaluate_drift(current=31, baseline=31)
        assert ok is True

    def test_below_baseline_passes(self) -> None:
        """Fewer bugs than baseline passes (and is worth noting)."""
        ok, message = evaluate_drift(current=28, baseline=31)
        assert ok is True
        assert "28" in message  # nudge to lower the baseline

    def test_above_baseline_fails(self) -> None:
        """A new dangling ref pushes the count up and blocks the commit."""
        ok, message = evaluate_drift(current=32, baseline=31)
        assert ok is False
        assert "32" in message and "31" in message


class TestCountUncalledLibraries:
    """The uncalled-library count comes from the report's list."""

    def test_counts_uncalled_entries(self) -> None:
        """Each library-role skill with no inbound consumer is counted."""
        assert count_uncalled_libraries(_report(bugs=0, uncalled=6)) == 6

    def test_zero_when_all_called(self) -> None:
        """No uncalled libraries counts zero."""
        assert count_uncalled_libraries(_report(bugs=3, uncalled=0)) == 0

    def test_missing_key_is_safe(self) -> None:
        """A report without the key degrades to zero rather than raising."""
        assert count_uncalled_libraries({}) == 0


class TestEvaluateUncalled:
    """The uncalled-library ratchet comparison.

    A new library skill legitimately starts uncalled (the
    shared-utility-consumer-rule grants a 30-day grace period), so the
    escape hatch is to raise the baseline -- mirroring the dangling-ref
    ratchet's behaviour.
    """

    def test_equal_to_baseline_passes(self) -> None:
        """At the baseline, the commit is allowed."""
        ok, _ = evaluate_uncalled(current=6, baseline=6)
        assert ok is True

    def test_below_baseline_passes(self) -> None:
        """Fewer uncalled libraries than baseline passes (worth noting)."""
        ok, message = evaluate_uncalled(current=4, baseline=6)
        assert ok is True
        assert "4" in message

    def test_above_baseline_fails(self) -> None:
        """A new uncalled library pushes the count up and blocks the commit."""
        ok, message = evaluate_uncalled(current=7, baseline=6)
        assert ok is False
        assert "7" in message and "6" in message
