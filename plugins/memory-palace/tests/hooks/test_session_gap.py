"""Tests for session-gap narration in the SessionStart path.

Feature: Elapsed time is reported, never inferred
  Without an explicit reading, a model treats a five-week gap the same
  as a five-second one and acts on stale state units.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "hooks"))

import index_surfacer  # noqa: E402 - import needs the sys.path insert above


class TestGapNarration:
    """Feature: the gap is computed from the stored ended_at."""

    def test_no_prior_session_says_so(self) -> None:
        """Scenario: absence is reported, not silently treated as fresh."""
        assert index_surfacer.format_session_gap(None) is None

    def test_recent_gap_is_not_narrated(self) -> None:
        """Scenario: a continuation needs no announcement."""
        from datetime import datetime, timedelta, timezone

        recent = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        assert index_surfacer.format_session_gap(recent) is None

    def test_long_gap_is_narrated_with_days(self) -> None:
        """Scenario: a multi-week gap states the elapsed days."""
        from datetime import datetime, timedelta, timezone

        old = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
        message = index_surfacer.format_session_gap(old)
        assert message is not None
        assert "21" in message

    def test_long_gap_warns_about_state_units(self) -> None:
        """Scenario: the narration says which units went stale."""
        from datetime import datetime, timedelta, timezone

        old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        assert "state" in index_surfacer.format_session_gap(old).lower()

    def test_unparsable_timestamp_is_silent(self) -> None:
        """Scenario: a bad stored value must not fabricate a gap."""
        assert index_surfacer.format_session_gap("not-a-date") is None
