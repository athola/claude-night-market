"""A list-shaped pass token denied every commit until deleted (ARCH-1)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))

import precommit_gate  # noqa: E402 - hooks dir joins sys.path above


def test_non_object_pass_token_is_no_token(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "pass_token.json").write_text("[]")
    assert precommit_gate.check_pass_token(tmp_path, "abc") is False
