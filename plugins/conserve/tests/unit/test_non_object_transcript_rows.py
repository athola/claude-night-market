"""A transcript row that is valid JSON but not an object is skipped.

``json.loads`` accepts ``[1, 2]`` and ``"str"``, and calling ``.get`` on
them raised AttributeError, which ended the hook with a traceback.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from context_warning import _estimate_from_recent_turns  # noqa: E402 - sys.path
from tool_output_summarizer import get_session_output_size  # noqa: E402 - sys.path

_VALID_ROW = {
    "message": {
        "role": "user",
        "content": [{"type": "tool_result", "content": "x" * 40}],
    }
}


def _session(tmp_path: Path) -> Path:
    path = tmp_path / "session.jsonl"
    rows = ["[1, 2]", '"str"', "7", "null", json.dumps(_VALID_ROW)]
    path.write_text("\n".join(rows) + "\n")
    return path


@pytest.mark.unit
def test_output_size_skips_non_object_rows(tmp_path: Path) -> None:
    assert get_session_output_size(_session(tmp_path)) > 0


@pytest.mark.unit
def test_recent_turn_estimate_skips_non_object_rows(tmp_path: Path) -> None:
    estimate = _estimate_from_recent_turns(_session(tmp_path))
    assert estimate is not None
    assert estimate > 0
