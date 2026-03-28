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
except ImportError:  # pragma: no cover — standalone fallback
    import re as _re

    def validate_session_id(session_id: str) -> bool:
        """Fallback ID validator used when leyline is not installed."""
        pattern = _re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
        return (
            bool(pattern.match(session_id))
            and len(session_id) <= 128
            and ".." not in session_id
        )

    class SessionStore:
        """Minimal fallback base when leyline is absent."""

        def __init__(self, sessions_dir: Path) -> None:
            self.sessions_dir = sessions_dir
            self.sessions_dir.mkdir(parents=True, exist_ok=True)

        def _session_path(self, session_id: str) -> Path:
            return self.sessions_dir / f"{session_id}.json"

        def save(self, session_id: str, record: Any) -> Path:
            if not validate_session_id(session_id):
                raise ValueError(f"Invalid session ID: {session_id!r}")
            path = self._session_path(session_id)
            path.write_text(
                json.dumps(self._serialize(record), indent=2), encoding="utf-8"
            )
            return path

        def load(self, session_id: str) -> Any | None:
            path = self._session_path(session_id)
            if not path.exists():
                return None
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return self._deserialize(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: corrupt session {session_id}: {e}", file=sys.stderr)
                return None

        def list_sessions(self) -> list[str]:
            if not self.sessions_dir.exists():
                return []
            return sorted(
                p.stem
                for p in self.sessions_dir.glob("*.json")
                if validate_session_id(p.stem)
            )

        def delete(self, session_id: str) -> bool:
            path = self._session_path(session_id)
            if path.exists():
                path.unlink()
                return True
            return False

        def _serialize(self, record: Any) -> dict:
            raise NotImplementedError

        def _deserialize(self, data: dict) -> Any:
            raise NotImplementedError


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

    def load(self, session_id: str) -> ResearchSession:
        """Deserialize and return a session by ID.

        Raises FileNotFoundError if the session file does not exist.
        """
        # Validate eagerly so callers get ValueError on bad IDs (not FileNotFoundError)
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session ID: {session_id!r}")
        result: ResearchSession | None = self._store.load(session_id)
        if result is None:
            raise FileNotFoundError(f"Session not found: {session_id}")
        return result

    def load_latest(self) -> ResearchSession | None:
        """Return the most recently modified session, or None."""
        json_files = list(self._sessions_dir.glob("*.json"))
        if not json_files:
            return None
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        try:
            data = json.loads(latest_file.read_text(encoding="utf-8"))
            return ResearchSession.from_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"tome: corrupt session file {latest_file}: {exc}", file=sys.stderr)
            return None

    def list_all(self) -> list[SessionSummary]:
        """Return summaries of all sessions, sorted by created_at descending.

        Sessions without a created_at timestamp sort to the end.
        Corrupt files are logged to stderr and skipped.
        """
        summaries: list[SessionSummary] = []
        for path in self._sessions_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session = ResearchSession.from_dict(data)
                summaries.append(session.to_summary())
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                print(f"tome: corrupt session file {path}: {exc}", file=sys.stderr)
                continue
        summaries.sort(
            key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return summaries
