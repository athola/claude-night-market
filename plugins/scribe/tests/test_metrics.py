"""Tests for historical slop metrics tracking.

Issue #139: Historical slop tracking and metrics

Tests verify JSON serialization, trend calculation, regression detection,
file naming, and summary statistics as specified in modules/metrics.md.
"""

import json
import os
from datetime import datetime
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Helpers that mirror the logic described in the module
# ---------------------------------------------------------------------------


def make_timestamp(dt: datetime) -> str:
    """Return ISO format timestamp string."""
    return dt.isoformat()


def make_filename(dt: datetime) -> str:
    """Return the scan filename for a given datetime."""
    return "scan-" + dt.strftime("%Y-%m-%d-%H%M%S") + ".json"


def build_summary(scores: list[dict[str, Any]], total_markers: int) -> dict[str, Any]:
    """Compute summary statistics from a list of score dicts."""
    values = [s["score"] for s in scores]
    avg = sum(values) / len(values) if values else 0.0
    maximum = max(values) if values else 0.0
    return {
        "avg_score": round(avg, 4),
        "max_score": maximum,
        "total_markers": total_markers,
    }


def build_record(
    dt: datetime,
    scores: list[dict[str, Any]],
    total_markers: int,
) -> dict[str, Any]:
    """Build a complete scan record dict."""
    return {
        "timestamp": make_timestamp(dt),
        "files_scanned": len(scores),
        "scores": scores,
        "summary": build_summary(scores, total_markers),
    }


def save_record(record: dict[str, Any], history_dir: str, dt: datetime) -> str:
    """Write a record to the history directory. Returns the file path written."""
    os.makedirs(history_dir, exist_ok=True)
    path = os.path.join(history_dir, make_filename(dt))
    with open(path, "w") as fh:
        json.dump(record, fh)
    return path


def load_history(history_dir: str) -> list[dict[str, Any]]:
    """Load all scan records from history_dir, sorted chronologically."""
    if not os.path.isdir(history_dir):
        return []
    files = sorted(f for f in os.listdir(history_dir) if f.endswith(".json"))
    records = []
    for fname in files:
        with open(os.path.join(history_dir, fname)) as fh:
            records.append(json.load(fh))
    return records


def compute_delta(records: list[dict[str, Any]]) -> list[float | None]:
    """Return per-record deltas; first entry is None."""
    deltas: list[float | None] = []
    for i, rec in enumerate(records):
        if i == 0:
            deltas.append(None)
        else:
            prev = records[i - 1]["summary"]["avg_score"]
            curr = rec["summary"]["avg_score"]
            deltas.append(round(curr - prev, 4))
    return deltas


def check_regression(
    records: list[dict[str, Any]], threshold: float = 0.5
) -> float | None:
    """Return the delta if the last two records show a regression, else None."""
    if len(records) < 2:
        return None
    prev = records[-2]["summary"]["avg_score"]
    curr = records[-1]["summary"]["avg_score"]
    delta = curr - prev
    return delta if delta > threshold else None


# ---------------------------------------------------------------------------
# Tests: file naming
# ---------------------------------------------------------------------------


class TestFileNaming:
    """Feature: Scan files are named with a timestamp."""

    @pytest.mark.unit
    def test_filename_format(self) -> None:
        """Scenario: Filename follows scan-YYYY-MM-DD-HHMMSS.json pattern.

        Given a datetime of 2026-03-01 14:30:22
        When generating a filename
        Then it equals scan-2026-03-01-143022.json.
        """
        dt = datetime(2026, 3, 1, 14, 30, 22)
        assert make_filename(dt) == "scan-2026-03-01-143022.json"

    @pytest.mark.unit
    def test_filename_zero_padded(self) -> None:
        """Scenario: Single-digit month and day are zero-padded."""
        dt = datetime(2026, 1, 5, 9, 5, 3)
        assert make_filename(dt) == "scan-2026-01-05-090503.json"

    @pytest.mark.unit
    def test_filename_starts_with_scan(self) -> None:
        """Scenario: All filenames begin with 'scan-'."""
        dt = datetime(2026, 6, 15, 0, 0, 0)
        assert make_filename(dt).startswith("scan-")

    @pytest.mark.unit
    def test_filename_ends_with_json(self) -> None:
        """Scenario: All filenames end with '.json'."""
        dt = datetime(2026, 6, 15, 12, 0, 0)
        assert make_filename(dt).endswith(".json")


# ---------------------------------------------------------------------------
# Tests: JSON serialization / deserialization
# ---------------------------------------------------------------------------


class TestSerialization:
    """Feature: Scan records round-trip through JSON without data loss."""

    @pytest.mark.unit
    def test_record_serializes_to_json(self, tmp_path: Any) -> None:
        """Scenario: A record can be written and read back as valid JSON.

        Given a complete scan record
        When written to a file and read back
        Then all fields are preserved.
        """
        dt = datetime(2026, 3, 1, 10, 0, 0)
        scores = [{"path": "docs/guide.md", "score": 1.4, "word_count": 320}]
        record = build_record(dt, scores, total_markers=5)
        path = save_record(record, str(tmp_path), dt)

        with open(path) as fh:
            loaded = json.load(fh)

        assert loaded["files_scanned"] == 1
        assert loaded["scores"][0]["path"] == "docs/guide.md"
        assert loaded["scores"][0]["score"] == pytest.approx(1.4)
        assert loaded["scores"][0]["word_count"] == 320

    @pytest.mark.unit
    def test_timestamp_is_iso_string(self, tmp_path: Any) -> None:
        """Scenario: The timestamp field is an ISO 8601 string."""
        dt = datetime(2026, 3, 1, 14, 30, 22)
        scores: list[dict[str, Any]] = []
        record = build_record(dt, scores, total_markers=0)
        path = save_record(record, str(tmp_path), dt)

        with open(path) as fh:
            loaded = json.load(fh)

        assert loaded["timestamp"] == "2026-03-01T14:30:22"

    @pytest.mark.unit
    def test_multiple_scores_preserved(self, tmp_path: Any) -> None:
        """Scenario: All score entries survive a round-trip."""
        dt = datetime(2026, 3, 2, 8, 0, 0)
        scores = [
            {"path": "README.md", "score": 0.5, "word_count": 100},
            {"path": "docs/api.md", "score": 3.2, "word_count": 800},
        ]
        record = build_record(dt, scores, total_markers=12)
        path = save_record(record, str(tmp_path), dt)

        with open(path) as fh:
            loaded = json.load(fh)

        assert len(loaded["scores"]) == 2
        assert loaded["scores"][1]["path"] == "docs/api.md"


# ---------------------------------------------------------------------------
# Tests: summary statistics
# ---------------------------------------------------------------------------


class TestSummaryStatistics:
    """Feature: Summary statistics are computed from per-file scores."""

    @pytest.mark.unit
    def test_avg_score_single_file(self) -> None:
        """Scenario: avg_score for one file equals that file's score."""
        scores = [{"path": "a.md", "score": 2.5, "word_count": 200}]
        summary = build_summary(scores, total_markers=4)
        assert summary["avg_score"] == pytest.approx(2.5)

    @pytest.mark.unit
    def test_avg_score_multiple_files(self) -> None:
        """Scenario: avg_score is the mean of all file scores."""
        scores = [
            {"path": "a.md", "score": 1.0, "word_count": 100},
            {"path": "b.md", "score": 3.0, "word_count": 100},
        ]
        summary = build_summary(scores, total_markers=8)
        assert summary["avg_score"] == pytest.approx(2.0)

    @pytest.mark.unit
    def test_max_score(self) -> None:
        """Scenario: max_score is the highest individual file score."""
        scores = [
            {"path": "a.md", "score": 1.0, "word_count": 100},
            {"path": "b.md", "score": 5.5, "word_count": 200},
            {"path": "c.md", "score": 2.3, "word_count": 150},
        ]
        summary = build_summary(scores, total_markers=20)
        assert summary["max_score"] == pytest.approx(5.5)

    @pytest.mark.unit
    def test_total_markers_stored(self) -> None:
        """Scenario: total_markers reflects the value passed in."""
        scores = [{"path": "a.md", "score": 1.0, "word_count": 100}]
        summary = build_summary(scores, total_markers=7)
        assert summary["total_markers"] == 7

    @pytest.mark.unit
    def test_empty_scores_yields_zeros(self) -> None:
        """Scenario: No files produce zero avg and max scores."""
        summary = build_summary([], total_markers=0)
        assert summary["avg_score"] == 0.0
        assert summary["max_score"] == 0.0
        assert summary["total_markers"] == 0


# ---------------------------------------------------------------------------
# Tests: trend calculation
# ---------------------------------------------------------------------------


class TestTrendCalculation:
    """Feature: Delta values are computed between consecutive scans."""

    @pytest.mark.unit
    def test_first_record_delta_is_none(self) -> None:
        """Scenario: The first record has no previous scan to compare against."""
        records = [
            {"summary": {"avg_score": 1.2}},
        ]
        deltas = compute_delta(records)
        assert deltas[0] is None

    @pytest.mark.unit
    def test_positive_delta(self) -> None:
        """Scenario: Score increase produces a positive delta."""
        records = [
            {"summary": {"avg_score": 1.0}},
            {"summary": {"avg_score": 1.5}},
        ]
        deltas = compute_delta(records)
        assert deltas[1] == pytest.approx(0.5)

    @pytest.mark.unit
    def test_negative_delta(self) -> None:
        """Scenario: Score decrease produces a negative delta."""
        records = [
            {"summary": {"avg_score": 2.0}},
            {"summary": {"avg_score": 1.2}},
        ]
        deltas = compute_delta(records)
        assert deltas[1] == pytest.approx(-0.8)

    @pytest.mark.unit
    def test_zero_delta(self) -> None:
        """Scenario: Identical scores produce a zero delta."""
        records = [
            {"summary": {"avg_score": 1.5}},
            {"summary": {"avg_score": 1.5}},
        ]
        deltas = compute_delta(records)
        assert deltas[1] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_three_records_all_deltas(self) -> None:
        """Scenario: Three records produce two non-None deltas."""
        records = [
            {"summary": {"avg_score": 1.0}},
            {"summary": {"avg_score": 1.3}},
            {"summary": {"avg_score": 1.9}},
        ]
        deltas = compute_delta(records)
        assert deltas[0] is None
        assert deltas[1] == pytest.approx(0.3)
        assert deltas[2] == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Tests: regression detection
# ---------------------------------------------------------------------------


class TestRegressionDetection:
    """Feature: Warn when avg score jumps by more than 0.5."""

    @pytest.mark.unit
    def test_regression_above_threshold(self) -> None:
        """Scenario: Increase of 0.62 triggers a regression warning.

        Given two records with avg scores 1.28 and 1.90
        When checking for regression
        Then the delta 0.62 is returned.
        """
        records = [
            {"summary": {"avg_score": 1.28}},
            {"summary": {"avg_score": 1.90}},
        ]
        delta = check_regression(records)
        assert delta is not None
        assert delta == pytest.approx(0.62)

    @pytest.mark.unit
    def test_no_regression_below_threshold(self) -> None:
        """Scenario: Increase of 0.45 does not trigger a warning."""
        records = [
            {"summary": {"avg_score": 1.0}},
            {"summary": {"avg_score": 1.45}},
        ]
        assert check_regression(records) is None

    @pytest.mark.unit
    def test_no_regression_at_threshold(self) -> None:
        """Scenario: Increase of exactly 0.5 does not trigger a warning (strictly >)."""
        records = [
            {"summary": {"avg_score": 1.0}},
            {"summary": {"avg_score": 1.5}},
        ]
        assert check_regression(records) is None

    @pytest.mark.unit
    def test_no_regression_score_decreases(self) -> None:
        """Scenario: A score decrease never triggers a warning."""
        records = [
            {"summary": {"avg_score": 3.0}},
            {"summary": {"avg_score": 1.0}},
        ]
        assert check_regression(records) is None

    @pytest.mark.unit
    def test_single_record_no_regression(self) -> None:
        """Scenario: Only one record means no comparison is possible."""
        records = [{"summary": {"avg_score": 2.0}}]
        assert check_regression(records) is None

    @pytest.mark.unit
    def test_empty_history_no_regression(self) -> None:
        """Scenario: Empty history never triggers a regression."""
        assert check_regression([]) is None


# ---------------------------------------------------------------------------
# Tests: history loading
# ---------------------------------------------------------------------------


class TestHistoryLoading:
    """Feature: Load all scan records from the history directory."""

    @pytest.mark.unit
    def test_loads_records_in_order(self, tmp_path: Any) -> None:
        """Scenario: Records are returned sorted by filename (chronological).

        Given two scan files written out of order
        When history is loaded
        Then records appear oldest-first.
        """
        dt1 = datetime(2026, 2, 1, 9, 0, 0)
        dt2 = datetime(2026, 3, 1, 9, 0, 0)
        scores: list[dict[str, Any]] = []
        r1 = build_record(dt1, scores, 0)
        r2 = build_record(dt2, scores, 0)
        # Write newer first to confirm sorting is by name not write order
        save_record(r2, str(tmp_path), dt2)
        save_record(r1, str(tmp_path), dt1)

        records = load_history(str(tmp_path))
        assert records[0]["timestamp"] == "2026-02-01T09:00:00"
        assert records[1]["timestamp"] == "2026-03-01T09:00:00"

    @pytest.mark.unit
    def test_empty_directory_returns_empty_list(self, tmp_path: Any) -> None:
        """Scenario: No scan files produces an empty list."""
        records = load_history(str(tmp_path))
        assert records == []

    @pytest.mark.unit
    def test_missing_directory_returns_empty_list(self, tmp_path: Any) -> None:
        """Scenario: A non-existent history dir returns an empty list."""
        absent = str(tmp_path / "no-such-dir")
        assert load_history(absent) == []

    @pytest.mark.unit
    def test_files_scanned_count_preserved(self, tmp_path: Any) -> None:
        """Scenario: The files_scanned count survives a save/load cycle."""
        dt = datetime(2026, 3, 5, 12, 0, 0)
        scores = [
            {"path": "a.md", "score": 1.0, "word_count": 100},
            {"path": "b.md", "score": 2.0, "word_count": 200},
            {"path": "c.md", "score": 0.5, "word_count": 50},
        ]
        record = build_record(dt, scores, total_markers=15)
        save_record(record, str(tmp_path), dt)

        loaded = load_history(str(tmp_path))
        assert loaded[0]["files_scanned"] == 3
