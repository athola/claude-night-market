"""Session persistence: create, save, load, and list research sessions."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from leyline.session_store import (
        SessionStore,
        validate_session_id,
    )
except ImportError:  # pragma: no cover, standalone fallback
    from tome._vendored_leyline_session_store import (
        SessionStore,
        validate_session_id,
    )


from tome.models import ResearchSession, SessionSummary


class _ResearchSessionStore(SessionStore):
    """SessionStore subclass that serializes/deserializes ResearchSession."""

    def _serialize(self, record: Any) -> Any:
        return record.to_dict()

    def _deserialize(self, data: Any) -> Any:
        return ResearchSession.from_dict(data)


class SessionManager:
    """Manages research session persistence under base_dir/.tome/sessions/."""

    def __init__(self, base_dir: Path) -> None:
        sessions_dir = base_dir / ".tome" / "sessions"
        self._sessions_dir = sessions_dir
        self._store = _ResearchSessionStore(sessions_dir)

    def _path_for(self, session_id: str) -> Path:
        """Return the file path for *session_id*, raising ValueError if invalid."""
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session ID: {session_id!r}")
        return self._store._session_path(session_id)

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
        return self._store.save(session.id, session)

    def _read(self, path: Path) -> ResearchSession:
        """Parse one session file, raising ValueError when it is damaged.

        An unreadable file (OSError) is not damaged and propagates, so a
        permission problem is not reported as corruption and skipped.
        """
        text = path.read_text(encoding="utf-8")
        try:
            return ResearchSession.from_dict(json.loads(text))
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            raise ValueError(f"corrupt session file {path}: {exc}") from exc

    def load(self, session_id: str) -> ResearchSession:
        """Deserialize and return a session by ID.

        Raises:
            ValueError: If the ID is invalid or the session file is corrupt.
            FileNotFoundError: If the session file does not exist.
        """
        # Validate eagerly so callers get ValueError on bad IDs (not FileNotFoundError)
        path = self._path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        return self._read(path)

    def load_latest(self) -> ResearchSession | None:
        """Return the newest readable session, or None when there is none.

        Corrupt files are logged to stderr and skipped, so an older valid
        session is returned in preference to None.
        """
        json_files = sorted(
            (
                p
                for p in self._sessions_dir.glob("*.json")
                if validate_session_id(p.stem)
            ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in json_files:
            try:
                return self._read(path)
            except ValueError as exc:
                print(f"tome: {exc}", file=sys.stderr)
        return None

    def list_all(self) -> list[SessionSummary]:
        """Return summaries of all sessions, sorted by created_at descending.

        Sessions without a created_at timestamp sort to the end.
        Corrupt files are logged to stderr and skipped.
        """
        summaries: list[SessionSummary] = []
        for path in self._sessions_dir.glob("*.json"):
            try:
                summaries.append(self._read(path).to_summary())
            except ValueError as exc:
                print(f"tome: {exc}", file=sys.stderr)
        summaries.sort(
            key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return summaries
