"""HTTP inference daemon for oracle plugin.

Serves ML model inference over HTTP on localhost using stdlib http.server.
Loads YAML model files from a directory and serves /health and /infer
endpoints.
"""

from __future__ import annotations

import argparse
import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import yaml


class _ModelRegistry:
    """Load .yaml model files from a directory and run inference."""

    def __init__(self, models_dir: Path) -> None:
        self._models: dict[str, dict[str, Any]] = {}
        self._load(models_dir)

    def _load(self, models_dir: Path) -> None:
        for path in sorted(models_dir.glob("*.yaml")):
            name = path.stem
            with path.open() as fh:
                data = yaml.safe_load(fh)
            self._models[name] = data

    def list_models(self) -> list[str]:
        """Return sorted list of loaded model names."""
        return sorted(self._models.keys())

    def infer(self, model_name: str, features: dict[str, float]) -> dict[str, Any]:
        """Run inference and return score with metadata.

        Returns a dict with ``score`` (float) and ``blend``
        (word_overlap/ml weight pair parsed from the model YAML).

        Raises KeyError if model_name is unknown.
        """
        model = self._models[model_name]
        weights: dict[str, float] = model.get("weights", {})
        intercept: float = float(model.get("intercept", 0.0))

        linear = intercept
        for feat, w in weights.items():
            linear += w * float(features.get(feat, 0.0))

        if model.get("sigmoid", False):
            clamped = max(-500.0, min(500.0, linear))
            score = 1.0 / (1.0 + math.exp(-clamped))
        else:
            score = linear

        blend_cfg = model.get("blend", {})
        wo = max(0.0, float(blend_cfg.get("word_overlap_weight", 0.5)))
        ml = max(0.0, float(blend_cfg.get("ml_weight", 0.5)))
        total = wo + ml
        if total > 0:
            wo, ml = wo / total, ml / total
        else:
            wo, ml = 0.5, 0.5

        return {"score": score, "blend": {"word_overlap_weight": wo, "ml_weight": ml}}


class _InferenceServer(HTTPServer):
    """HTTPServer subclass that carries a model registry reference."""

    def __init__(
        self,
        server_address: tuple[str, int],
        registry: _ModelRegistry,
    ) -> None:
        """Initialise server with a pre-built registry."""
        self.registry = registry
        super().__init__(server_address, _InferenceHandler)


class _InferenceHandler(BaseHTTPRequestHandler):
    """Handle GET /health and POST /infer."""

    server: _InferenceServer  # type narrowing for mypy

    def log_message(  # noqa: A002 - overrides stdlib BaseHTTPRequestHandler.log_message signature
        self,
        format: str,
        *args: Any,  # noqa: A002 - overrides stdlib BaseHTTPRequestHandler.log_message signature
    ) -> None:
        """Suppress default access log output."""

    def _send_json(self, status: int, body: Any) -> None:
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler requires uppercase verb methods
        """Dispatch GET requests."""
        if self.path == "/health":
            self._send_json(
                200,
                {"status": "ok", "models": self.server.registry.list_models()},
            )
        else:
            self._send_json(404, {"error": f"Not found: {self.path}"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler requires uppercase verb methods
        """Dispatch POST requests."""
        if self.path != "/infer":
            self._send_json(404, {"error": f"Not found: {self.path}"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""

        if not raw:
            self._send_json(400, {"error": "Empty request body"})
            return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        model_name: str | None = payload.get("model")
        features = payload.get("features", {})

        if not model_name:
            self._send_json(400, {"error": "Missing 'model' field"})
            return

        try:
            result = self.server.registry.infer(model_name, features)
        except KeyError:
            self._send_json(404, {"error": f"Unknown model: {model_name!r}"})
            return

        self._send_json(200, result)


class InferenceDaemon:
    """Manage lifecycle of the inference HTTP server.

    Parameters
    ----------
    host:
        Bind address (default ``127.0.0.1``).
    port:
        TCP port; pass ``0`` to let the OS pick a free port.
    models_dir:
        Directory containing ``*.yaml`` model files.
    port_file:
        Path where the bound port number is written after startup.

    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        models_dir: Path | None = None,
        port_file: Path | None = None,
    ) -> None:
        """Initialise and bind the server socket."""
        self._host = host
        self._models_dir = models_dir or Path("models")
        self._port_file: Path | None = port_file
        self._registry = _ModelRegistry(self._models_dir)
        self._server = _InferenceServer((host, port), self._registry)

    @property
    def port(self) -> int:
        """Actual bound port (resolved after the socket is open)."""
        return self._server.server_address[1]

    @property
    def port_file(self) -> Path | None:
        """Path to the port file (may be None if not configured)."""
        return self._port_file

    def serve_forever(self) -> None:
        """Write port file then start serving requests (blocks)."""
        if self._port_file is not None:
            self._port_file.write_text(str(self.port))
        self._server.serve_forever()

    def shutdown(self) -> None:
        """Stop the server loop."""
        self._server.shutdown()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Oracle HTTP inference daemon")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--models-dir", type=Path, default=Path("models"))
    parser.add_argument("--port-file", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = _parse_args()
    d = InferenceDaemon(
        host=args.host,
        port=args.port,
        models_dir=args.models_dir,
        port_file=args.port_file,
    )
    try:
        d.serve_forever()
    except KeyboardInterrupt:
        d.shutdown()
