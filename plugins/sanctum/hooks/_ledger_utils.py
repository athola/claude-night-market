"""Shared ledger path utilities for sanctum hooks."""

from __future__ import annotations

import os
from pathlib import Path


def get_ledger_path() -> Path:
    """Return the session-scoped ledger path, respecting CLAUDE_HOME."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    return claude_dir / "deferred-items-session.json"
