"""Lightweight HTTP client for the oracle inference daemon.

Runs on Python 3.9. Uses only stdlib urllib.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class OracleClient:
    """Client for the oracle inference daemon."""

    def __init__(self, port_file: Path, timeout: float = 5.0) -> None:
        """Initialise the client with a port file path and optional timeout."""
        self._port_file = port_file
        self._timeout = timeout
        self._base_url: str | None = None

    def _resolve_url(self) -> str | None:
        """Read port file and return base URL."""
        if self._base_url is not None:
            return self._base_url
        try:
            if not self._port_file.exists():
                return None
            port = int(self._port_file.read_text().strip())
            self._base_url = f"http://127.0.0.1:{port}"
            return self._base_url
        except (OSError, ValueError):
            return None

    def is_available(self) -> bool:
        """Check if daemon is running and healthy."""
        base = self._resolve_url()
        if base is None:
            return False
        try:
            req = Request(f"{base}/health")  # noqa: S310 - localhost-only daemon
            with urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 - localhost-only daemon  # nosec B310 - localhost-only daemon
                data: Any = json.loads(resp.read())
                return bool(data.get("status") == "ok")
        except (URLError, OSError, json.JSONDecodeError):
            self._base_url = None
            return False

    def infer(self, model: str, features: dict) -> float | None:
        """Send features to daemon. Returns score or None on failure."""
        base = self._resolve_url()
        if base is None:
            return None
        try:
            body = json.dumps({"model": model, "features": features}).encode()
            req = Request(  # noqa: S310 - localhost-only daemon
                f"{base}/infer",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 - localhost-only daemon  # nosec B310 - localhost-only daemon
                data = json.loads(resp.read())
                if "score" in data:
                    return float(data["score"])
                return None
        except (URLError, OSError, json.JSONDecodeError, ValueError):
            self._base_url = None
            return None
