"""A list-shaped throttle file crashed the Stop hook (ARCH-1)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))

import double_shot_latte  # noqa: E402 - hooks dir joins sys.path above


def test_non_object_throttle_file_reads_as_fresh(tmp_path: Path) -> None:
    throttle = tmp_path / "throttle.json"
    throttle.write_text("[]")
    assert double_shot_latte._read_throttle(throttle) == (0, 0.0)
