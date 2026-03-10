"""Experience library for storing successful skill execution trajectories.

Stores task descriptions, approaches, and outcomes from successful
skill executions. Retrieved via keyword similarity matching.
Context injection is planned but not yet implemented.

Part of the self-adapting system. See:
docs/adr/0006-self-adapting-skill-health.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_ENTRIES_PER_SKILL = 20
MAX_EXEMPLARS = 3

STOP_WORDS: frozenset = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "about",
        "it",
        "its",
        "this",
        "that",
        "and",
        "or",
        "but",
        "not",
        "no",
        "if",
        "then",
        "so",
    }
)


@dataclass
class ExecutionTrajectory:
    """A single execution trajectory to store in the library."""

    skill_ref: str
    task_description: str
    approach_taken: str
    outcome: str
    duration_ms: int
    tools_used: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)


class ExperienceLibrary:
    """Stores and retrieves successful execution patterns."""

    def __init__(self, library_dir: Path) -> None:
        self.library_dir = library_dir
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def _skill_dir(self, skill_ref: str) -> Path:
        """Get directory for a specific skill's experiences."""
        safe_name = skill_ref.replace(":", "_").replace("/", "_")
        d = self.library_dir / safe_name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _task_hash(self, task_description: str) -> str:
        """Generate a short hash for a task description."""
        return hashlib.sha256(task_description.encode()).hexdigest()[:12]

    def store(
        self, trajectory: ExecutionTrajectory | None = None, **kwargs: Any
    ) -> bool:
        """Store a successful execution trajectory.

        Accepts an ExecutionTrajectory dataclass or keyword arguments.
        Returns True if stored, False if rejected.
        """
        if trajectory is None:
            trajectory = ExecutionTrajectory(**kwargs)

        if trajectory.outcome != "success":
            return False

        entry = {
            "task_description": trajectory.task_description,
            "approach_taken": trajectory.approach_taken,
            "outcome": trajectory.outcome,
            "duration_ms": trajectory.duration_ms,
            "tools_used": trajectory.tools_used,
            "key_decisions": trajectory.key_decisions,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        skill_dir = self._skill_dir(trajectory.skill_ref)
        task_hash = self._task_hash(trajectory.task_description)
        entry_file = skill_dir / f"{task_hash}.json"
        try:
            entry_file.write_text(json.dumps(entry, indent=2))
        except OSError as e:
            sys.stderr.write(
                f"experience_library: failed to write entry {entry_file}: {e}\n"
            )
            return False

        self._prune(trajectory.skill_ref)
        return True

    def list_entries(self, skill_ref: str) -> list[dict[str, Any]]:
        """List all entries for a skill."""
        skill_dir = self._skill_dir(skill_ref)
        entries = []
        for f in sorted(skill_dir.glob("*.json")):
            try:
                entries.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                sys.stderr.write(
                    f"experience_library: corrupt JSON in entry {f}, skipping\n"
                )
                continue
            except OSError as e:
                sys.stderr.write(
                    f"experience_library: failed to read entry {f}: {e}, skipping\n"
                )
                continue
        return entries

    def find_similar(
        self, skill_ref: str, query: str, max_results: int = MAX_EXEMPLARS
    ) -> list[dict[str, Any]]:
        """Find similar past experiences by keyword overlap."""
        entries = self.list_entries(skill_ref)
        if not entries:
            return []

        query_words = set(query.lower().split()) - STOP_WORDS

        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in entries:
            desc_words = set(entry["task_description"].lower().split()) - STOP_WORDS
            overlap = len(query_words & desc_words)
            if overlap > 0:
                scored.append((overlap, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:max_results]]

    def _prune(self, skill_ref: str) -> None:
        """Keep only the most recent MAX_ENTRIES_PER_SKILL entries."""
        skill_dir = self._skill_dir(skill_ref)
        files = sorted(skill_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
        while len(files) > MAX_ENTRIES_PER_SKILL:
            oldest = files.pop(0)
            oldest.unlink()
