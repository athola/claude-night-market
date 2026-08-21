"""Tests for the in-place correction of fabricated duration readings (#671).

``skill_execution_logger`` wrote ``duration_ms: 0`` whenever it could not
find the matching pre-execution state, and stored negative intervals when
the wall clock moved backward between the two hooks. Both are numbers no
clock produced, and both pass the ``>= 0``/``is not None`` filters the
report uses, so they count as timing samples.

The producer no longer emits either. Entries already on disk still carry
them, and the two ``invocation_id`` shapes tell the fabricated zeros apart
from real sub-millisecond readings: the pre hook writes
``plugin:skill:timestamp`` when it found the state, a bare ``uuid4`` when
it did not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from correct_fabricated_durations import (  # noqa: E402 - import after sys.path setup
    correct_entry,
    correct_file,
)

PAIRED = "abstract:skill-auditor:1786591624.0"
UNPAIRED = "3f2a1b4c-5d6e-4f70-8a91-b2c3d4e5f607"


def _entry(invocation_id: str, duration_ms: int | None) -> dict:
    return {
        "timestamp": "2026-08-03T04:21:03.239907+00:00",
        "invocation_id": invocation_id,
        "skill": "abstract:skill-auditor",
        "plugin": "abstract",
        "skill_name": "skill-auditor",
        "duration_ms": duration_ms,
        "outcome": "success",
        "context": {"session_id": "s1", "tool_input": {"skill": "abstract:x"}},
    }


class TestCorrectEntry:
    """The decision of which readings were never measured."""

    def test_unpaired_zero_becomes_none(self) -> None:
        """A zero on an unpaired entry is the logger's fallback, not a reading."""
        corrected = correct_entry(_entry(UNPAIRED, 0))
        assert corrected is not None
        assert corrected["duration_ms"] is None

    def test_paired_zero_is_left_alone(self) -> None:
        """A zero on a paired entry could be a real sub-millisecond reading.

        This is the precision half of the correction. The fallback and a
        genuine fast execution both store 0; only the invocation_id shape
        separates them, so a paired zero must survive untouched.
        """
        assert correct_entry(_entry(PAIRED, 0)) is None

    def test_negative_becomes_none(self) -> None:
        """No execution takes negative time, however the entry was paired."""
        corrected = correct_entry(_entry(PAIRED, -2375))
        assert corrected is not None
        assert corrected["duration_ms"] is None

    def test_ordinary_reading_is_untouched(self) -> None:
        """A positive measurement is left exactly as recorded."""
        assert correct_entry(_entry(PAIRED, 126)) is None

    def test_already_none_is_untouched(self) -> None:
        """An entry the fixed producer wrote needs no second pass."""
        assert correct_entry(_entry(UNPAIRED, None)) is None

    def test_unpaired_positive_is_untouched(self) -> None:
        """Only the zero is fabricated; an unpaired positive is still a reading."""
        assert correct_entry(_entry(UNPAIRED, 140)) is None


class TestCorrectFile:
    """Rewriting a log file without disturbing anything else."""

    def _write(self, path: Path, entries: list[dict]) -> None:
        path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    def test_dry_run_reports_without_writing(self, tmp_path: Path) -> None:
        """Counting the damage must never be what changes it."""
        log = tmp_path / "2026-08-03.jsonl"
        self._write(log, [_entry(UNPAIRED, 0), _entry(PAIRED, 126)])
        before = log.read_text()

        stats = correct_file(log, apply=False)

        assert stats.corrected == 1
        assert log.read_text() == before, "dry run modified the file"

    def test_apply_corrects_only_the_fabricated_rows(self, tmp_path: Path) -> None:
        """Every other row survives byte-for-byte in its original order."""
        log = tmp_path / "2026-08-03.jsonl"
        rows = [
            _entry(PAIRED, 126),
            _entry(UNPAIRED, 0),
            _entry(PAIRED, -2375),
            _entry(PAIRED, 0),
        ]
        self._write(log, rows)

        stats = correct_file(log, apply=True)
        assert stats.corrected == 2

        out = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
        assert len(out) == len(rows)
        assert out[0]["duration_ms"] == 126
        assert out[1]["duration_ms"] is None
        assert out[2]["duration_ms"] is None
        assert out[3]["duration_ms"] == 0, "a paired zero was rewritten"

    def test_every_other_field_round_trips(self, tmp_path: Path) -> None:
        """Correction touches duration_ms and nothing else."""
        log = tmp_path / "2026-08-03.jsonl"
        original = _entry(UNPAIRED, 0)
        self._write(log, [original])

        correct_file(log, apply=True)

        out = json.loads(log.read_text().strip())
        assert out.pop("duration_ms") is None
        expected = dict(original)
        expected.pop("duration_ms")
        assert out == expected

    def test_malformed_line_is_preserved_not_dropped(self, tmp_path: Path) -> None:
        """A line this tool cannot parse is data it must not delete."""
        log = tmp_path / "2026-08-03.jsonl"
        log.write_text(json.dumps(_entry(UNPAIRED, 0)) + "\n{ not json\n")

        stats = correct_file(log, apply=True)

        assert stats.unparseable == 1
        lines = [x for x in log.read_text().splitlines() if x.strip()]
        assert len(lines) == 2
        assert lines[1] == "{ not json"

    def test_a_clean_file_is_not_rewritten(self, tmp_path: Path) -> None:
        """No corrections means the file is left completely alone."""
        log = tmp_path / "2026-08-03.jsonl"
        self._write(log, [_entry(PAIRED, 126)])
        mtime_before = log.stat().st_mtime_ns

        stats = correct_file(log, apply=True)

        assert stats.corrected == 0
        assert log.stat().st_mtime_ns == mtime_before, "clean file was rewritten"
