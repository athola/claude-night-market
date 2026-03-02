"""Tests for progress indicator formatting and logic.

Issue #135: CLI progress indicators for large file scans

Tests verify the progress line formats, mode logic, and threshold behavior
described in modules/progress-indicators.md. No file I/O is performed.
"""

import pytest

# ---------------------------------------------------------------------------
# Helpers that mirror the logic described in the module
# ---------------------------------------------------------------------------


def format_progress_line(current: int, total: int, filepath: str) -> str:
    """Return a default-mode progress line."""
    return f"[{current}/{total}] Scanning {filepath}..."


def format_progress_line_verbose(
    current: int, total: int, filepath: str, score: float
) -> str:
    """Return a verbose-mode progress line with score label."""
    label = score_label(score)
    return f"[{current}/{total}] Scanning {filepath}... score={score:.1f} ({label})"


def format_summary(total: int, elapsed: float) -> str:
    """Return the completion summary line."""
    return f"Scanned {total} files in {elapsed:.1f}s"


def format_warning_line(current: int, total: int, filepath: str) -> str:
    """Return a progress line for an unreadable file."""
    return f"[{current}/{total}] Scanning {filepath}... WARNING: could not read file"


def score_label(score: float) -> str:
    """Map a slop score to its human-readable label."""
    if score < 1.0:
        return "Clean"
    if score < 2.5:
        return "Light"
    if score < 5.0:
        return "Moderate"
    return "Heavy"


def should_show_progress(file_count: int) -> bool:
    """Return True when the file count warrants progress output."""
    return file_count >= 3


# ---------------------------------------------------------------------------
# Tests: progress line formatting
# ---------------------------------------------------------------------------


class TestProgressLineFormat:
    """Feature: Default-mode progress line formatting.

    As a user scanning many files
    I want to see a counter for each file
    So that I can track scan progress.
    """

    @pytest.mark.unit
    def test_basic_format(self) -> None:
        """Scenario: Format a basic progress line.

        Given file 12 of 49 is being scanned
        When formatting the progress line
        Then it matches the expected pattern.
        """
        line = format_progress_line(12, 49, "plugins/scribe/README.md")
        assert line == "[12/49] Scanning plugins/scribe/README.md..."

    @pytest.mark.unit
    def test_first_file(self) -> None:
        """Scenario: First file uses 1-based index."""
        line = format_progress_line(1, 10, "docs/intro.md")
        assert line.startswith("[1/10]")

    @pytest.mark.unit
    def test_last_file(self) -> None:
        """Scenario: Last file counter matches total."""
        line = format_progress_line(49, 49, "plugins/abstract/README.md")
        assert line.startswith("[49/49]")

    @pytest.mark.unit
    def test_filepath_included(self) -> None:
        """Scenario: The filepath appears in the progress line."""
        path = "plugins/scribe/skills/slop-detector/SKILL.md"
        line = format_progress_line(3, 5, path)
        assert path in line

    @pytest.mark.unit
    def test_ends_with_ellipsis(self) -> None:
        """Scenario: Progress line ends with '...'."""
        line = format_progress_line(1, 5, "README.md")
        assert line.endswith("...")


# ---------------------------------------------------------------------------
# Tests: summary line formatting
# ---------------------------------------------------------------------------


class TestSummaryFormat:
    """Feature: Completion summary line formatting."""

    @pytest.mark.unit
    def test_summary_format(self) -> None:
        """Scenario: Summary shows file count and elapsed time."""
        line = format_summary(49, 3.2)
        assert line == "Scanned 49 files in 3.2s"

    @pytest.mark.unit
    def test_summary_rounds_to_one_decimal(self) -> None:
        """Scenario: Elapsed time is rounded to one decimal place."""
        line = format_summary(10, 1.567)
        assert "1.6s" in line

    @pytest.mark.unit
    def test_summary_single_file(self) -> None:
        """Scenario: Summary works for small counts."""
        line = format_summary(1, 0.4)
        assert "1 files" in line


# ---------------------------------------------------------------------------
# Tests: quiet mode
# ---------------------------------------------------------------------------


class TestQuietMode:
    """Feature: Quiet mode suppresses progress output.

    As a CI pipeline
    I want no per-file progress lines in logs
    So that only the final report appears.
    """

    @pytest.mark.unit
    def test_quiet_produces_no_lines(self) -> None:
        """Scenario: Quiet mode collects no progress lines."""
        quiet = True
        lines = []
        files = ["a.md", "b.md", "c.md"]
        for i, f in enumerate(files, 1):
            if not quiet:
                lines.append(format_progress_line(i, len(files), f))
        assert lines == []

    @pytest.mark.unit
    def test_non_quiet_produces_lines(self) -> None:
        """Scenario: Default mode collects one line per file."""
        quiet = False
        lines = []
        files = ["a.md", "b.md", "c.md"]
        for i, f in enumerate(files, 1):
            if not quiet:
                lines.append(format_progress_line(i, len(files), f))
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# Tests: verbose mode
# ---------------------------------------------------------------------------


class TestVerboseMode:
    """Feature: Verbose mode shows per-file scores.

    As a developer
    I want to see each file's slop score during the scan
    So that I can spot problematic files immediately.
    """

    @pytest.mark.unit
    def test_verbose_line_includes_score(self) -> None:
        """Scenario: Verbose line includes score and label."""
        line = format_progress_line_verbose(1, 5, "README.md", 2.1)
        assert "score=2.1" in line
        assert "(Light)" in line

    @pytest.mark.unit
    def test_verbose_clean_label(self) -> None:
        """Scenario: Score below 1.0 shows 'Clean' label."""
        line = format_progress_line_verbose(1, 5, "README.md", 0.4)
        assert "(Clean)" in line

    @pytest.mark.unit
    def test_verbose_moderate_label(self) -> None:
        """Scenario: Score between 2.5 and 5.0 shows 'Moderate' label."""
        line = format_progress_line_verbose(2, 5, "guide.md", 3.7)
        assert "(Moderate)" in line

    @pytest.mark.unit
    def test_verbose_heavy_label(self) -> None:
        """Scenario: Score at or above 5.0 shows 'Heavy' label."""
        line = format_progress_line_verbose(3, 5, "draft.md", 6.0)
        assert "(Heavy)" in line

    @pytest.mark.unit
    def test_verbose_line_still_has_counter(self) -> None:
        """Scenario: Verbose line retains the [current/total] counter."""
        line = format_progress_line_verbose(7, 20, "docs/api.md", 1.2)
        assert line.startswith("[7/20]")


# ---------------------------------------------------------------------------
# Tests: score label mapping
# ---------------------------------------------------------------------------


class TestScoreLabels:
    """Feature: Score-to-label mapping."""

    @pytest.mark.unit
    def test_boundary_clean_light(self) -> None:
        """Scenario: Score of exactly 1.0 is 'Light', not 'Clean'."""
        assert score_label(1.0) == "Light"

    @pytest.mark.unit
    def test_boundary_light_moderate(self) -> None:
        """Scenario: Score of exactly 2.5 is 'Moderate'."""
        assert score_label(2.5) == "Moderate"

    @pytest.mark.unit
    def test_boundary_moderate_heavy(self) -> None:
        """Scenario: Score of exactly 5.0 is 'Heavy'."""
        assert score_label(5.0) == "Heavy"

    @pytest.mark.unit
    def test_zero_score_is_clean(self) -> None:
        """Scenario: Score of 0.0 is 'Clean'."""
        assert score_label(0.0) == "Clean"


# ---------------------------------------------------------------------------
# Tests: threshold logic (skip progress for < 3 files)
# ---------------------------------------------------------------------------


class TestProgressThreshold:
    """Feature: Skip progress output for small file counts.

    As a user scanning one or two files
    I want no progress noise
    So that output stays clean for the single-file case.
    """

    @pytest.mark.unit
    def test_one_file_no_progress(self) -> None:
        """Scenario: Single file does not trigger progress display."""
        assert should_show_progress(1) is False

    @pytest.mark.unit
    def test_two_files_no_progress(self) -> None:
        """Scenario: Two files do not trigger progress display."""
        assert should_show_progress(2) is False

    @pytest.mark.unit
    def test_three_files_shows_progress(self) -> None:
        """Scenario: Three files is the minimum that triggers progress."""
        assert should_show_progress(3) is True

    @pytest.mark.unit
    def test_large_count_shows_progress(self) -> None:
        """Scenario: Large file counts always show progress."""
        assert should_show_progress(100) is True


# ---------------------------------------------------------------------------
# Tests: warning line for unreadable files
# ---------------------------------------------------------------------------


class TestWarningLine:
    """Feature: Unreadable files produce a warning line, not a failure."""

    @pytest.mark.unit
    def test_warning_line_format(self) -> None:
        """Scenario: Warning line contains the expected text."""
        line = format_warning_line(7, 49, "locked/file.md")
        assert "[7/49]" in line
        assert "locked/file.md" in line
        assert "WARNING: could not read file" in line

    @pytest.mark.unit
    def test_warning_line_still_has_counter(self) -> None:
        """Scenario: Warning line keeps the counter prefix."""
        line = format_warning_line(1, 3, "missing.md")
        assert line.startswith("[1/3]")
