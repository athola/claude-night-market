"""doc-consolidation names new ADRs the way the ADR directory does."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "doc-consolidation"
ADR_DIR = Path(__file__).resolve().parents[5] / "docs" / "adr"


@pytest.mark.unit
def test_adr_destination_carries_no_date() -> None:
    # A dated name sorts and links differently from every committed ADR.
    for path in [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "modules").glob("*.md"))]:
        for target in re.findall(
            r"docs/adr/[^`|\s]+", path.read_text(encoding="utf-8")
        ):
            dated = re.search(r"date|YYYY|\d{4}-\d{2}-\d{2}", target, re.IGNORECASE)
            assert not dated, (path.name, target)


@pytest.mark.unit
def test_committed_adrs_follow_the_undated_convention() -> None:
    names = sorted(p.name for p in ADR_DIR.glob("*.md") if p.name[:4].isdigit())
    assert names
    for name in names:
        assert re.fullmatch(r"\d{4}-[a-z0-9-]+\.md", name), name
