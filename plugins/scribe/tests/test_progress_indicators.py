"""Contract tests for progress indicators in the reporting module (Issue #135).

Progress output is produced by the model following
`skills/slop-detector/modules/reporting.md` (Part 1). These tests pin
the line formats, mode rules, and score labels that document states.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPORTING_MODULE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "slop-detector"
    / "modules"
    / "reporting.md"
)


@pytest.fixture(scope="module")
def progress_part() -> str:
    text = REPORTING_MODULE.read_text(encoding="utf-8")
    start = text.index("## Part 1: Progress Indicators")
    return text[start : text.index("## Part 2: Historical Metrics")]


@pytest.mark.unit
class TestProgressLineFormat:
    def test_default_line_template(self, progress_part: str) -> None:
        assert "[{current}/{total}] Scanning {filepath}..." in progress_part

    def test_completion_summary_template_rounds_to_one_decimal(
        self, progress_part: str
    ) -> None:
        assert "Scanned {total} files in {elapsed:.1f}s" in progress_part

    def test_counter_is_one_based(self, progress_part: str) -> None:
        assert "Use 1-based indexing in the counter" in progress_part

    def test_unreadable_file_prints_a_warning_and_the_scan_continues(
        self, progress_part: str
    ) -> None:
        assert "... WARNING: could not read file" in progress_part
        assert "Do not abort the scan on a single unreadable file." in progress_part


@pytest.mark.unit
class TestModes:
    def test_quiet_mode_prints_no_per_file_lines_or_summary(
        self, progress_part: str
    ) -> None:
        quiet = progress_part.split("#### Quiet Mode")[1].split("####")[0]
        assert "No per-file lines. No summary line." in quiet

    def test_verbose_line_carries_score_and_label(self, progress_part: str) -> None:
        verbose = progress_part.split("#### Verbose Mode")[1]
        assert re.search(r"\[1/49\] Scanning \S+\.\.\. score=2\.1 \(Light\)", verbose)


@pytest.mark.unit
class TestScoreLabels:
    def test_label_bands_are_clean_light_moderate_heavy(
        self, progress_part: str
    ) -> None:
        bands = re.findall(r"^\| ([\d.+ -]+) \| (\w+) \|$", progress_part, re.MULTILINE)
        assert [(band.replace(" ", ""), label) for band, label in bands] == [
            ("0-1.0", "Clean"),
            ("1.0-2.5", "Light"),
            ("2.5-5.0", "Moderate"),
            ("5.0+", "Heavy"),
        ]

    def test_verbose_examples_use_the_labels_for_their_scores(
        self, progress_part: str
    ) -> None:
        assert "score=2.1 (Light)" in progress_part
        assert "score=0.4 (Clean)" in progress_part


@pytest.mark.unit
class TestProgressThreshold:
    def test_files_below_three_show_no_progress(self, progress_part: str) -> None:
        assert "| 1-2 | No progress output |" in progress_part

    def test_three_or_more_files_show_progress(self, progress_part: str) -> None:
        assert "| 3+ | Show file count progress |" in progress_part
