"""The quota-management skill's examples compare against real return values.

Math review finding C28: the Quick Start compared ``status == "CRITICAL"``
while ``QuotaTracker.get_quota_status`` returns lowercase levels, so the
"defer or use secondary service" branch could never run.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from leyline.quota_tracker import QuotaConfig, QuotaTracker

SKILL_FILE = (
    Path(__file__).resolve().parents[3] / "skills" / "quota-management" / "SKILL.md"
)


def _levels_the_tracker_returns(tmp_path: Path) -> set[str]:
    config = QuotaConfig(requests_per_minute=100)
    levels = set()
    for requests in (0, 85, 100):
        tracker = QuotaTracker("doc-check", config, storage_dir=tmp_path)
        tracker.usage.requests_this_minute = requests
        levels.add(tracker.get_quota_status()[0])
    return levels


@pytest.mark.unit
def test_documented_status_comparisons_use_values_the_tracker_returns(
    tmp_path: Path,
) -> None:
    """Every ``status == "..."`` in the skill names a returned level."""
    returned = _levels_the_tracker_returns(tmp_path)
    compared = set(re.findall(r'status == "([^"]+)"', SKILL_FILE.read_text()))

    assert compared, "the skill no longer shows a status comparison"
    assert compared <= returned, compared - returned
