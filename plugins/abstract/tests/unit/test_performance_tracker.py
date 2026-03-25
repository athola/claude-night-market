"""Tests for PerformanceTracker module.

Feature: Track skill performance across versions (generations)

As a skill ecosystem maintainer
I want to record and query skill performance scores per version
So that I can detect improvement trends and identify top performers
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.performance_tracker import PerformanceTracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tracker(tmp_path: Path) -> PerformanceTracker:
    return PerformanceTracker(tmp_path / "performance_history.json")


# ---------------------------------------------------------------------------
# test_record_and_retrieve
# ---------------------------------------------------------------------------


class TestRecordAndRetrieve:
    """Feature: Recording performance entries and retrieving statistics

    As a skill maintainer
    I want to record scores and read them back as statistics
    So that I can see how a skill is performing overall
    """

    @pytest.mark.unit
    def test_record_and_retrieve(self, tmp_path: Path) -> None:
        """Scenario: Record entries then retrieve statistics
        Given a fresh tracker
        When three scores are recorded for the same skill
        Then statistics reflect those three entries
        """
        tracker = _make_tracker(tmp_path)

        tracker.record_generation("abstract:my-skill", "1.0.0", 0.7)
        tracker.record_generation("abstract:my-skill", "1.0.0", 0.8)
        tracker.record_generation("abstract:my-skill", "1.0.0", 0.9)

        stats = tracker.get_statistics("abstract:my-skill")

        assert stats["total_generations"] == 3
        assert stats["best_score"] == pytest.approx(0.9)
        assert stats["worst_score"] == pytest.approx(0.7)
        assert stats["average_score"] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# test_improvement_trend_positive
# ---------------------------------------------------------------------------


class TestImprovementTrendPositive:
    """Feature: Positive improvement trend detection

    As a skill maintainer
    I want a positive trend value when recent scores exceed older scores
    So that I can identify skills that are improving
    """

    @pytest.mark.unit
    def test_improvement_trend_positive(self, tmp_path: Path) -> None:
        """Scenario: Scores improve over time
        Given a tracker with window=3
        When 6 entries are recorded with rising scores
        Then the trend is a positive float
        """
        tracker = _make_tracker(tmp_path)

        # Older window: low scores
        for score in [0.2, 0.3, 0.25]:
            tracker.record_generation("abstract:my-skill", "1.0.0", score)
        # Recent window: high scores
        for score in [0.7, 0.8, 0.9]:
            tracker.record_generation("abstract:my-skill", "1.1.0", score)

        trend = tracker.get_improvement_trend("abstract:my-skill", window=3)

        assert trend is not None
        assert trend > 0


# ---------------------------------------------------------------------------
# test_improvement_trend_negative
# ---------------------------------------------------------------------------


class TestImprovementTrendNegative:
    """Feature: Negative improvement trend detection

    As a skill maintainer
    I want a negative trend value when recent scores fall below older scores
    So that I can catch regressions early
    """

    @pytest.mark.unit
    def test_improvement_trend_negative(self, tmp_path: Path) -> None:
        """Scenario: Scores degrade over time
        Given a tracker with window=3
        When 6 entries are recorded with falling scores
        Then the trend is a negative float
        """
        tracker = _make_tracker(tmp_path)

        # Older window: high scores
        for score in [0.8, 0.85, 0.9]:
            tracker.record_generation("abstract:my-skill", "1.0.0", score)
        # Recent window: low scores
        for score in [0.4, 0.35, 0.3]:
            tracker.record_generation("abstract:my-skill", "1.1.0", score)

        trend = tracker.get_improvement_trend("abstract:my-skill", window=3)

        assert trend is not None
        assert trend < 0


# ---------------------------------------------------------------------------
# test_improvement_trend_insufficient_data
# ---------------------------------------------------------------------------


class TestImprovementTrendInsufficientData:
    """Feature: Graceful handling of insufficient data

    As a skill maintainer
    I want None returned when there is not enough history
    So that I do not act on statistically meaningless signals
    """

    @pytest.mark.unit
    def test_improvement_trend_insufficient_data(self, tmp_path: Path) -> None:
        """Scenario: Fewer than window*2 entries exist
        Given a tracker with window=5 (default)
        When only 3 entries have been recorded
        Then get_improvement_trend returns None
        """
        tracker = _make_tracker(tmp_path)

        for score in [0.5, 0.6, 0.7]:
            tracker.record_generation("abstract:my-skill", "1.0.0", score)

        trend = tracker.get_improvement_trend("abstract:my-skill")

        assert trend is None


# ---------------------------------------------------------------------------
# test_improvement_trend_with_domain_filter
# ---------------------------------------------------------------------------


class TestImprovementTrendWithDomainFilter:
    """Feature: Domain-scoped trend computation

    As a skill maintainer
    I want trends computed only for a specific domain
    So that cross-domain noise does not distort signals
    """

    @pytest.mark.unit
    def test_improvement_trend_with_domain_filter(self, tmp_path: Path) -> None:
        """Scenario: Mixed-domain history, filter to one domain
        Given entries in both 'review' and 'testing' domains
        When trend is requested for 'review' with window=3
        Then only review-domain entries influence the result
        """
        tracker = _make_tracker(tmp_path)

        # review domain: improving
        for score in [0.2, 0.25, 0.3]:
            tracker.record_generation(
                "abstract:my-skill", "1.0.0", score, domain="review"
            )
        for score in [0.7, 0.75, 0.8]:
            tracker.record_generation(
                "abstract:my-skill", "1.1.0", score, domain="review"
            )

        # testing domain: degrading (should be ignored)
        for score in [0.9, 0.85, 0.8, 0.3, 0.2, 0.1]:
            tracker.record_generation(
                "abstract:my-skill", "1.0.0", score, domain="testing"
            )

        trend = tracker.get_improvement_trend(
            "abstract:my-skill", domain="review", window=3
        )

        assert trend is not None
        assert trend > 0


# ---------------------------------------------------------------------------
# test_best_performers
# ---------------------------------------------------------------------------


class TestBestPerformers:
    """Feature: Top-K best performing skill versions

    As a skill maintainer
    I want a ranked list of the top performing entries
    So that I can identify which skill versions to recommend
    """

    @pytest.mark.unit
    def test_best_performers(self, tmp_path: Path) -> None:
        """Scenario: Multiple skills recorded, request top-3
        Given entries for three different skills with varied scores
        When get_best_performers is called with top_k=3
        Then the result is sorted descending by score, length <= 3
        """
        tracker = _make_tracker(tmp_path)

        tracker.record_generation("abstract:skill-a", "1.0.0", 0.5)
        tracker.record_generation("abstract:skill-b", "1.0.0", 0.9)
        tracker.record_generation("abstract:skill-c", "1.0.0", 0.7)
        tracker.record_generation("abstract:skill-d", "1.0.0", 0.3)

        best = tracker.get_best_performers(top_k=3)

        assert len(best) == 3
        assert best[0]["score"] >= best[1]["score"] >= best[2]["score"]
        assert best[0]["skill_ref"] == "abstract:skill-b"


# ---------------------------------------------------------------------------
# test_best_performers_domain_filter
# ---------------------------------------------------------------------------


class TestBestPerformersDomainFilter:
    """Feature: Domain-filtered best performers

    As a skill maintainer
    I want best performers scoped to a domain
    So that different domains have independent leaderboards
    """

    @pytest.mark.unit
    def test_best_performers_domain_filter(self, tmp_path: Path) -> None:
        """Scenario: Entries in two domains, filter to 'docs'
        Given entries in 'docs' and 'testing' domains
        When get_best_performers is called with domain='docs'
        Then only docs-domain entries appear in the result
        """
        tracker = _make_tracker(tmp_path)

        tracker.record_generation("abstract:skill-a", "1.0.0", 0.9, domain="docs")
        tracker.record_generation("abstract:skill-b", "1.0.0", 0.95, domain="testing")
        tracker.record_generation("abstract:skill-c", "1.0.0", 0.6, domain="docs")

        best = tracker.get_best_performers(domain="docs", top_k=5)

        assert all(e["domain"] == "docs" for e in best)
        assert len(best) == 2
        assert best[0]["skill_ref"] == "abstract:skill-a"


# ---------------------------------------------------------------------------
# test_compare_versions
# ---------------------------------------------------------------------------


class TestCompareVersions:
    """Feature: Side-by-side version comparison

    As a skill maintainer
    I want to compare two versions of a skill directly
    So that I can confirm whether an upgrade improved performance
    """

    @pytest.mark.unit
    def test_compare_versions(self, tmp_path: Path) -> None:
        """Scenario: Two versions recorded, compare them
        Given v1 entries averaging 0.5 and v2 entries averaging 0.8
        When compare_versions is called
        Then improvement is approx 0.3 and improved is True
        """
        tracker = _make_tracker(tmp_path)

        for score in [0.4, 0.5, 0.6]:
            tracker.record_generation("abstract:my-skill", "1.0.0", score)
        for score in [0.7, 0.8, 0.9]:
            tracker.record_generation("abstract:my-skill", "1.1.0", score)

        result = tracker.compare_versions("abstract:my-skill", "1.0.0", "1.1.0")

        assert result["v1_scores"] == pytest.approx([0.4, 0.5, 0.6])
        assert result["v2_scores"] == pytest.approx([0.7, 0.8, 0.9])
        assert result["v1_avg"] == pytest.approx(0.5)
        assert result["v2_avg"] == pytest.approx(0.8)
        assert result["improvement"] == pytest.approx(0.3)
        assert result["improved"] is True


# ---------------------------------------------------------------------------
# test_compare_versions_missing
# ---------------------------------------------------------------------------


class TestCompareVersionsMissing:
    """Feature: Graceful handling of missing version in comparison

    As a skill maintainer
    I want compare_versions to succeed even when one version has no data
    So that the caller does not have to guard against missing versions
    """

    @pytest.mark.unit
    def test_compare_versions_missing(self, tmp_path: Path) -> None:
        """Scenario: v2 has no recorded entries
        Given only v1 entries exist for a skill
        When compare_versions is called with a non-existent v2
        Then v2_scores is empty, v2_avg is 0.0, improved is False
        """
        tracker = _make_tracker(tmp_path)

        for score in [0.6, 0.7]:
            tracker.record_generation("abstract:my-skill", "1.0.0", score)

        result = tracker.compare_versions("abstract:my-skill", "1.0.0", "9.9.9")

        assert result["v2_scores"] == []
        assert result["v2_avg"] == pytest.approx(0.0)
        assert result["improved"] is False


# ---------------------------------------------------------------------------
# test_empty_tracker
# ---------------------------------------------------------------------------


class TestEmptyTracker:
    """Feature: Empty-state safety

    As a skill maintainer
    I want all methods to handle an empty tracker without crashing
    So that callers do not need to special-case first-run conditions
    """

    @pytest.mark.unit
    def test_empty_tracker(self, tmp_path: Path) -> None:
        """Scenario: Tracker with no recorded data
        Given a freshly created tracker
        When statistics, trend, best performers, and compare are called
        Then they return empty/None results without raising
        """
        tracker = _make_tracker(tmp_path)

        stats = tracker.get_statistics()
        assert stats["total_generations"] == 0
        assert stats["best_score"] is None
        assert stats["worst_score"] is None
        assert stats["average_score"] is None
        assert stats["improvement_trend"] is None

        trend = tracker.get_improvement_trend("abstract:nonexistent")
        assert trend is None

        best = tracker.get_best_performers()
        assert best == []

        result = tracker.compare_versions("abstract:nonexistent", "1.0.0", "2.0.0")
        assert result["v1_scores"] == []
        assert result["v2_scores"] == []
        assert result["improved"] is False


# ---------------------------------------------------------------------------
# test_persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    """Feature: Data survives process restart

    As a skill maintainer
    I want recorded data to persist to disk
    So that history survives between Claude Code sessions
    """

    @pytest.mark.unit
    def test_persistence(self, tmp_path: Path) -> None:
        """Scenario: Write data then reload from disk
        Given a tracker that recorded two entries
        When a new PerformanceTracker is created from the same file
        Then the new instance sees both entries
        """
        tracking_file = tmp_path / "performance_history.json"

        tracker1 = PerformanceTracker(tracking_file)
        tracker1.record_generation("abstract:my-skill", "1.0.0", 0.75)
        tracker1.record_generation("abstract:my-skill", "1.0.0", 0.85)

        tracker2 = PerformanceTracker(tracking_file)
        stats = tracker2.get_statistics("abstract:my-skill")

        assert stats["total_generations"] == 2
        assert stats["average_score"] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# test_corrupt_file
# ---------------------------------------------------------------------------


class TestCorruptFile:
    """Feature: Resilience to corrupt storage

    As a skill maintainer
    I want the tracker to recover gracefully from a corrupt JSON file
    So that a single corrupt file does not break the entire system
    """

    @pytest.mark.unit
    def test_corrupt_file(self, tmp_path: Path, capsys) -> None:
        """Scenario: JSON file contains invalid content
        Given a tracking file with invalid JSON
        When PerformanceTracker is initialised
        Then it starts with empty history and emits a stderr warning
        """
        tracking_file = tmp_path / "performance_history.json"
        tracking_file.write_text("{invalid json{{{{")

        tracker = PerformanceTracker(tracking_file)

        captured = capsys.readouterr()
        assert "corrupt" in captured.err
        assert tracker.get_statistics()["total_generations"] == 0
