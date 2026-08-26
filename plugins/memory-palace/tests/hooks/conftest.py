"""Keep hook tests off the real memory palace.

The web research handler prunes its staging queue as a side effect of a
successful capture. Tests that drive `main()` therefore delete real
files, and on 2026-08-23 a test run took the live staging directory
from 2,544 captures to 400 before anyone noticed. Nothing in those
tests mentioned pruning; the destruction rode along on a code path
they were exercising for another reason.

A hook that writes to a fixed location needs that location redirected
for the whole test session, not per test that remembers to ask.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[2] / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


@pytest.fixture(autouse=True)
def _staging_is_disposable(tmp_path, monkeypatch):
    """Point every staging write and prune at a throwaway directory."""
    try:
        import web_research_handler as handler
    except ImportError:  # pragma: no cover - module not on the path
        return

    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    for name in ("STAGING_DIR", "QUEUE_DIR"):
        if hasattr(handler, name):
            monkeypatch.setattr(handler, name, staging)
