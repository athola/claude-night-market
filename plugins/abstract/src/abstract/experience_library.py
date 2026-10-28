"""Experience library for storing successful skill execution trajectories.

The PostToolUse logger stores each successful Skill call that carried
args; the PreToolUse hook injects the most recent entries for the same
skill as additionalContext.

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


@dataclass
class ExecutionTrajectory:
    """A single execution trajectory to store in the library."""

    skill_ref: str
    task_description: str
    approach_taken: str
    outcome: str
    # None when the hooks could not time the call (#671); never a fake 0.
    duration_ms: int | None
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

    def recent_entries(self, skill_ref: str, limit: int) -> list[dict[str, Any]]:
        """Return up to ``limit`` entries, newest first.

        Reads without creating the skill directory: the PreToolUse hook
        calls this for every skill, most of which have no entries.
        """
        safe_name = skill_ref.replace(":", "_").replace("/", "_")
        if not (self.library_dir / safe_name).is_dir():
            return []
        entries = self.list_entries(skill_ref)
        entries.sort(key=lambda e: str(e.get("stored_at", "")), reverse=True)
        return entries[:limit]

    def _prune(self, skill_ref: str) -> None:
        """Keep only the most recent MAX_ENTRIES_PER_SKILL entries."""
        skill_dir = self._skill_dir(skill_ref)
        files = sorted(skill_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
        while len(files) > MAX_ENTRIES_PER_SKILL:
            oldest = files.pop(0)
            oldest.unlink()


def format_context(entries: list[dict[str, Any]], max_chars_each: int) -> str:
    """Render entries as context text, each cut to ``max_chars_each``.

    The cap bounds what a long args string can add to every later
    invocation of the skill.
    """
    blocks = []
    for entry in entries:
        lines = [f"- Task: {entry.get('task_description', '')}"]
        if entry.get("approach_taken"):
            lines.append(f"  Approach: {entry['approach_taken']}")
        if entry.get("tools_used"):
            lines.append(f"  Tools: {', '.join(entry['tools_used'])}")
        blocks.append("\n".join(lines)[:max_chars_each])
    return "\n".join(blocks)
