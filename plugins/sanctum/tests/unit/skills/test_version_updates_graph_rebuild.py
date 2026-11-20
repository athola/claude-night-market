"""A version bump rebuilds the gauntlet graph when the project keeps one."""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL = Path(__file__).resolve().parents[3] / "skills" / "version-updates" / "SKILL.md"


@pytest.mark.unit
def test_verification_rebuilds_an_existing_gauntlet_graph() -> None:
    # The bump changes gauntlet's recorded version. Rebuilding here stamps
    # the graph with the release, so the installed plugin's SessionStart
    # hook does not rebuild the same graph again after the update.
    text = _SKILL.read_text(encoding="utf-8")
    verification = text.split("## Step 5: Verification", 1)[1].split("\n## ", 1)[0]
    assert ".gauntlet/graph.db" in verification
    assert "make graph" in verification
    exit_criteria = text.split("## Exit Criteria", 1)[1]
    assert ".gauntlet/graph.db" in exit_criteria
