"""Tests for the index_surfacer SessionStart hook.

The hook surfaces a small set of high-importance, already-promoted
captures at session start, turning the index into an active prompt
rather than a write-only buffer. The selection and formatting logic is
pure and tested here; the I/O wrapper (`main`) is a thin shell.
"""

from __future__ import annotations

import os
import sys

# Add hooks to path for testing (mirrors the other hook tests).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

from index_surfacer import (  # noqa: E402 - import after sys.path setup
    build_session_context,
    format_context,
    select_surfaced_entries,
)


def _index() -> dict:
    """Build an index mixing promoted, pending, and archived entries."""
    return {
        "entries": {
            "https://docs.x/high": {
                "title": "High Value Note",
                "importance_score": 90,
                "maturity": "growing",
                "routing_type": "meta",
                "url": "https://docs.x/high",
            },
            "https://docs.x/mid": {
                "title": "Mid Value Note",
                "importance_score": 72,
                "maturity": "growing",
                "routing_type": "meta",
                "url": "https://docs.x/mid",
            },
            "https://docs.x/below": {
                "title": "Below Threshold",
                "importance_score": 65,
                "maturity": "growing",
                "routing_type": "meta",
                "url": "https://docs.x/below",
            },
            "https://docs.x/pending": {
                "title": "Still Pending",
                "importance_score": 50,
                "maturity": "seedling",
                "routing_type": "pending",
                "url": "https://docs.x/pending",
            },
            "https://docs.x/archived": {
                "title": "Archived",
                "importance_score": 50,
                "maturity": "seedling",
                "routing_type": "archived",
                "url": "https://docs.x/archived",
            },
        },
        "hashes": {},
    }


class TestSelectSurfacedEntries:
    """Selection of entries worth surfacing."""

    def test_excludes_pending_archived_and_below_threshold(self) -> None:
        """Only promoted entries at or above the importance floor qualify."""
        selected = select_surfaced_entries(_index(), min_importance=70)
        keys = {entry["key"] for entry in selected}
        assert keys == {"https://docs.x/high", "https://docs.x/mid"}

    def test_sorted_by_importance_and_limited(self) -> None:
        """Highest importance first, capped by limit."""
        selected = select_surfaced_entries(_index(), limit=1, min_importance=70)
        assert len(selected) == 1
        assert selected[0]["key"] == "https://docs.x/high"

    def test_empty_index_yields_nothing(self) -> None:
        """An empty index surfaces nothing."""
        assert select_surfaced_entries({"entries": {}, "hashes": {}}) == []


class TestFormatContext:
    """Rendering selected entries into hook context text."""

    def test_mentions_titles_and_count(self) -> None:
        """The rendered context names the entries and how many there are."""
        selected = select_surfaced_entries(_index(), min_importance=70)
        text = format_context(selected)
        assert "High Value Note" in text
        assert "Memory Palace" in text


class TestBuildSessionContext:
    """The flag-gated end-to-end builder."""

    def test_disabled_returns_none(self) -> None:
        """When the feature flag is off, nothing is surfaced."""
        assert build_session_context(_index(), enabled=False) is None

    def test_enabled_with_entries_returns_text(self) -> None:
        """When enabled and entries qualify, returns context text."""
        result = build_session_context(_index(), enabled=True, min_importance=70)
        assert result is not None
        assert "High Value Note" in result

    def test_enabled_but_empty_returns_none(self) -> None:
        """When enabled but nothing qualifies, returns None (stay quiet)."""
        empty = {"entries": {}, "hashes": {}}
        assert build_session_context(empty, enabled=True) is None
