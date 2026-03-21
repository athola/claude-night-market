"""Session persistence: create, save, load, and list research sessions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tome.models import ResearchSession, SessionSummary


class SessionManager:
    """Manages research session persistence under base_dir/.tome/sessions/."""

    def __init__(self, base_dir: Path) -> None:
        self._sessions_dir = base_dir / ".tome" / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_id: str) -> Path:
        return self._sessions_dir / f"{session_id}.json"

    def create(
        self,
        topic: str,
        domain: str,
        triz_depth: str,
        channels: list[str],
    ) -> ResearchSession:
        """Create a new active session, persist it, and return it."""
        session = ResearchSession(
            topic=topic,
            domain=domain,
            triz_depth=triz_depth,
            channels=channels,
            status="active",
            created_at=datetime.now(tz=timezone.utc),
        )
        self.save(session)
        return session

    def save(self, session: ResearchSession) -> Path:
        """Serialize session to JSON and write to disk; returns the file path."""
        path = self._path_for(session.id)
        path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
        return path

    def load(self, session_id: str) -> ResearchSession:
        """Deserialize and return a session by ID.

        Raises FileNotFoundError if the session file does not exist.
        """
        path = self._path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ResearchSession.from_dict(data)

    def load_latest(self) -> ResearchSession | None:
        """Return the most recently modified session, or None."""
        json_files = list(self._sessions_dir.glob("*.json"))
        if not json_files:
            return None
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        try:
            data = json.loads(latest_file.read_text(encoding="utf-8"))
            return ResearchSession.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    def list_all(self) -> list[SessionSummary]:
        """Return summaries of all sessions, sorted by created_at descending.

        Sessions without a created_at timestamp sort to the end.
        """
        summaries: list[SessionSummary] = []
        for path in self._sessions_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            session = ResearchSession.from_dict(data)
            summaries.append(session.to_summary())
        summaries.sort(
            key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return summaries
