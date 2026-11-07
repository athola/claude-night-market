"""Tests for session-gap narration in the SessionStart path.

Feature: Elapsed time is reported, never inferred
  Without an explicit reading, a model treats a five-week gap the same
  as a five-second one and acts on stale state units.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "hooks"))
