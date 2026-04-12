"""Insight deduplication registry.

Accepts findings from any source, deduplicates via
content hashing with 30-day staleness expiry, and
persists state to disk.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from insight_types import Finding, finding_hash

STALENESS_DAYS = 30


class InsightRegistry:
    """Tracks posted insights and prevents duplicates."""

    def __init__(self, state_path: Path | None = None):
        self._path = state_path or (
            Path.home() / ".claude" / "skills" / "discussions" / "insights_posted.json"
        )
        self._state: dict = {"posted_hashes": {}, "last_snapshot": {}}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        # Ensure required keys
        self._state.setdefault("posted_hashes", {})
        self._state.setdefault("last_snapshot", {})

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._state, indent=2))

    def check_local(self, finding: Finding) -> str:
        """Check if a finding is a local duplicate.

        Returns:
            "skip" if already posted and not stale,
            "create" if new or stale.

        """
        h = finding_hash(finding)
        entry = self._state["posted_hashes"].get(h)
        if entry is None:
            return "create"

        posted_at = entry.get("posted_at", "")
        if self._is_stale(posted_at):
            return "create"

        return "skip"

    def record_posted(self, finding: Finding, url: str) -> None:
        """Record that a finding was posted."""
        h = finding_hash(finding)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._state["posted_hashes"][h] = {
            "url": url,
            "posted_at": today,
            "type": finding.type,
            "summary": finding.summary,
        }
        self._save()

    def save_snapshot(self, snapshot: dict) -> None:
        """Save a metrics snapshot for delta comparison."""
        self._state["last_snapshot"] = snapshot
        self._save()

    def load_snapshot(self) -> dict[str, Any]:
        """Load the last metrics snapshot."""
        result: dict[str, Any] = self._state.get("last_snapshot", {})
        return result

    @staticmethod
    def _is_stale(posted_at: str, max_age_days: int = STALENESS_DAYS) -> bool:
        if not posted_at:
            return True
        try:
            posted_date = datetime.strptime(posted_at, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            age = (datetime.now(timezone.utc) - posted_date).days
            return age > max_age_days
        except ValueError:
            return True
