"""Tests for wrapper_base module — _detect_breaking_changes.

SuperpowerWrapper was removed (ABS-006): 0 production consumers as of 2026-03.
"""

from __future__ import annotations

from abstract.wrapper_base import _detect_breaking_changes


class TestDetectBreakingChanges:
    """Test _detect_breaking_changes() with edge cases - addressing issue #33."""

    def test_detect_breaking_changes_empty_file_list(self) -> None:
        """_detect_breaking_changes returns empty list for empty input."""
        result = _detect_breaking_changes([])
        assert result == []

    def test_detect_breaking_changes_returns_appropriate_structure(self) -> None:
        """_detect_breaking_changes returns a list (possibly empty)."""
        result = _detect_breaking_changes([])
        assert isinstance(result, list)
