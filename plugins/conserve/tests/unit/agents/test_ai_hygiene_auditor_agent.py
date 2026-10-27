"""The ai-hygiene auditor reads repeated names from the census.

The agent already runs ``detect_duplicates.py`` for repeated blocks. Its
name heuristic was a second detector, a grep counting every ``def`` name
seen more than twice, which on this repository is mostly CLI scaffolding
such as ``_build_parser``. The census in the same JSON report compares
bodies, so it names only the cases that are two models of one concern
(docs/knowledge-corpus/decoherence.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[3] / "agents" / "ai-hygiene-auditor.md"


@pytest.mark.unit
def test_repeated_names_come_from_the_census() -> None:
    """The finding is built from ``competing_implementations``."""
    assert 'duplicates["competing_implementations"]' in AGENT.read_text()


@pytest.mark.unit
def test_the_name_count_grep_is_gone() -> None:
    """No second detector counts bare ``def`` names."""
    assert "uniq -c" not in AGENT.read_text()
