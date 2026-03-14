#!/usr/bin/env python3
"""Tests for detect_duplicates.py duplicate detection functions."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Load the detect_duplicates module dynamically (same pattern as siblings)
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "detect_duplicates_module", scripts_dir / "detect_duplicates.py"
)
assert spec is not None
assert spec.loader is not None
detect_duplicates_module = importlib.util.module_from_spec(spec)
sys.modules["detect_duplicates_module"] = detect_duplicates_module
spec.loader.exec_module(detect_duplicates_module)

extract_blocks = detect_duplicates_module.extract_blocks
normalize_line = detect_duplicates_module.normalize_line
hash_block = detect_duplicates_module.hash_block
get_language = detect_duplicates_module.get_language
find_duplicates = detect_duplicates_module.find_duplicates
find_similar_functions = detect_duplicates_module.find_similar_functions
format_text = detect_duplicates_module.format_text
format_json = detect_duplicates_module.format_json
DuplicateBlock = detect_duplicates_module.DuplicateBlock
DuplicateReport = detect_duplicates_module.DuplicateReport


class TestExtractBlocks:
    """Feature: extract_blocks extracts sliding-window code blocks.

    As a duplicate detector
    I want to extract overlapping code blocks from source files
    So that I can hash them and find duplicates.
    """

    @pytest.mark.unit
    def test_returns_empty_when_file_too_short(self, tmp_path: Path) -> None:
        """Scenario: File with fewer lines than min_lines yields no blocks."""
        short_file = tmp_path / "short.py"
        short_file.write_text("x = 1\ny = 2\n")

        result = extract_blocks(short_file, min_lines=5)

        assert result == []

    @pytest.mark.unit
    def test_returns_blocks_from_file(self, tmp_path: Path) -> None:
        """Scenario: File with enough lines produces sliding-window blocks."""
        lines = [f"line_{i} = {i}" for i in range(10)]
        src = tmp_path / "example.py"
        src.write_text("\n".join(lines))

        result = extract_blocks(src, min_lines=5)

        assert len(result) > 0
        # Each block is (hash, start_line, end_line, content)
        for block_hash, start, end, _content in result:
            assert isinstance(block_hash, str)
            # Window covers min_lines lines: start..end inclusive = min_lines
            assert end - start + 1 == 5  # min_lines window
            assert start >= 1  # 1-indexed

    @pytest.mark.unit
    def test_content_parameter_skips_file_read(self, tmp_path: Path) -> None:
        """Scenario: Pre-supplied content avoids reading from disk.

        Given a filepath pointing to a non-existent file
        When content is provided as a parameter
        Then extract_blocks succeeds using the provided content.
        """
        fake_path = tmp_path / "does_not_exist.py"
        lines = [f"var_{i} = {i}" for i in range(8)]
        pre_read = "\n".join(lines)

        result = extract_blocks(fake_path, min_lines=5, content=pre_read)

        assert len(result) > 0

    @pytest.mark.unit
    def test_content_parameter_matches_file_read(self, tmp_path: Path) -> None:
        """Scenario: Results match whether content comes from file or param."""
        lines = [f"data_{i} = {i * 10}" for i in range(7)]
        text = "\n".join(lines)
        src = tmp_path / "sample.py"
        src.write_text(text)

        from_file = extract_blocks(src, min_lines=5)
        from_param = extract_blocks(src, min_lines=5, content=text)

        assert from_file == from_param

    @pytest.mark.unit
    def test_returns_empty_for_unreadable_file(self, tmp_path: Path) -> None:
        """Scenario: Non-existent file without content param returns empty."""
        missing = tmp_path / "missing.py"

        result = extract_blocks(missing, min_lines=5)

        assert result == []

    @pytest.mark.unit
    def test_skips_mostly_empty_blocks(self, tmp_path: Path) -> None:
        """Scenario: Blocks with >40% blank lines are skipped."""
        # 5-line block with 3 blanks → 60% empty → skipped
        lines = ["code = 1", "", "", "", "code = 2", "code = 3", "code = 4"]
        src = tmp_path / "sparse.py"
        src.write_text("\n".join(lines))

        result = extract_blocks(src, min_lines=5)

        # The first window (lines 1-5) has only 2 non-empty out of 5 (40%)
        # which is below the 60% threshold, so it should be skipped
        for _, _start, _end, block_content in result:
            block_lines = block_content.splitlines()
            non_empty = [ln for ln in block_lines if ln.strip()]
            assert len(non_empty) >= 5 * 0.6


class TestNormalizeLine:
    """Feature: normalize_line strips comments and normalizes whitespace."""

    @pytest.mark.unit
    def test_strips_python_comment(self) -> None:
        """Scenario: Python inline comment is removed."""
        assert normalize_line("x = 1  # set x", "python") == "x = 1"

    @pytest.mark.unit
    def test_normalizes_whitespace(self) -> None:
        """Scenario: Extra whitespace is collapsed."""
        assert normalize_line("  x  =   1  ", "python") == "x = 1"

    @pytest.mark.unit
    def test_strips_js_comment(self) -> None:
        """Scenario: JavaScript // comment is removed."""
        assert normalize_line("let x = 1; // init", "javascript") == "let x = 1;"


class TestGetLanguage:
    """Feature: get_language maps file extensions to language names."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "suffix, expected",
        [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".go", "go"),
            (".rs", "rust"),
            (".xyz", "unknown"),
        ],
    )
    def test_extension_mapping(self, suffix: str, expected: str) -> None:
        """Scenario: Known extensions map to correct language."""
        assert get_language(Path(f"file{suffix}")) == expected


class TestHashBlock:
    """Feature: hash_block creates normalized hashes for code blocks."""

    @pytest.mark.unit
    def test_identical_content_same_hash(self) -> None:
        """Scenario: Same code produces identical hash."""
        lines = ["x = 1", "y = 2", "z = 3"]
        h1 = hash_block(lines, "python")
        h2 = hash_block(lines, "python")
        assert h1 == h2

    @pytest.mark.unit
    def test_comment_differences_ignored(self) -> None:
        """Scenario: Lines differing only by comments produce same hash."""
        lines_a = ["x = 1  # first", "y = 2"]
        lines_b = ["x = 1  # second", "y = 2"]
        assert hash_block(lines_a, "python") == hash_block(lines_b, "python")


def _write_py_file(directory: Path, name: str, lines: list[str]) -> Path:
    """Helper: write a .py file with given lines."""
    f = directory / name
    f.write_text("\n".join(lines) + "\n")
    return f


# Shared block used to create known duplicates across files.
_DUPLICATE_BLOCK = [
    "def process_data(items):",
    "    result = []",
    "    for item in items:",
    "        if item.is_valid():",
    "            result.append(item.transform())",
    "    return result",
]


class TestFindDuplicates:
    """Feature: find_duplicates detects repeated code across files.

    As a codebase maintainer
    I want to find duplicated code blocks across files
    So that I can refactor them into shared utilities.
    """

    @pytest.mark.unit
    def test_detects_identical_blocks_across_files(self, tmp_path: Path) -> None:
        """Scenario: Two files sharing an identical block are reported."""
        _write_py_file(tmp_path, "a.py", _DUPLICATE_BLOCK)
        _write_py_file(tmp_path, "b.py", _DUPLICATE_BLOCK)

        report = find_duplicates([tmp_path], min_lines=5)

        assert report.files_scanned == 2
        assert len(report.duplicates) >= 1
        assert report.duplicate_lines > 0

    @pytest.mark.unit
    def test_no_duplicates_in_unique_files(self, tmp_path: Path) -> None:
        """Scenario: Files with entirely different content produce no duplicates."""
        _write_py_file(
            tmp_path,
            "x.py",
            [f"x_{i} = {i}" for i in range(10)],
        )
        _write_py_file(
            tmp_path,
            "y.py",
            [f"y_{i} = {i * 100}" for i in range(10)],
        )

        report = find_duplicates([tmp_path], min_lines=5)

        assert report.duplicates == []
        assert report.duplicate_lines == 0

    @pytest.mark.unit
    def test_respects_min_lines_parameter(self, tmp_path: Path) -> None:
        """Scenario: Blocks shorter than min_lines are not flagged."""
        short_block = ["a = 1", "b = 2", "c = 3"]
        _write_py_file(tmp_path, "s1.py", short_block + ["d = 4"] * 5)
        _write_py_file(tmp_path, "s2.py", short_block + ["e = 5"] * 5)

        report = find_duplicates([tmp_path], min_lines=6)

        # The 3-line shared block is below the 6-line threshold
        dup_hashes = {d.normalized_hash for d in report.duplicates}
        short_hash = hash_block(short_block, "python")
        assert short_hash not in dup_hashes

    @pytest.mark.unit
    def test_filters_by_extension(self, tmp_path: Path) -> None:
        """Scenario: Only files matching extensions are scanned."""
        _write_py_file(tmp_path, "code.py", _DUPLICATE_BLOCK)
        txt = tmp_path / "code.txt"
        txt.write_text("\n".join(_DUPLICATE_BLOCK) + "\n")

        report = find_duplicates([tmp_path], min_lines=5, extensions={".py"})

        assert report.files_scanned == 1

    @pytest.mark.unit
    def test_excludes_venv_directories(self, tmp_path: Path) -> None:
        """Scenario: Files inside .venv are excluded from scanning."""
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        _write_py_file(venv_dir, "hidden.py", _DUPLICATE_BLOCK)
        _write_py_file(tmp_path, "visible.py", _DUPLICATE_BLOCK)

        report = find_duplicates([tmp_path], min_lines=5)

        # Only the non-venv file should be scanned
        assert report.files_scanned == 1

    @pytest.mark.unit
    def test_report_duplication_percentage(self, tmp_path: Path) -> None:
        """Scenario: Duplication percentage is calculated correctly."""
        _write_py_file(tmp_path, "dup1.py", _DUPLICATE_BLOCK)
        _write_py_file(tmp_path, "dup2.py", _DUPLICATE_BLOCK)

        report = find_duplicates([tmp_path], min_lines=5)

        assert report.duplication_percentage >= 0.0
        assert report.total_lines > 0


class TestFindSimilarFunctions:
    """Feature: find_similar_functions groups similar function names.

    As a developer
    I want to find functions with similar names
    So that I can identify candidates for abstraction.
    """

    @pytest.mark.unit
    def test_groups_suffixed_variants(self, tmp_path: Path) -> None:
        """Scenario: Functions differing only by _v2 suffix are grouped."""
        code = "def process_data():\n    pass\n\ndef process_data_v2():\n    pass\n"
        (tmp_path / "funcs.py").write_text(code)

        groups = find_similar_functions(tmp_path)

        base_names = [base for base, _ in groups]
        assert "process_data" in base_names

    @pytest.mark.unit
    def test_no_groups_for_unique_names(self, tmp_path: Path) -> None:
        """Scenario: Unique function names produce no groups."""
        code = "def alpha():\n    pass\n\ndef beta():\n    pass\n"
        (tmp_path / "unique.py").write_text(code)

        groups = find_similar_functions(tmp_path)

        # alpha and beta share no common base after suffix stripping
        assert groups == []

    @pytest.mark.unit
    def test_excludes_venv(self, tmp_path: Path) -> None:
        """Scenario: Functions in .venv are ignored."""
        venv_dir = tmp_path / ".venv" / "pkg"
        venv_dir.mkdir(parents=True)
        (venv_dir / "mod.py").write_text(
            "def handler():\n    pass\n\ndef handler_v2():\n    pass\n"
        )

        groups = find_similar_functions(tmp_path)

        assert groups == []


class TestFormatText:
    """Feature: format_text renders a human-readable report."""

    @pytest.mark.unit
    def test_includes_summary_stats(self) -> None:
        """Scenario: Report header contains scan statistics."""
        report = DuplicateReport(
            duplicates=[],
            files_scanned=10,
            total_lines=500,
            duplicate_lines=0,
        )

        output = format_text(report, [])

        assert "Files scanned: 10" in output
        assert "Total lines: 500" in output
        assert "0.0%" in output

    @pytest.mark.unit
    def test_shows_duplicate_block_details(self) -> None:
        """Scenario: Duplicate blocks are listed with locations."""
        dup = DuplicateBlock(
            content="x = 1\ny = 2\nz = 3\na = 4\nb = 5",
            locations=[("a.py", 1, 5), ("b.py", 1, 5)],
            line_count=5,
            normalized_hash="abc123",
        )
        report = DuplicateReport(
            duplicates=[dup],
            files_scanned=2,
            total_lines=10,
            duplicate_lines=5,
        )

        output = format_text(report, [])

        assert "2 occurrences" in output
        assert "a.py" in output
        assert "b.py" in output

    @pytest.mark.unit
    def test_shows_similar_function_groups(self) -> None:
        """Scenario: Similar function names are listed."""
        groups = [("handle", ["handle", "handle_v2"])]
        report = DuplicateReport(
            duplicates=[],
            files_scanned=1,
            total_lines=50,
            duplicate_lines=0,
        )

        output = format_text(report, groups)

        assert "SIMILAR FUNCTION NAMES" in output
        assert "handle" in output

    @pytest.mark.unit
    def test_high_duplication_recommendation(self) -> None:
        """Scenario: High duplication triggers extraction recommendation."""
        report = DuplicateReport(
            duplicates=[],
            files_scanned=5,
            total_lines=100,
            duplicate_lines=20,
        )

        output = format_text(report, [])

        assert "HIGH" in output


class TestFormatJson:
    """Feature: format_json renders a machine-readable report."""

    @pytest.mark.unit
    def test_returns_valid_json(self) -> None:
        """Scenario: Output parses as valid JSON."""
        report = DuplicateReport(
            duplicates=[],
            files_scanned=3,
            total_lines=100,
            duplicate_lines=0,
        )

        raw = format_json(report, [])
        data = json.loads(raw)

        assert data["summary"]["files_scanned"] == 3
        assert data["summary"]["total_lines"] == 100
        assert data["duplicates"] == []
        assert data["similar_functions"] == []

    @pytest.mark.unit
    def test_includes_duplicate_locations(self) -> None:
        """Scenario: Duplicate locations appear in JSON output."""
        dup = DuplicateBlock(
            content="code",
            locations=[("f1.py", 1, 5), ("f2.py", 10, 14)],
            line_count=5,
            normalized_hash="deadbeef",
        )
        report = DuplicateReport(
            duplicates=[dup],
            files_scanned=2,
            total_lines=30,
            duplicate_lines=5,
        )

        raw = format_json(report, [])
        data = json.loads(raw)

        assert len(data["duplicates"]) == 1
        locs = data["duplicates"][0]["locations"]
        assert locs[0]["file"] == "f1.py"
        assert locs[1]["start"] == 10


class TestDuplicateReportProperties:
    """Feature: DuplicateReport computed properties."""

    @pytest.mark.unit
    def test_zero_lines_gives_zero_percentage(self) -> None:
        """Scenario: Empty report has 0% duplication."""
        report = DuplicateReport(
            duplicates=[],
            files_scanned=0,
            total_lines=0,
            duplicate_lines=0,
        )

        assert report.duplication_percentage == 0.0

    @pytest.mark.unit
    def test_occurrence_count(self) -> None:
        """Scenario: DuplicateBlock.occurrence_count matches location count."""
        dup = DuplicateBlock(
            content="x",
            locations=[("a.py", 1, 5), ("b.py", 1, 5), ("c.py", 1, 5)],
            line_count=5,
            normalized_hash="abc",
        )

        assert dup.occurrence_count == 3
