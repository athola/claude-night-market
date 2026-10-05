"""escape_for_json's jq-less fallback must emit valid JSON (shell review S2-14, S2-15).

The fallback runs when jq is not on PATH. Every replacement was written
one escape level too deep: a quote came out as \\" (ending the string
early) and a backslash was never matched at all.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COPIES = [
    "scripts/shared/json_utils.sh",
    "plugins/imbue/hooks/shared/json_utils.sh",
    "plugins/conserve/hooks/shared/json_utils.sh",
    "plugins/memory-palace/hooks/shared/json_utils.sh",
]
SAMPLE = 'say "hi"\\c:\\temp\nnext\ttab\rcr\x01ctl\x0bvt\x1fend'


def _escape_without_jq(lib: Path, text: str, tmp_path: Path) -> str:
    """Run escape_for_json with a PATH that holds no jq."""
    proc = subprocess.run(
        ["/bin/bash", "-c", 'source "$0"; escape_for_json "$1"', str(lib), text],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": str(tmp_path)},
    )
    return proc.stdout


@pytest.mark.parametrize("copy", COPIES)
def test_fallback_output_round_trips_through_a_json_parser(
    copy: str, tmp_path: Path
) -> None:
    """Every escape decodes back to the original character."""
    escaped = _escape_without_jq(ROOT / copy, SAMPLE, tmp_path)
    assert json.loads(f'"{escaped}"') == SAMPLE
