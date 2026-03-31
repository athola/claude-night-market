"""Progress tracking for the gauntlet plugin."""

from __future__ import annotations

import datetime
import json
import random
import re
from pathlib import Path

from gauntlet.models import AnswerRecord, DeveloperProgress, KnowledgeEntry

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SAFE_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def _sanitize(developer_id: str) -> str:
    """Convert an arbitrary developer ID (e.g. email) to a safe filename stem."""
    return _SAFE_RE.sub("_", developer_id)


# ---------------------------------------------------------------------------
# ProgressTracker
# ---------------------------------------------------------------------------


class ProgressTracker:
    """Persist and query developer challenge progress."""

    def __init__(self, gauntlet_dir: Path) -> None:
        self._progress_dir = gauntlet_dir / "progress"

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _path_for(self, developer_id: str) -> Path:
        return self._progress_dir / f"{_sanitize(developer_id)}.json"

    def get_or_create(self, developer_id: str) -> DeveloperProgress:
        """Load existing progress from disk, or return a fresh record."""
        path = self._path_for(developer_id)
        if path.exists():
            data = json.loads(path.read_text())
            return DeveloperProgress.from_dict(data)
        return DeveloperProgress(developer_id=developer_id)

    def save(self, progress: DeveloperProgress) -> None:
        """Persist *progress* to disk."""
        self._progress_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(progress.developer_id)
        path.write_text(json.dumps(progress.to_dict(), indent=2))

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_answer(
        self,
        progress: DeveloperProgress,
        challenge_id: str,
        knowledge_entry_id: str,
        challenge_type: str,
        category: str,
        difficulty: int,
        result: str,
    ) -> None:
        """Append a result to history, update streak, and auto-save."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        record = AnswerRecord(
            challenge_id=challenge_id,
            knowledge_entry_id=knowledge_entry_id,
            challenge_type=challenge_type,
            category=category,
            difficulty=difficulty,
            result=result,
            answered_at=now,
        )
        progress.history.append(record)
        progress.last_seen[knowledge_entry_id] = now

        if result == "pass":
            progress.streak += 1
        else:
            progress.streak = 0

        self.save(progress)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select_entry(
        self, progress: DeveloperProgress, entries: list[KnowledgeEntry]
    ) -> KnowledgeEntry:
        """Weighted random selection of the next knowledge entry.

        Weight components per entry:
        - Base weight: 1.0
        - Unseen (not in last_seen): +2.0
        - Weak category (below average accuracy): proportional bonus
        - Untested category (no history for it): +1.5
        """
        weights: list[float] = []
        seen_ids = set(progress.last_seen.keys())

        for entry in entries:
            w = 1.0
            if entry.id not in seen_ids:
                w += 2.0

            cat_records = [r for r in progress.history if r.category == entry.category]
            if not cat_records:
                w += 1.5
            else:
                accuracy = sum(r.score() for r in cat_records) / len(cat_records)
                # weak category: accuracy < 0.5 gets extra weight
                if accuracy < 0.5:
                    w += (0.5 - accuracy) * 2.0

            weights.append(w)

        return random.choices(entries, weights=weights, k=1)[0]

    # ------------------------------------------------------------------
    # Difficulty
    # ------------------------------------------------------------------

    def current_difficulty(self, progress: DeveloperProgress) -> int:
        """Return adaptive difficulty: base 3, +1 per 3 consecutive correct, max 5."""
        bonus = progress.streak // 3
        return min(5, 3 + bonus)
