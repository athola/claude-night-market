"""The context-band mod and context_warning.py agree on "critical".

The mod sets the status line at a percentage hard-coded in TypeScript,
and the Python hook warns Claude at CRITICAL_THRESHOLD. The two are read
by different audiences in the same session, so a drift between them
shows the user a calm band while Claude is told context is critical, or
the reverse.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))

from context_warning import CRITICAL_THRESHOLD

HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
MOD_CONSTANT = re.compile(r"^const CRITICAL_PERCENT = (\d+)$", re.MULTILINE)


def test_band_critical_percent_matches_python_critical_threshold() -> None:
    """Scenario: both surfaces call context critical at the same fill."""
    source = (HOOKS_DIR / "context-band.tsx").read_text(encoding="utf-8")
    found = MOD_CONSTANT.findall(source)
    assert len(found) == 1, "context-band.tsx must declare CRITICAL_PERCENT once"
    assert int(found[0]) == round(CRITICAL_THRESHOLD * 100)
