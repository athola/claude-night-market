"""clear-context caps its self-grading loop and its handoff chain (ADR-0025)."""

from __future__ import annotations

from pathlib import Path

_SKILL = Path(__file__).resolve().parents[2] / "skills" / "clear-context" / "SKILL.md"


def test_the_re_score_loop_is_capped() -> None:
    assert "Re-score at most twice" in _SKILL.read_text(encoding="utf-8")


def test_the_handoff_chain_is_capped() -> None:
    text = _SKILL.read_text(encoding="utf-8")
    assert "handoff_depth" in text
    assert "At depth 3" in text
