"""Tests for wrapper_base module — _detect_breaking_changes.

SuperpowerWrapper was removed (ABS-006): 0 production consumers as of 2026-03.
"""

from __future__ import annotations

from unittest.mock import patch

from abstract.wrapper_base import _detect_breaking_changes


class TestDetectBreakingChanges:
    """Test _detect_breaking_changes() with edge cases - addressing issue #33."""

    def test_detect_breaking_changes_empty_file_list(self) -> None:
        """_detect_breaking_changes returns empty list for empty input."""
        result = _detect_breaking_changes([])
        assert result == []

    def test_detect_breaking_changes_skips_non_python_files_without_git(
        self, tmp_path
    ) -> None:
        """A non-.py file yields no changes and never reaches git."""
        doc = tmp_path / "README.md"
        doc.write_text("# Title\n")
        with patch("abstract.wrapper_base.subprocess.run") as run:
            result = _detect_breaking_changes([str(doc)])
        assert result == []
        run.assert_not_called()
