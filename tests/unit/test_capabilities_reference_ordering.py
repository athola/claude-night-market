"""Guard the alphabetical ordering the capabilities reference claims.

``book/src/reference/capabilities-reference.md`` heads its tables
"(Alphabetical)". That heading is a promise to the reader: it is the
reason a person scans for a row instead of searching for it. When rows
are appended in place rather than inserted in order, the promise
quietly stops holding and the table becomes slower to read than an
unsorted one, because scanning fails in a way searching would not.

#536 reported one misplaced row. A single-row fix would have left the
other ten, and nothing would have stopped the eleventh. This asserts
the property the heading claims.

Following BDD principles with Given/When/Then scenarios.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REFERENCE = (
    Path(__file__).resolve().parents[2]
    / "book"
    / "src"
    / "reference"
    / "capabilities-reference.md"
)

# A table row whose first cell is a backticked identifier.
_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def _sorted_sections() -> list[tuple[int, list[tuple[int, str]]]]:
    """Return contiguous runs of identifier rows, with line numbers.

    A run ends at any line that is not such a row, which is what
    separates one table (and its heading and separator rows) from the
    next.
    """
    sections: list[tuple[int, list[tuple[int, str]]]] = []
    current: list[tuple[int, str]] = []
    start = 0
    for lineno, line in enumerate(REFERENCE.read_text().split("\n"), 1):
        match = _ROW.match(line)
        if match:
            if not current:
                start = lineno
            current.append((lineno, match.group(1)))
            continue
        if current:
            sections.append((start, current))
            current = []
    if current:
        sections.append((start, current))
    return sections


class TestCapabilitiesReferenceOrdering:
    """Feature: the reference is ordered the way it says it is.

    As a reader scanning for a capability
    I want the alphabetical tables to actually be alphabetical
    So that not finding a row means it is absent, not misfiled
    """

    @pytest.mark.unit
    def test_reference_file_exists(self) -> None:
        """Given the book, the capabilities reference is present."""
        assert REFERENCE.exists()

    @pytest.mark.unit
    def test_every_table_section_is_alphabetical(self) -> None:
        """Scenario: no row sits before a row that sorts above it.

        Given each contiguous run of rows in the reference
        When comparing each row's identifier to the one before it
        Then the sequence is non-decreasing
        """
        violations: list[str] = []
        for _start, rows in _sorted_sections():
            for (_, previous), (lineno, name) in zip(rows, rows[1:]):
                if name < previous:
                    violations.append(f"line {lineno}: {previous!r} then {name!r}")
        assert violations == [], "rows out of alphabetical order:\n" + "\n".join(
            violations
        )

    @pytest.mark.unit
    def test_sections_were_actually_found(self) -> None:
        """Given the parser, it finds the tables it is meant to guard.

        Without this, a change to the table markup would empty the
        section list and the ordering test above would pass vacuously.
        """
        sections = _sorted_sections()
        assert len(sections) >= 3
        assert sum(len(rows) for _, rows in sections) > 300
