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

import pytest


_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from correct_fabricated_durations import (  # noqa: E402 - import after sys.path setup
    _atomic_write,
    backup_logs,
    correct_entry,
    correct_file,
    main,
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
        """A zero on an unpaired entry is the logger's fallback, not a reading.

        Given: an entry with a bare uuid4 invocation_id and duration_ms 0
        When: correct_entry inspects it
        Then: a corrected copy is returned, and its duration_ms is None
        """
        corrected = correct_entry(_entry(UNPAIRED, 0))
        assert corrected is not None
        assert corrected["duration_ms"] is None

    def test_paired_zero_is_left_alone(self) -> None:
        """A zero on a paired entry could be a real sub-millisecond reading.

        Given: an entry with a plugin:skill:timestamp id and duration_ms 0
        When: correct_entry inspects it
        Then: None is returned, meaning no correction is due

        This is the precision half of the correction. The fallback and a
        genuine fast execution both store 0, and only the invocation_id
        shape separates them, so a paired zero must survive untouched.
        """
        assert correct_entry(_entry(PAIRED, 0)) is None

    def test_negative_becomes_none(self) -> None:
        """No execution takes negative time, however the entry was paired.

        Given: a paired entry whose duration_ms is negative
        When: correct_entry inspects it
        Then: a corrected copy is returned, and its duration_ms is None
        """
        corrected = correct_entry(_entry(PAIRED, -2375))
        assert corrected is not None
        assert corrected["duration_ms"] is None

    def test_ordinary_reading_is_untouched(self) -> None:
        """A positive measurement is left exactly as recorded.

        Given: a paired entry with an ordinary positive duration_ms
        When: correct_entry inspects it
        Then: None is returned, and the reading stands unaltered
        """
        assert correct_entry(_entry(PAIRED, 126)) is None

    def test_already_none_is_untouched(self) -> None:
        """An entry the fixed producer wrote needs no second pass.

        Given: an entry whose duration_ms is already None
        When: correct_entry inspects it
        Then: None is returned, and the pass stays idempotent
        """
        assert correct_entry(_entry(UNPAIRED, None)) is None

    def test_unpaired_positive_is_untouched(self) -> None:
        """Only the zero is fabricated, and an unpaired positive still counts.

        Given: an unpaired entry with a positive duration_ms
        When: correct_entry inspects it
        Then: None is returned, because the interval was genuinely measured
        """
        assert correct_entry(_entry(UNPAIRED, 140)) is None


class TestCorrectFile:
    """Rewriting a log file without disturbing anything else."""

    def _write(self, path: Path, entries: list[dict]) -> None:
        path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    def test_dry_run_reports_without_writing(self, tmp_path: Path) -> None:
        """Counting the damage must never be what changes it.

        Given: a log holding one fabricated zero and one real reading
        When: correct_file scans it with apply False
        Then: the count reports one correction, and the bytes are unchanged
        """
        log = tmp_path / "2026-08-03.jsonl"
        self._write(log, [_entry(UNPAIRED, 0), _entry(PAIRED, 126)])
        before = log.read_text()

        stats = correct_file(log, apply=False)

        assert stats.corrected == 1
        assert log.read_text() == before, "dry run modified the file"

    def test_apply_corrects_only_the_fabricated_rows(self, tmp_path: Path) -> None:
        """Every other row survives byte-for-byte in its original order.

        Given: a log of four rows, two of them fabricated
        When: correct_file rewrites it with apply True
        Then: the two are nulled, and the real reading and paired zero stand
        """
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
        """Correction touches duration_ms and nothing else.

        Given: a fabricated entry carrying every other telemetry field
        When: correct_file rewrites it
        Then: duration_ms is None, and each remaining field round-trips
        """
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
        """A line this tool cannot parse is data it must not delete.

        Given: a log holding one fabricated entry and one unparseable line
        When: correct_file rewrites it
        Then: the bad line is counted, and it survives verbatim
        """
        log = tmp_path / "2026-08-03.jsonl"
        log.write_text(json.dumps(_entry(UNPAIRED, 0)) + "\n{ not json\n")

        stats = correct_file(log, apply=True)

        assert stats.unparseable == 1
        lines = [x for x in log.read_text().splitlines() if x.strip()]
        assert len(lines) == 2
        assert lines[1] == "{ not json"

    def test_a_clean_file_is_not_rewritten(self, tmp_path: Path) -> None:
        """No corrections means the file is left completely alone.

        Given: a log with nothing fabricated in it
        When: correct_file runs with apply True
        Then: zero corrections are reported, and the mtime does not move
        """
        log = tmp_path / "2026-08-03.jsonl"
        self._write(log, [_entry(PAIRED, 126)])
        mtime_before = log.stat().st_mtime_ns

        stats = correct_file(log, apply=True)

        assert stats.corrected == 0
        assert log.stat().st_mtime_ns == mtime_before, "clean file was rewritten"


class TestBackupLogs:
    """The copy taken before anything is rewritten."""

    def test_backup_copies_the_whole_tree(self, tmp_path: Path) -> None:
        """The backup reproduces the log tree in full.

        Given: a log tree with entries in nested skill directories
        When: backup_logs runs
        Then: a sibling directory exists, and its copy matches byte for byte
        """
        logs = tmp_path / "logs"
        nested = logs / "abstract" / "skill-auditor"
        nested.mkdir(parents=True)
        (nested / "2026-08-03.jsonl").write_text(json.dumps(_entry(UNPAIRED, 0)) + "\n")

        destination = backup_logs(logs)

        assert destination.exists()
        copied = destination / "abstract" / "skill-auditor" / "2026-08-03.jsonl"
        assert copied.read_text() == (nested / "2026-08-03.jsonl").read_text()

    def test_backup_replaces_a_stale_one(self, tmp_path: Path) -> None:
        """A previous backup is replaced, not merged into.

        Given: a backup directory left by an earlier run
        When: backup_logs runs again
        Then: the current file is present, and the stale one is gone

        A merged backup is worse than none: it would restore files the
        current tree no longer contains.
        """
        logs = tmp_path / "logs"
        logs.mkdir()
        (logs / "current.jsonl").write_text("{}\n")
        stale = tmp_path / "logs.pre-671-backup"
        stale.mkdir()
        (stale / "from-an-older-run.jsonl").write_text("{}\n")

        destination = backup_logs(logs)

        assert (destination / "current.jsonl").exists()
        assert not (destination / "from-an-older-run.jsonl").exists()

    def test_a_second_run_does_not_overwrite_the_original_backup(
        self, tmp_path: Path
    ) -> None:
        """The copy of the uncorrected logs survives a second --apply.

        Given: a backup taken before the first correction
        When:  backup_logs runs again, now over the corrected tree
        Then:  the first backup still holds the uncorrected values

        Replacing the destination in place makes the second run copy the
        already-corrected logs over the only record of what they said
        before, which is the one thing a backup is for.
        """
        logs = tmp_path / "logs"
        logs.mkdir()
        (logs / "run.jsonl").write_text('{"duration_ms": 0}\n')

        first = backup_logs(logs)
        (logs / "run.jsonl").write_text('{"duration_ms": null}\n')
        second = backup_logs(logs)

        assert first != second
        assert (first / "run.jsonl").read_text() == '{"duration_ms": 0}\n'
        assert (second / "run.jsonl").read_text() == '{"duration_ms": null}\n'


class TestAtomicWrite:
    """The rewrite must not leave a log half-written."""

    def test_failed_write_leaves_no_temp_file_behind(self, tmp_path: Path) -> None:
        """A failed write strands no temporary file.

        Given: a value that raises while the replacement text is built
        When: _atomic_write is called
        Then: the error propagates, the original stands, and no .tmp remains

        A stranded temp file would accumulate silently on every failure.
        """
        target = tmp_path / "2026-08-03.jsonl"
        target.write_text("original\n")

        class Exploding:
            def __str__(self) -> str:
                raise RuntimeError("boom")

        with pytest.raises((RuntimeError, TypeError)):
            _atomic_write(  # type: ignore[list-item] - a non-str is the point
                target, ["fine", Exploding()]
            )

        assert target.read_text() == "original\n"
        assert not list(tmp_path.glob("*.tmp")), "a temp file was stranded"


class TestBlankLines:
    """Formatting artifacts are not entries."""

    def test_blank_lines_are_skipped_and_not_counted(self, tmp_path: Path) -> None:
        """Blank padding is neither counted nor flagged.

        Given: a log padded with blank lines between entries
        When: correct_file scans it
        Then: only real entries are counted, and none is reported unparseable
        """
        log = tmp_path / "2026-08-03.jsonl"
        log.write_text(
            "\n"
            + json.dumps(_entry(PAIRED, 126))
            + "\n\n\n"
            + json.dumps(_entry(UNPAIRED, 0))
            + "\n\n"
        )

        stats = correct_file(log, apply=False)

        assert stats.entries == 2
        assert stats.unparseable == 0
        assert stats.corrected == 1


class TestCommandLine:
    """The entry point, including the safety of its default."""

    def _tree(self, tmp_path: Path, entries: list[dict]) -> Path:
        logs = tmp_path / "logs"
        nested = logs / "abstract" / "skill-auditor"
        nested.mkdir(parents=True)
        (nested / "2026-08-03.jsonl").write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        return logs

    @staticmethod
    def _rows(path: Path) -> list[dict]:
        return [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]

    def test_default_run_writes_nothing(self, tmp_path, monkeypatch, capsys) -> None:
        """The default run reports without touching the logs.

        Given: a log tree containing a fabricated zero
        When: the tool runs with no flags
        Then: it reports what it would correct and changes nothing on disk

        Reporting is the default precisely so that inspecting the damage
        can never be the thing that causes it.
        """
        logs = self._tree(tmp_path, [_entry(UNPAIRED, 0), _entry(PAIRED, 126)])
        log = logs / "abstract" / "skill-auditor" / "2026-08-03.jsonl"
        before = log.read_text()
        monkeypatch.setattr(sys, "argv", ["prog", "--log-dir", str(logs)])

        assert main() == 0

        assert "would correct 1" in capsys.readouterr().out
        assert log.read_text() == before
        assert not (tmp_path / "logs.pre-671-backup").exists()

    def test_apply_backs_up_before_rewriting(self, tmp_path, monkeypatch, capsys):
        """Applying corrections leaves the original recoverable.

        Given: a log tree containing a fabricated zero
        When: the tool runs with --apply
        Then: the entry is corrected and the pre-change tree is recoverable
        """
        logs = self._tree(tmp_path, [_entry(UNPAIRED, 0), _entry(PAIRED, 126)])
        monkeypatch.setattr(sys, "argv", ["prog", "--apply", "--log-dir", str(logs)])

        assert main() == 0

        assert "corrected 1" in capsys.readouterr().out
        rows = self._rows(logs / "abstract" / "skill-auditor" / "2026-08-03.jsonl")
        assert rows[0]["duration_ms"] is None
        assert rows[1]["duration_ms"] == 126

        backup = tmp_path / "logs.pre-671-backup"
        restored = self._rows(
            backup / "abstract" / "skill-auditor" / "2026-08-03.jsonl"
        )
        assert restored[0]["duration_ms"] == 0, "the backup lost the original value"

    def test_missing_log_directory_is_an_error(self, tmp_path, monkeypatch, capsys):
        """A missing log tree exits non-zero.

        Given: a log directory path that does not exist
        When: the tool runs
        Then: it returns 1, and says so on stderr rather than reporting clean

        Exiting 0 on a missing tree would read as "nothing to correct".
        """
        monkeypatch.setattr(sys, "argv", ["prog", "--log-dir", str(tmp_path / "gone")])

        assert main() == 1
        assert "no log directory" in capsys.readouterr().err

    def test_a_clean_tree_reports_zero_and_skips_the_advice(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """A clean tree reports zero and offers no advice.

        Given: a log tree with nothing fabricated in it
        When: the tool runs with no flags
        Then: it reports zero corrections and does not suggest --apply
        """
        logs = self._tree(tmp_path, [_entry(PAIRED, 126)])
        monkeypatch.setattr(sys, "argv", ["prog", "--log-dir", str(logs)])

        assert main() == 0

        out = capsys.readouterr().out
        assert "would correct 0" in out
        assert "--apply" not in out
