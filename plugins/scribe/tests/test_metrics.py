"""Contract tests for historical metrics in the reporting module (Issue #139).

`--track` and `--history` are performed by the model following
`skills/slop-detector/modules/reporting.md` (Part 2). These tests pin
the storage path, file naming, record schema, and regression rule that
document states.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

REPORTING_MODULE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "slop-detector"
    / "modules"
    / "reporting.md"
)


@pytest.fixture(scope="module")
def metrics_part() -> str:
    text = REPORTING_MODULE.read_text(encoding="utf-8")
    return text[text.index("## Part 2: Historical Metrics") :]


@pytest.fixture(scope="module")
def record_example(metrics_part: str) -> dict[str, Any]:
    block = re.search(r"```json\n(.*?)\n```", metrics_part, re.DOTALL)
    assert block, "reporting.md Part 2 has no ```json record example"
    return json.loads(block.group(1))


@pytest.mark.unit
class TestFileNaming:
    def test_history_lives_in_a_slop_history_directory(self, metrics_part: str) -> None:
        assert "Write scan records to `.slop-history/` at the repo root" in metrics_part

    def test_scan_filename_template_matches_the_strftime_it_documents(
        self, metrics_part: str
    ) -> None:
        assert ".slop-history/scan-YYYY-MM-DD-HHMMSS.json" in metrics_part
        assert 'strftime("%Y-%m-%d-%H%M%S")' in metrics_part
        stamp = datetime(2026, 3, 1, 14, 30, 22).strftime("%Y-%m-%d-%H%M%S")
        assert f".slop-history/scan-{stamp}.json" in metrics_part


@pytest.mark.unit
class TestRecordSchema:
    def test_record_has_the_four_documented_top_level_keys(
        self, record_example: dict[str, Any]
    ) -> None:
        assert set(record_example) == {
            "timestamp",
            "files_scanned",
            "scores",
            "summary",
        }

    def test_timestamp_in_the_example_is_iso_format(
        self, record_example: dict[str, Any]
    ) -> None:
        assert datetime.fromisoformat(record_example["timestamp"])

    def test_score_entries_carry_path_score_and_word_count(
        self, record_example: dict[str, Any]
    ) -> None:
        assert set(record_example["scores"][0]) == {"path", "score", "word_count"}

    def test_summary_carries_average_maximum_and_marker_total(
        self, record_example: dict[str, Any]
    ) -> None:
        assert set(record_example["summary"]) == {
            "avg_score",
            "max_score",
            "total_markers",
        }

    def test_empty_scan_summarizes_to_zero_scores(self, metrics_part: str) -> None:
        assert "mean of all scores (0.0 if no files)" in metrics_part
        assert "maximum score (0.0 if no files)" in metrics_part


@pytest.mark.unit
class TestTrendAndRegression:
    def test_history_is_read_in_filename_order(self, metrics_part: str) -> None:
        assert "sorted by\nfilename (chronological order)" in metrics_part

    def test_first_history_row_shows_a_dash_for_delta(self, metrics_part: str) -> None:
        assert "Use `—` for the delta on the first row." in metrics_part

    def test_positive_deltas_are_prefixed_with_a_plus(self, metrics_part: str) -> None:
        assert "Prefix positive deltas with `+`." in metrics_part

    def test_regression_threshold_is_an_increase_above_half_a_point(
        self, metrics_part: str
    ) -> None:
        assert "`avg_score` increased by more than 0.5" in metrics_part

    def test_regression_warning_example_states_both_scores(
        self, metrics_part: str
    ) -> None:
        warning = re.search(
            r"WARNING: avg score increased by ([\d.]+) since last scan "
            r"\(([\d.]+) -> ([\d.]+)\)",
            metrics_part,
        )
        assert warning
        delta, before, after = (float(group) for group in warning.groups())
        assert round(after - before, 2) == delta
        assert delta > 0.5

    def test_tracking_checks_for_regression_before_writing_the_new_record(
        self, metrics_part: str
    ) -> None:
        assert "Compare the new avg against the most recent existing record" in (
            metrics_part.replace("\n", " ")
        )
