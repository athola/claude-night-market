"""Reusable JSON-file session store with safe ID validation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")


def validate_session_id(session_id: str) -> bool:
    """Check if session ID is safe for use as a filename."""
    return (
        bool(_SAFE_ID_RE.match(session_id))
        and len(session_id) <= 128
        and ".." not in session_id
    )


class SessionStore:
    """Base JSON-file session store with CRUD operations.

    Subclasses must implement:
    - ``_serialize(record) -> dict``
    - ``_deserialize(data: dict) -> record``
    """

    def __init__(self, sessions_dir: Path) -> None:
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def save(self, session_id: str, record: Any) -> Path:
        """Persist a record by session ID; returns the written path."""
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session ID: {session_id!r}")
        path = self._session_path(session_id)
        data = self._serialize(record)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def load(self, session_id: str) -> Any | None:
        """Load a record by session ID; returns None if missing or corrupt."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._deserialize(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(
                f"Warning: corrupt session {session_id}: {e}",
                file=sys.stderr,
            )
            return None

    def list_sessions(self) -> list[str]:
        """Return sorted list of valid session IDs found on disk."""
        if not self.sessions_dir.exists():
            return []
        return sorted(
            p.stem
            for p in self.sessions_dir.glob("*.json")
            if validate_session_id(p.stem)
        )

    def delete(self, session_id: str) -> bool:
        """Delete a session file; returns True if deleted, False if absent."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _serialize(self, record: Any) -> dict:  # type: ignore[type-arg]
        raise NotImplementedError

    def _deserialize(self, data: dict) -> Any:  # type: ignore[type-arg]
        raise NotImplementedError
