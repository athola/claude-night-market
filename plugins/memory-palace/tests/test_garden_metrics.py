"""Tests for garden_metrics.py - Digital garden health metrics.

BDD-style tests organized by behavior:
- Computing link density (interconnectedness measure)
- Computing maintenance recency (staleness detection)
- Handling edge cases (empty gardens, missing data)
"""


# ruff: noqa: S101
import json
from datetime import timezone

import pytest

from memory_palace.garden_metrics import compute_garden_metrics, compute_metrics, iso_to_datetime


class TestIsoToDatetime:
    """Tests for ISO 8601 timestamp parsing."""

    def test_parses_utc_timestamp(self):
        """Parse UTC timestamp correctly."""
        result = iso_to_datetime("2025-12-01T12:00:00+00:00")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 1
        assert result.hour == 12
        assert result.tzinfo == timezone.utc

    def test_converts_non_utc_to_utc(self):
        """Convert non-UTC timestamps to UTC."""
        # EST is UTC-5
        result = iso_to_datetime("2025-12-01T07:00:00-05:00")
        assert result.hour == 12  # 7 AM EST = 12 PM UTC
        assert result.tzinfo == timezone.utc

    def test_handles_naive_timestamps(self):
        """Handle naive timestamps (no timezone info)."""
        # Should still parse, converting to local then UTC
        result = iso_to_datetime("2025-12-01T12:00:00")
        assert result.year == 2025


class TestComputeMetrics:
    """Tests for the core metrics computation logic."""

    def test_computes_plot_count(self, fixed_timestamp):
        """Count total plots in garden."""
        data = {
            "garden": {
                "plots": [
                    {"name": "a", "inbound_links": [], "outbound_links": []},
                    {"name": "b", "inbound_links": [], "outbound_links": []},
                    {"name": "c", "inbound_links": [], "outbound_links": []},
                ]
            }
        }
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["plots"] == 3

    def test_computes_link_density_for_interconnected_garden(self, fixed_timestamp):
        """Link density = average (inbound + outbound) links per plot."""
        data = {
            "garden": {
                "plots": [
                    {"name": "a", "inbound_links": ["b"], "outbound_links": ["c"]},  # 2 links
                    {"name": "b", "inbound_links": [], "outbound_links": ["a", "c"]},  # 2 links
                    {"name": "c", "inbound_links": ["a", "b"], "outbound_links": []},  # 2 links
                ]
            }
        }
        # Average: (2 + 2 + 2) / 3 = 2.0
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["link_density"] == 2.0

    def test_handles_duplicate_links(self, fixed_timestamp):
        """Duplicate links should be deduplicated before counting."""
        data = {
            "garden": {
                "plots": [
                    {"name": "a", "inbound_links": ["b", "b", "b"], "outbound_links": ["c", "c"]},
                ]
            }
        }
        # Unique: 1 inbound + 1 outbound = 2
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["link_density"] == 2.0

    def test_computes_avg_days_since_tend(self, fixed_timestamp):
        """Compute average days since last tending."""
        # fixed_timestamp is 2025-12-01 12:00 UTC
        one_day_ago = "2025-11-30T12:00:00+00:00"
        three_days_ago = "2025-11-28T12:00:00+00:00"

        data = {
            "garden": {
                "plots": [
                    {"name": "a", "last_tended": one_day_ago},
                    {"name": "b", "last_tended": three_days_ago},
                ]
            }
        }
        # Average: (1 + 3) / 2 = 2.0
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] == 2.0

    def test_handles_mixed_tended_untended_plots(self, fixed_timestamp):
        """Average only includes plots with last_tended timestamps."""
        one_day_ago = "2025-11-30T12:00:00+00:00"

        data = {
            "garden": {
                "plots": [
                    {"name": "a", "last_tended": one_day_ago},
                    {"name": "b"},  # Never tended, no timestamp
                    {"name": "c", "last_tended": None},  # Explicitly null
                ]
            }
        }
        # Only plot 'a' has valid timestamp
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] == 1.0

    def test_returns_none_when_no_plots_have_timestamps(self, fixed_timestamp):
        """Return None for avg_days_since_tend when no plots have timestamps."""
        data = {"garden": {"plots": [{"name": "a"}, {"name": "b"}]}}
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] is None

    def test_handles_empty_garden(self, fixed_timestamp):
        """Empty garden returns zero metrics gracefully."""
        data = {"garden": {"plots": []}}
        metrics = compute_metrics(data, fixed_timestamp)

        assert metrics["plots"] == 0
        assert metrics["link_density"] == 0.0
        assert metrics["avg_days_since_tend"] is None

    def test_handles_missing_garden_key(self, fixed_timestamp):
        """Missing 'garden' key treated as empty."""
        data = {}
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["plots"] == 0

    def test_handles_null_link_lists(self, fixed_timestamp):
        """Null link lists treated as empty."""
        data = {
            "garden": {
                "plots": [
                    {"name": "a", "inbound_links": None, "outbound_links": None},
                ]
            }
        }
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["link_density"] == 0.0


class TestComputeGardenMetrics:
    """Integration tests for the file-based metrics computation."""

    def test_loads_and_computes_metrics_from_file(self, sample_garden_file, fixed_timestamp):
        """Load garden JSON and compute metrics."""
        metrics = compute_garden_metrics(sample_garden_file, fixed_timestamp)

        assert "plots" in metrics
        assert "link_density" in metrics
        assert "avg_days_since_tend" in metrics
        assert metrics["plots"] == 3

    def test_uses_current_time_when_not_specified(self, sample_garden_file):
        """Use current time if no timestamp provided."""
        metrics = compute_garden_metrics(sample_garden_file)

        # Should still compute without error
        assert "plots" in metrics
        assert metrics["plots"] == 3

    def test_raises_on_nonexistent_file(self, tmp_path):
        """Raise FileNotFoundError for missing garden file."""
        nonexistent = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            compute_garden_metrics(nonexistent)

    def test_raises_on_invalid_json(self, tmp_path):
        """Raise JSONDecodeError for malformed JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            compute_garden_metrics(bad_file)


class TestLinkDensityEdgeCases:
    """Edge cases for link density calculations."""

    def test_single_plot_isolated(self, fixed_timestamp):
        """Single isolated plot has zero link density."""
        data = {
            "garden": {
                "plots": [{"name": "lonely", "inbound_links": [], "outbound_links": []}]
            }
        }
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["link_density"] == 0.0

    def test_highly_connected_plot(self, fixed_timestamp):
        """Plot with many links contributes correctly to average."""
        data = {
            "garden": {
                "plots": [
                    {
                        "name": "hub",
                        "inbound_links": ["a", "b", "c", "d", "e"],
                        "outbound_links": ["f", "g", "h", "i", "j"],
                    },  # 10 links
                    {
                        "name": "spoke",
                        "inbound_links": [],
                        "outbound_links": [],
                    },  # 0 links
                ]
            }
        }
        # Average: (10 + 0) / 2 = 5.0
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["link_density"] == 5.0


class TestRecencyEdgeCases:
    """Edge cases for tending recency calculations."""

    def test_just_tended_plot(self, fixed_timestamp):
        """Plot tended at exactly 'now' has 0 days since tend."""
        data = {
            "garden": {
                "plots": [{"name": "fresh", "last_tended": fixed_timestamp.isoformat()}]
            }
        }
        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] == 0.0

    def test_ancient_plot(self, fixed_timestamp):
        """Very old plot computes correctly."""
        # 100 days before fixed_timestamp (2025-12-01)
        ancient = "2025-08-23T12:00:00+00:00"
        data = {"garden": {"plots": [{"name": "ancient", "last_tended": ancient}]}}

        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] == 100.0

    def test_fractional_days(self, fixed_timestamp):
        """Partial days are rounded to 2 decimal places."""
        # 12 hours ago = 0.5 days
        half_day_ago = "2025-12-01T00:00:00+00:00"
        data = {"garden": {"plots": [{"name": "recent", "last_tended": half_day_ago}]}}

        metrics = compute_metrics(data, fixed_timestamp)
        assert metrics["avg_days_since_tend"] == 0.5
