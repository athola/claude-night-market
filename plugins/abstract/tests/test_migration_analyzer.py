"""Tests for migration analyzer."""

from scripts.migration_analyzer import MigrationAnalyzer


def test_detects_overlapping_functionality() -> None:
    """Test that overlapping functionality is detected."""
    analyzer = MigrationAnalyzer("abstract")
    # Placeholder test
    assert analyzer is not None
