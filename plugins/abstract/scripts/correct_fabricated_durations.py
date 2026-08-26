#!/usr/bin/env python3
"""Correct duration readings that no clock produced (#671).

``skill_execution_logger`` used to write ``duration_ms: 0`` whenever it
could not find the matching pre-execution state, and to store the interval
whole when the wall clock moved backward between the two hooks. Both are
fabrications, and both survive the ``is not None``/``>= 0`` filters the
aggregate report applies, so each one counts as a timing sample and pulls
an average toward a number nothing measured.

The producer no longer emits either. Entries already written still carry
them. They can be found after the fact because the pre hook records
``invocation_id`` as ``plugin:skill:timestamp`` when it located the state
and as a bare ``uuid4`` when it did not, so a fabricated zero is
distinguishable from a genuine sub-millisecond reading.

What gets corrected, and nothing else:

* ``duration_ms == 0`` on an unpaired entry, which is the fallback
* ``duration_ms < 0`` on any entry, which is an impossible interval

A zero on a *paired* entry is left alone. It may be a real fast execution,
and this tool has no way to prove otherwise.

Usage::

    correct_fabricated_durations.py            # report only, writes nothing
    correct_fabricated_durations.py --apply    # rewrite, after a backup
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from abstract.utils import get_log_directory  # noqa: E402 - import after sys.path setup

# The pre hook's fallback id. Anything else means the state file was found.
_UUID4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass
class CorrectionStats:
    """Outcome of a single file pass."""

    path: Path
    entries: int = 0
    corrected: int = 0
    fabricated_zeros: int = 0
    negatives: int = 0
    unparseable: int = 0


def is_unpaired(entry: dict[str, Any]) -> bool:
    """Report whether the post hook failed to find this entry's pre-state."""
    return bool(_UUID4.match(str(entry.get("invocation_id") or "")))


def correct_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Return a corrected copy of ``entry``, or None when it is sound.

    Args:
        entry: One decoded telemetry record.

    Returns:
        A new entry with ``duration_ms`` set to None, or None to signal that
        the record needs no change.

    """
    duration = entry.get("duration_ms")
    if not isinstance(duration, int) or isinstance(duration, bool):
        return None

    if duration < 0 or (duration == 0 and is_unpaired(entry)):
        corrected = dict(entry)
        corrected["duration_ms"] = None
        return corrected
    return None


def correct_file(path: Path, *, apply: bool) -> CorrectionStats:
    """Scan one ``.jsonl`` log, optionally rewriting the fabricated rows.

    A line that does not parse is copied through untouched. It is data this
    tool does not understand, which is not a reason to drop it.

    The rewrite goes to a temporary file in the same directory and is moved
    into place, so an interrupted run leaves the original intact. A file
    with nothing to correct is not rewritten at all.

    Args:
        path: The log file to scan.
        apply: Rewrite the file when True; report only when False.

    Returns:
        Counts for this file.

    """
    stats = CorrectionStats(path=path)
    out_lines: list[str] = []

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            stats.unparseable += 1
            out_lines.append(raw)
            continue

        stats.entries += 1
        corrected = correct_entry(entry)
        if corrected is None:
            out_lines.append(raw)
            continue

        stats.corrected += 1
        if entry.get("duration_ms", 0) < 0:
            stats.negatives += 1
        else:
            stats.fabricated_zeros += 1
        out_lines.append(json.dumps(corrected))

    if apply and stats.corrected:
        _atomic_write(path, out_lines)
    return stats


def _atomic_write(path: Path, lines: list[str]) -> None:
    """Replace ``path`` with ``lines`` without a window of partial content."""
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def backup_logs(log_dir: Path) -> Path:
    """Copy the log tree next to itself before any rewrite.

    Each run gets its own destination. Copying over an existing backup
    would put the already-corrected tree where the uncorrected one was,
    so a second ``--apply`` would destroy the only record of what the
    logs said before the first. A fresh directory also keeps the copy
    unmerged: nothing from an earlier run survives inside a later one.

    Returns:
        The backup directory, which is new and did not exist before.

    """
    base = log_dir.with_name(log_dir.name + ".pre-671-backup")
    destination = base
    suffix = 2
    while destination.exists():
        destination = base.with_name(f"{base.name}.{suffix}")
        suffix += 1
    shutil.copytree(log_dir, destination)
    return destination


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="rewrite the logs; without it nothing is written",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="log tree to scan (defaults to the skill log directory)",
    )
    args = parser.parse_args()

    log_dir = args.log_dir or get_log_directory()
    if not log_dir.exists():
        print(f"no log directory at {log_dir}", file=sys.stderr)
        return 1

    files = sorted(log_dir.rglob("*.jsonl"))
    if args.apply and files:
        print(f"backup: {backup_logs(log_dir)}")

    totals = CorrectionStats(path=log_dir)
    for path in files:
        stats = correct_file(path, apply=args.apply)
        totals.entries += stats.entries
        totals.corrected += stats.corrected
        totals.fabricated_zeros += stats.fabricated_zeros
        totals.negatives += stats.negatives
        totals.unparseable += stats.unparseable
        if stats.corrected:
            print(
                f"  {path.relative_to(log_dir)}: "
                f"{stats.fabricated_zeros} fabricated, {stats.negatives} impossible"
            )

    verb = "corrected" if args.apply else "would correct"
    print(
        f"\n{len(files)} files, {totals.entries} entries, "
        f"{totals.unparseable} unparseable"
    )
    print(
        f"{verb} {totals.corrected} "
        f"({totals.fabricated_zeros} fabricated zeros, "
        f"{totals.negatives} impossible intervals)"
    )
    if not args.apply and totals.corrected:
        print("\nre-run with --apply to write these changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
