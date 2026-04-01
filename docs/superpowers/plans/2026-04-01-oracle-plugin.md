# Oracle Plugin + Gauntlet Integration -- Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Create a standalone `oracle` plugin that provides
ONNX Runtime inference as an HTTP daemon, and wire gauntlet
to auto-detect and use it when available.

**Architecture:** Oracle is a marketplace-installable plugin
with explicit opt-in activation. The daemon runs in a
uv-provisioned Python 3.11+ venv with onnxruntime, serves
inference over HTTP on localhost, and is discovered by other
plugins via a port file in `$CLAUDE_PLUGIN_DATA/oracle/`.
Gauntlet's `score_answer_quality()` tries the oracle daemon
first, falls back to the existing YamlScorer.

**Tech Stack:** Python 3.9 (hooks/client), Python 3.11+
(daemon venv), uv, onnxruntime, http.server (stdlib),
urllib (stdlib client -- no requests dependency)

**Spec:** `docs/superpowers/specs/2026-03-31-onnx-integration-design.md` (Phase 2 section)

**Marketplace safety contract:**
- Installing oracle does NOTHING until user runs `/oracle:setup`
- No surprise downloads, no background processes, no errors
- Uninstalling oracle causes zero errors in gauntlet
- All network calls happen only during explicit `/oracle:setup`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `plugins/oracle/.claude-plugin/plugin.json` | Plugin manifest |
| Create | `plugins/oracle/pyproject.toml` | Package config (Python 3.9, no deps) |
| Create | `plugins/oracle/src/oracle/__init__.py` | Package root |
| Create | `plugins/oracle/src/oracle/daemon.py` | HTTP inference server (runs in 3.11+ venv) |
| Create | `plugins/oracle/src/oracle/client.py` | Lightweight HTTP client (runs on 3.9) |
| Create | `plugins/oracle/src/oracle/provision.py` | uv venv + onnxruntime provisioning |
| Create | `plugins/oracle/hooks/daemon_lifecycle.py` | SessionStart/SessionEnd daemon management |
| Create | `plugins/oracle/skills/setup/SKILL.md` | Setup skill for provisioning |
| Create | `plugins/oracle/commands/oracle-setup.md` | User-facing setup command |
| Create | `plugins/oracle/tests/unit/test_client.py` | Client unit tests |
| Create | `plugins/oracle/tests/unit/test_daemon.py` | Daemon unit tests |
| Create | `plugins/oracle/tests/unit/test_provision.py` | Provisioning unit tests |
| Create | `plugins/oracle/tests/conftest.py` | Test fixtures |
| Create | `plugins/oracle/tests/__init__.py` | Test package |
| Create | `plugins/oracle/tests/unit/__init__.py` | Unit test package |
| Modify | `plugins/gauntlet/src/gauntlet/ml/__init__.py` | Add oracle sidecar detection |
| Modify | `plugins/gauntlet/src/gauntlet/ml/scorer.py` | Add OnnxSidecarScorer class |
| Create | `plugins/gauntlet/tests/unit/test_sidecar_scorer.py` | Sidecar scorer tests |

---

## Task 1: Oracle Plugin Skeleton

**Files:**
- Create: `plugins/oracle/.claude-plugin/plugin.json`
- Create: `plugins/oracle/pyproject.toml`
- Create: `plugins/oracle/src/oracle/__init__.py`
- Create: `plugins/oracle/tests/__init__.py`
- Create: `plugins/oracle/tests/unit/__init__.py`
- Create: `plugins/oracle/tests/conftest.py`

- [ ] **Step 1: Create plugin directory structure**

```bash
mkdir -p plugins/oracle/.claude-plugin
mkdir -p plugins/oracle/src/oracle
mkdir -p plugins/oracle/hooks
mkdir -p plugins/oracle/skills/setup
mkdir -p plugins/oracle/commands
mkdir -p plugins/oracle/tests/unit
```

- [ ] **Step 2: Create plugin.json**

```json
{
  "name": "oracle",
  "version": "1.0.0",
  "description": "ONNX Runtime inference daemon for ML-enhanced plugin capabilities. Provides local model inference over HTTP with explicit opt-in activation.",
  "skills": [
    "./skills/setup"
  ],
  "commands": [
    "./commands/oracle-setup.md"
  ],
  "agents": [],
  "hooks": [
    {
      "event": "SessionStart",
      "script": "./hooks/daemon_lifecycle.py"
    },
    {
      "event": "Stop",
      "script": "./hooks/daemon_lifecycle.py"
    }
  ],
  "dependencies": [],
  "keywords": ["ml", "inference", "onnx", "scoring", "daemon"],
  "author": {"name": "Alex Thola", "url": "https://github.com/athola"},
  "license": "MIT"
}
```

- [ ] **Step 3: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "oracle"
version = "1.0.0"
description = "ONNX Runtime inference daemon for Claude Code plugins"
authors = [
    {name = "Alex Thola", email = "alexthola@gmail.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = [
    "ruff>=0.14.13",
    "mypy>=1.11.0",
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/oracle"]

[tool.ruff]
line-length = 88
target-version = "py39"
exclude = [".venv", ".uv-cache"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "S", "PL", "D"]
extend-ignore = ["S101", "E203", "D203", "D213", "UP017"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101", "S108", "PLR2004", "D102", "D103", "D205", "D400", "D415",
    "D212", "S603", "S607", "PLW1510",
]
"hooks/**/*.py" = ["S603", "S607", "PLR0911", "PLR2004", "UP045", "S105"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src", "hooks"]
addopts = "-v --cov=src/oracle --cov-report=term-missing --cov-fail-under=90"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
]

[tool.coverage.run]
source = ["src/oracle"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 90
```

- [ ] **Step 4: Create package init files**

```python
# plugins/oracle/src/oracle/__init__.py
"""Oracle: ONNX Runtime inference daemon for Claude Code plugins."""

from __future__ import annotations

__version__ = "1.0.0"
```

```python
# plugins/oracle/tests/__init__.py
```

```python
# plugins/oracle/tests/unit/__init__.py
```

```python
# plugins/oracle/tests/conftest.py
from __future__ import annotations
```

- [ ] **Step 5: Commit**

```bash
git add plugins/oracle/
git commit -m "feat(oracle): create plugin skeleton with marketplace-safe structure"
```

---

## Task 2: Provisioning Module

**Files:**
- Create: `plugins/oracle/tests/unit/test_provision.py`
- Create: `plugins/oracle/src/oracle/provision.py`

- [ ] **Step 1: Write failing tests for provisioning**

```python
# plugins/oracle/tests/unit/test_provision.py
"""Tests for oracle venv provisioning."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from oracle.provision import (
    get_oracle_data_dir,
    get_venv_path,
    is_provisioned,
    provision_venv,
)


class TestOracleDataDir:
    """
    Feature: Oracle data directory management

    As the oracle plugin
    I want a stable data directory for venv and state
    So that provisioning survives plugin updates
    """

    @pytest.mark.unit
    def test_uses_claude_plugin_data_env(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: CLAUDE_PLUGIN_DATA env var is set
        Given CLAUDE_PLUGIN_DATA points to a directory
        When get_oracle_data_dir is called
        Then it returns a path under that directory
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/plugin-data/oracle")
        result = get_oracle_data_dir()
        assert result == Path("/tmp/plugin-data/oracle")

    @pytest.mark.unit
    def test_falls_back_to_home_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: CLAUDE_PLUGIN_DATA is not set
        Given no CLAUDE_PLUGIN_DATA env var
        When get_oracle_data_dir is called
        Then it returns ~/.oracle-inference
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        result = get_oracle_data_dir()
        assert result == Path.home() / ".oracle-inference"


class TestVenvPath:
    """
    Feature: Venv path resolution

    As the oracle plugin
    I want a consistent venv location
    So that the daemon can find its Python interpreter
    """

    @pytest.mark.unit
    def test_venv_under_data_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Venv path is under the data directory
        Given a data directory
        When get_venv_path is called
        Then it returns data_dir / venv
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/oracle-data")
        result = get_venv_path()
        assert result == Path("/tmp/oracle-data") / "venv"


class TestIsProvisioned:
    """
    Feature: Provisioning status check

    As the oracle daemon lifecycle hook
    I want to check if the venv is ready
    So that I only start the daemon when provisioned
    """

    @pytest.mark.unit
    def test_not_provisioned_when_no_venv(self, tmp_path: Path):
        """
        Scenario: No venv directory exists
        Given an empty data directory
        When is_provisioned is called
        Then it returns False
        """
        assert is_provisioned(tmp_path / "venv") is False

    @pytest.mark.unit
    def test_provisioned_when_python_exists(self, tmp_path: Path):
        """
        Scenario: Venv with Python binary exists
        Given a venv directory with bin/python
        When is_provisioned is called
        Then it returns True
        """
        venv = tmp_path / "venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        assert is_provisioned(venv) is True


class TestProvisionVenv:
    """
    Feature: Venv provisioning via uv

    As a user running /oracle:setup
    I want the venv and onnxruntime installed automatically
    So that I don't need to manage Python environments
    """

    @pytest.mark.unit
    def test_provision_calls_uv_with_correct_args(self, tmp_path: Path):
        """
        Scenario: Provisioning runs uv commands
        Given a target directory
        When provision_venv is called
        Then it runs uv venv and uv pip install with correct args
        """
        with patch("oracle.provision.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = provision_venv(tmp_path / "venv")
            assert result.success is True
            calls = mock_run.call_args_list
            # First call: uv venv
            assert "venv" in str(calls[0])
            # Second call: uv pip install onnxruntime
            assert "onnxruntime" in str(calls[1])

    @pytest.mark.unit
    def test_provision_fails_when_uv_missing(self, tmp_path: Path):
        """
        Scenario: uv is not installed
        Given uv is not on PATH
        When provision_venv is called
        Then it returns failure with helpful message
        """
        with patch("oracle.provision.subprocess.run", side_effect=FileNotFoundError):
            result = provision_venv(tmp_path / "venv")
            assert result.success is False
            assert "uv" in result.message.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/oracle && uv run pytest tests/unit/test_provision.py -v -o 'addopts='`

- [ ] **Step 3: Implement provisioning module**

```python
# plugins/oracle/src/oracle/provision.py
"""Venv provisioning for the oracle inference daemon."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProvisionResult:
    """Result of a provisioning attempt."""

    success: bool
    message: str


def get_oracle_data_dir() -> Path:
    """Return the oracle data directory.

    Uses $CLAUDE_PLUGIN_DATA if set, otherwise ~/.oracle-inference.
    """
    env_dir = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".oracle-inference"


def get_venv_path() -> Path:
    """Return the path to the oracle venv."""
    return get_oracle_data_dir() / "venv"


def is_provisioned(venv_path: Path) -> bool:
    """Return True if the venv has a working Python binary."""
    python = venv_path / "bin" / "python"
    if sys.platform == "win32":
        python = venv_path / "Scripts" / "python.exe"
    return python.exists()


def get_python_path(venv_path: Path) -> Path:
    """Return the path to the venv's Python binary."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def provision_venv(venv_path: Path) -> ProvisionResult:
    """Provision a Python 3.11+ venv with onnxruntime.

    Requires uv to be installed. Runs:
      uv venv --python 3.11 <path>
      uv pip install --python <path>/bin/python onnxruntime
    """
    try:
        # Create venv with Python 3.11+
        result = subprocess.run(
            ["uv", "venv", "--python", "3.11", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return ProvisionResult(
                success=False,
                message=f"Failed to create venv: {result.stderr.strip()}",
            )

        # Install onnxruntime
        python = str(get_python_path(venv_path))
        result = subprocess.run(
            ["uv", "pip", "install", "--python", python, "onnxruntime"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return ProvisionResult(
                success=False,
                message=f"Failed to install onnxruntime: {result.stderr.strip()}",
            )

        return ProvisionResult(
            success=True,
            message=f"Oracle venv provisioned at {venv_path}",
        )

    except FileNotFoundError:
        return ProvisionResult(
            success=False,
            message=(
                "uv not found. Install it first: "
                "curl -LsSf https://astral.sh/uv/install.sh | sh"
            ),
        )
    except subprocess.TimeoutExpired:
        return ProvisionResult(
            success=False,
            message="Provisioning timed out. Check your network connection.",
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/oracle && uv run pytest tests/unit/test_provision.py -v -o 'addopts='`

- [ ] **Step 5: Commit**

```bash
git add plugins/oracle/src/oracle/provision.py plugins/oracle/tests/unit/test_provision.py
git commit -m "feat(oracle): add venv provisioning with uv and onnxruntime"
```

---

## Task 3: HTTP Inference Daemon

**Files:**
- Create: `plugins/oracle/tests/unit/test_daemon.py`
- Create: `plugins/oracle/src/oracle/daemon.py`

- [ ] **Step 1: Write failing tests for the daemon**

```python
# plugins/oracle/tests/unit/test_daemon.py
"""Tests for the oracle HTTP inference daemon."""

from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from oracle.daemon import InferenceDaemon


@pytest.fixture()
def model_yaml(tmp_path: Path) -> Path:
    """Create a test model YAML."""
    content = (
        "schema_version: 1\n"
        "model_type: logistic_regression\n"
        "features:\n"
        "  - feat_a\n"
        "  - feat_b\n"
        "weights:\n"
        "  feat_a: 2.0\n"
        "  feat_b: -1.0\n"
        "intercept: 0.5\n"
        "sigmoid: true\n"
        "blend:\n"
        "  word_overlap_weight: 0.4\n"
        "  ml_weight: 0.6\n"
    )
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    model_path = models_dir / "test.yaml"
    model_path.write_text(content)
    return models_dir


@pytest.fixture()
def daemon(model_yaml: Path, tmp_path: Path):
    """Start a daemon on a random port and yield it."""
    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=model_yaml,
        port_file=tmp_path / "daemon.port",
    )
    t = threading.Thread(target=d.serve, daemon=True)
    t.start()
    # Wait for daemon to write port file
    for _ in range(50):
        if (tmp_path / "daemon.port").exists():
            break
        time.sleep(0.05)
    yield d
    d.shutdown()


def _get(daemon: InferenceDaemon, path: str) -> dict:
    """HTTP GET helper."""
    port = daemon.port
    req = Request(f"http://127.0.0.1:{port}{path}")
    with urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def _post(daemon: InferenceDaemon, path: str, body: dict) -> dict:
    """HTTP POST helper."""
    port = daemon.port
    data = json.dumps(body).encode()
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


class TestDaemonHealth:
    """
    Feature: Daemon health endpoint

    As a plugin client
    I want to check if the daemon is running
    So that I can fall back gracefully if not
    """

    @pytest.mark.unit
    def test_health_returns_ok(self, daemon: InferenceDaemon):
        """
        Scenario: Daemon is running
        Given a started daemon
        When GET /health is called
        Then status is 'ok' and models are listed
        """
        resp = _get(daemon, "/health")
        assert resp["status"] == "ok"
        assert "test" in resp["models"]


class TestDaemonInfer:
    """
    Feature: Daemon inference endpoint

    As a plugin client
    I want to send features and get a score
    So that I can use ML scoring without onnxruntime locally
    """

    @pytest.mark.unit
    def test_infer_returns_score(self, daemon: InferenceDaemon):
        """
        Scenario: Valid inference request
        Given a running daemon with a loaded model
        When POST /infer is called with features
        Then a float score is returned
        """
        resp = _post(daemon, "/infer", {
            "model": "test",
            "features": {"feat_a": 1.0, "feat_b": 0.5},
        })
        expected = 1.0 / (1.0 + math.exp(-2.0))
        assert abs(resp["score"] - expected) < 1e-6

    @pytest.mark.unit
    def test_infer_unknown_model_returns_error(self, daemon: InferenceDaemon):
        """
        Scenario: Unknown model name
        Given a running daemon
        When POST /infer is called with a nonexistent model name
        Then an error is returned
        """
        resp = _post(daemon, "/infer", {
            "model": "nonexistent",
            "features": {"feat_a": 1.0},
        })
        assert "error" in resp

    @pytest.mark.unit
    def test_infer_missing_body_returns_error(self, daemon: InferenceDaemon):
        """
        Scenario: Malformed request body
        Given a running daemon
        When POST /infer is called with empty body
        Then an error is returned
        """
        port = daemon.port
        req = Request(
            f"http://127.0.0.1:{port}/infer",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
        assert "error" in result


class TestDaemonPortFile:
    """
    Feature: Daemon port file for service discovery

    As another plugin
    I want to discover the daemon's port
    So that I can connect without configuration
    """

    @pytest.mark.unit
    def test_port_file_written_on_start(self, daemon: InferenceDaemon, tmp_path: Path):
        """
        Scenario: Daemon writes port file on startup
        Given a daemon configured with a port file path
        When the daemon starts
        Then the port file contains the actual port number
        """
        port_file = tmp_path / "daemon.port"
        assert port_file.exists()
        written_port = int(port_file.read_text().strip())
        assert written_port == daemon.port
        assert written_port > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/oracle && uv run pytest tests/unit/test_daemon.py -v -o 'addopts='`

- [ ] **Step 3: Implement the daemon**

```python
# plugins/oracle/src/oracle/daemon.py
"""HTTP inference daemon for the oracle plugin.

Serves model inference over localhost HTTP. Designed to run
inside a uv-provisioned Python 3.11+ venv with onnxruntime.
For Phase 2, uses YamlScorer (same as gauntlet) to prove
the architecture. Phase 2b adds ONNX Runtime sessions.

Usage (from the venv):
    python -m oracle.daemon --models-dir /path/to/models --port-file /path/to/daemon.port
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event
from typing import Any

import yaml


class _ModelRegistry:
    """Loads and caches YAML-based models from a directory."""

    def __init__(self, models_dir: Path) -> None:
        self._models: dict[str, dict[str, Any]] = {}
        self._load_models(models_dir)

    def _load_models(self, models_dir: Path) -> None:
        """Load all .yaml model files from the directory."""
        if not models_dir.is_dir():
            return
        for path in sorted(models_dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "weights" in data:
                    name = path.stem
                    self._models[name] = data
            except (OSError, yaml.YAMLError):
                continue

    def list_models(self) -> list[str]:
        """Return names of loaded models."""
        return list(self._models.keys())

    def infer(self, model_name: str, features: dict[str, float]) -> float:
        """Run inference on the named model."""
        model = self._models[model_name]
        weights = model.get("weights", {})
        intercept = float(model.get("intercept", 0.0))
        use_sigmoid = bool(model.get("sigmoid", True))

        linear = sum(
            float(w) * features.get(name, 0.0)
            for name, w in weights.items()
        )
        linear += intercept

        if use_sigmoid:
            import math
            clamped = max(-500.0, min(500.0, linear))
            return 1.0 / (1.0 + math.exp(-clamped))
        return linear


class _InferenceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for inference endpoints."""

    server: _InferenceServer

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._respond(200, {
                "status": "ok",
                "models": self.server.registry.list_models(),
            })
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        if self.path == "/infer":
            self._handle_infer()
        else:
            self._respond(404, {"error": "not found"})

    def _handle_infer(self) -> None:
        """Process an inference request."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            self._respond(400, {"error": "invalid JSON"})
            return

        model_name = body.get("model", "")
        features = body.get("features", {})

        if not model_name:
            self._respond(400, {"error": "missing 'model' field"})
            return

        if model_name not in self.server.registry.list_models():
            self._respond(404, {"error": f"unknown model: {model_name}"})
            return

        try:
            score = self.server.registry.infer(model_name, features)
            self._respond(200, {"score": score})
        except Exception as exc:
            self._respond(500, {"error": str(exc)})

    def _respond(self, code: int, body: dict[str, Any]) -> None:
        """Send a JSON response."""
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr logging."""


class _InferenceServer(HTTPServer):
    """HTTPServer subclass that holds the model registry."""

    def __init__(
        self,
        server_address: tuple[str, int],
        registry: _ModelRegistry,
    ) -> None:
        self.registry = registry
        super().__init__(server_address, _InferenceHandler)


class InferenceDaemon:
    """Manages the inference HTTP server lifecycle."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        models_dir: Path = Path("."),
        port_file: Path = Path("daemon.port"),
    ) -> None:
        self._host = host
        self._port = port
        self._models_dir = models_dir
        self._port_file = port_file
        self._server: _InferenceServer | None = None
        self._shutdown_event = Event()

    @property
    def port(self) -> int:
        """Return the actual port the server is listening on."""
        if self._server is not None:
            return self._server.server_address[1]
        return self._port

    def serve(self) -> None:
        """Start serving. Blocks until shutdown() is called."""
        registry = _ModelRegistry(self._models_dir)
        self._server = _InferenceServer(
            (self._host, self._port), registry,
        )
        # Write port file for service discovery
        actual_port = self._server.server_address[1]
        self._port_file.parent.mkdir(parents=True, exist_ok=True)
        self._port_file.write_text(str(actual_port))

        self._server.serve_forever()

    def shutdown(self) -> None:
        """Stop the server and clean up the port file."""
        if self._server is not None:
            self._server.shutdown()
        if self._port_file.exists():
            self._port_file.unlink()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Oracle inference daemon")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--models-dir", type=Path, required=True)
    parser.add_argument("--port-file", type=Path, required=True)
    args = parser.parse_args()

    daemon = InferenceDaemon(
        host=args.host,
        port=args.port,
        models_dir=args.models_dir,
        port_file=args.port_file,
    )
    try:
        daemon.serve()
    except KeyboardInterrupt:
        daemon.shutdown()
        sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/oracle && uv run pytest tests/unit/test_daemon.py -v -o 'addopts='`

- [ ] **Step 5: Commit**

```bash
git add plugins/oracle/src/oracle/daemon.py plugins/oracle/tests/unit/test_daemon.py
git commit -m "feat(oracle): add HTTP inference daemon with model registry"
```

---

## Task 4: Client Module

**Files:**
- Create: `plugins/oracle/tests/unit/test_client.py`
- Create: `plugins/oracle/src/oracle/client.py`

- [ ] **Step 1: Write failing tests for the client**

```python
# plugins/oracle/tests/unit/test_client.py
"""Tests for the oracle inference client."""

from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from oracle.client import OracleClient
from oracle.daemon import InferenceDaemon


@pytest.fixture()
def running_daemon(tmp_path: Path):
    """Start a daemon with a test model and return client config."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "quality_v1.yaml").write_text(
        "schema_version: 1\n"
        "model_type: logistic_regression\n"
        "features:\n"
        "  - feat_a\n"
        "weights:\n"
        "  feat_a: 1.0\n"
        "intercept: 0.0\n"
        "sigmoid: true\n"
        "blend:\n"
        "  word_overlap_weight: 0.4\n"
        "  ml_weight: 0.6\n"
    )
    port_file = tmp_path / "daemon.port"
    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=models_dir,
        port_file=port_file,
    )
    t = threading.Thread(target=d.serve, daemon=True)
    t.start()
    for _ in range(50):
        if port_file.exists():
            break
        time.sleep(0.05)
    yield {"port_file": port_file, "daemon": d}
    d.shutdown()


class TestOracleClient:
    """
    Feature: Oracle inference client

    As a plugin (like gauntlet)
    I want a simple client to call the oracle daemon
    So that I can get ML scores without importing onnxruntime
    """

    @pytest.mark.unit
    def test_is_available_when_daemon_running(self, running_daemon: dict):
        """
        Scenario: Daemon is running and healthy
        Given a running oracle daemon
        When OracleClient checks availability
        Then it returns True
        """
        client = OracleClient(running_daemon["port_file"])
        assert client.is_available() is True

    @pytest.mark.unit
    def test_not_available_when_no_port_file(self, tmp_path: Path):
        """
        Scenario: No daemon running (no port file)
        Given no port file exists
        When OracleClient checks availability
        Then it returns False
        """
        client = OracleClient(tmp_path / "nonexistent.port")
        assert client.is_available() is False

    @pytest.mark.unit
    def test_infer_returns_score(self, running_daemon: dict):
        """
        Scenario: Successful inference call
        Given a running daemon with quality_v1 model
        When infer is called with features
        Then a float score is returned
        """
        client = OracleClient(running_daemon["port_file"])
        score = client.infer("quality_v1", {"feat_a": 1.0})
        assert score is not None
        expected = 1.0 / (1.0 + math.exp(-1.0))
        assert abs(score - expected) < 1e-6

    @pytest.mark.unit
    def test_infer_returns_none_when_unavailable(self, tmp_path: Path):
        """
        Scenario: Daemon not running
        Given no daemon available
        When infer is called
        Then None is returned (graceful degradation)
        """
        client = OracleClient(tmp_path / "nonexistent.port")
        assert client.infer("quality_v1", {"feat_a": 1.0}) is None

    @pytest.mark.unit
    def test_infer_returns_none_on_timeout(self, running_daemon: dict):
        """
        Scenario: Daemon is slow or unresponsive
        Given a running daemon
        When infer times out
        Then None is returned
        """
        client = OracleClient(running_daemon["port_file"], timeout=0.001)
        # With such a tiny timeout, may or may not fail depending on speed
        # Just verify it doesn't raise
        result = client.infer("quality_v1", {"feat_a": 1.0})
        assert result is None or isinstance(result, float)
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement the client**

```python
# plugins/oracle/src/oracle/client.py
"""Lightweight HTTP client for the oracle inference daemon.

This module runs on Python 3.9 (system Python) and uses only
stdlib urllib. It is designed to be imported by other plugins
(like gauntlet) to communicate with the oracle daemon.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


class OracleClient:
    """Client for the oracle inference daemon.

    Discovers the daemon via a port file written at startup.
    All methods return None on failure (graceful degradation).
    """

    def __init__(
        self, port_file: Path, timeout: float = 5.0,
    ) -> None:
        self._port_file = port_file
        self._timeout = timeout
        self._base_url: Optional[str] = None

    def _resolve_url(self) -> Optional[str]:
        """Read the port file and return the base URL."""
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
        """Check if the daemon is running and healthy."""
        base = self._resolve_url()
        if base is None:
            return False
        try:
            req = Request(f"{base}/health")
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                return data.get("status") == "ok"
        except (URLError, OSError, json.JSONDecodeError):
            # Daemon not reachable -- clear cached URL
            self._base_url = None
            return False

    def infer(
        self, model: str, features: dict[str, float],
    ) -> Optional[float]:
        """Send features to the daemon and return a score.

        Returns None if the daemon is unavailable or returns
        an error. Never raises exceptions.
        """
        base = self._resolve_url()
        if base is None:
            return None
        try:
            body = json.dumps({"model": model, "features": features}).encode()
            req = Request(
                f"{base}/infer",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                if "score" in data:
                    return float(data["score"])
                return None
        except (URLError, OSError, json.JSONDecodeError, ValueError):
            self._base_url = None
            return None
```

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**

```bash
git add plugins/oracle/src/oracle/client.py plugins/oracle/tests/unit/test_client.py
git commit -m "feat(oracle): add HTTP client with graceful degradation"
```

---

## Task 5: Daemon Lifecycle Hook

**Files:**
- Create: `plugins/oracle/hooks/daemon_lifecycle.py`

- [ ] **Step 1: Implement the lifecycle hook**

```python
#!/usr/bin/env python3
"""Oracle daemon lifecycle hook.

SessionStart: Start the daemon if venv is provisioned.
Stop: Stop the daemon and clean up the port file.

This hook runs on system Python 3.9. It spawns the daemon
as a subprocess using the venv's Python 3.11+.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _get_data_dir() -> Path:
    """Return the oracle data directory."""
    env_dir = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".oracle-inference"


def _get_venv_python() -> Path:
    """Return the venv Python path."""
    data_dir = _get_data_dir()
    if sys.platform == "win32":
        return data_dir / "venv" / "Scripts" / "python.exe"
    return data_dir / "venv" / "bin" / "python"


def _get_port_file() -> Path:
    """Return the daemon port file path."""
    return _get_data_dir() / "daemon.port"


def _get_pid_file() -> Path:
    """Return the daemon PID file path."""
    return _get_data_dir() / "daemon.pid"


def _get_models_dir() -> Path:
    """Return the models directory.

    Uses the gauntlet plugin's models if available,
    otherwise uses the oracle data dir.
    """
    # Look for gauntlet's models relative to this hook
    hook_dir = Path(__file__).resolve().parent
    gauntlet_models = (
        hook_dir.parent.parent
        / "gauntlet"
        / "src"
        / "gauntlet"
        / "ml"
        / "models"
    )
    if gauntlet_models.is_dir():
        return gauntlet_models
    # Fallback to oracle data dir
    models = _get_data_dir() / "models"
    models.mkdir(parents=True, exist_ok=True)
    return models


def _is_daemon_running() -> bool:
    """Check if the daemon process is still alive."""
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # Signal 0 = check if alive
        return True
    except (OSError, ValueError):
        # Process not found or bad PID
        pid_file.unlink(missing_ok=True)
        return False


def _start_daemon() -> None:
    """Start the daemon subprocess."""
    venv_python = _get_venv_python()
    if not venv_python.exists():
        # Not provisioned -- silently skip
        return

    port_file = _get_port_file()
    pid_file = _get_pid_file()
    models_dir = _get_models_dir()

    if _is_daemon_running():
        return

    # Clean up stale port file
    if port_file.exists():
        port_file.unlink()

    # Start daemon as detached subprocess
    daemon_module = Path(__file__).resolve().parent.parent / "src" / "oracle" / "daemon.py"
    proc = subprocess.Popen(
        [
            str(venv_python),
            str(daemon_module),
            "--models-dir", str(models_dir),
            "--port-file", str(port_file),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Write PID file
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(proc.pid))


def _stop_daemon() -> None:
    """Stop the daemon subprocess."""
    pid_file = _get_pid_file()
    port_file = _get_port_file()

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 15)  # SIGTERM
        except (OSError, ValueError):
            pass
        pid_file.unlink(missing_ok=True)

    if port_file.exists():
        port_file.unlink(missing_ok=True)


def main() -> None:
    """Hook entry point. Dispatches on event type."""
    event = os.environ.get("CLAUDE_HOOK_EVENT", "")

    if event == "SessionStart":
        _start_daemon()
    elif event == "Stop":
        _stop_daemon()

    # Always exit cleanly -- never block the session
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add plugins/oracle/hooks/daemon_lifecycle.py
git commit -m "feat(oracle): add SessionStart/Stop daemon lifecycle hook"
```

---

## Task 6: Setup Skill and Command

**Files:**
- Create: `plugins/oracle/skills/setup/SKILL.md`
- Create: `plugins/oracle/commands/oracle-setup.md`

- [ ] **Step 1: Create the setup skill**

```markdown
# plugins/oracle/skills/setup/SKILL.md
---
name: setup
description: Provision the oracle inference daemon venv with Python 3.11+ and onnxruntime
---

# Oracle Setup

Provision the ML inference environment for the oracle plugin.

## What This Does

1. Creates a Python 3.11+ virtual environment using `uv`
2. Installs `onnxruntime` into the venv
3. Verifies the installation works

## Prerequisites

- `uv` must be installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Internet connection (for downloading Python and onnxruntime)

## Steps

1. Run the provisioning script:

\```bash
cd plugins/oracle && uv run python -c "
from oracle.provision import provision_venv, get_venv_path
result = provision_venv(get_venv_path())
print(result.message)
"
\```

2. Verify the daemon starts:

\```bash
# The daemon will start automatically on next session.
# To test now, check the health endpoint after restarting:
# curl http://127.0.0.1:$(cat $CLAUDE_PLUGIN_DATA/daemon.port)/health
\```

3. Report the result to the user.

If provisioning fails, show the error message and suggest
checking `uv` installation and network connectivity.
```

- [ ] **Step 2: Create the command**

```markdown
# plugins/oracle/commands/oracle-setup.md
---
description: Provision the oracle ML inference daemon with Python 3.11+ and onnxruntime
---

# Oracle Setup

Run `Skill(oracle:setup)` to provision the inference environment.

This downloads Python 3.11+ and onnxruntime (~65MB total).
The daemon will start automatically on your next session.

Arguments: none
```

- [ ] **Step 3: Commit**

```bash
git add plugins/oracle/skills/ plugins/oracle/commands/
git commit -m "feat(oracle): add /oracle:setup command for user-initiated provisioning"
```

---

## Task 7: Wire Gauntlet to Detect Oracle

**Files:**
- Create: `plugins/gauntlet/tests/unit/test_sidecar_scorer.py`
- Modify: `plugins/gauntlet/src/gauntlet/ml/scorer.py`
- Modify: `plugins/gauntlet/src/gauntlet/ml/__init__.py`

- [ ] **Step 1: Write failing tests for OnnxSidecarScorer**

```python
# plugins/gauntlet/tests/unit/test_sidecar_scorer.py
"""Tests for the OnnxSidecarScorer (oracle daemon client)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gauntlet.ml.scorer import OnnxSidecarScorer


class TestOnnxSidecarScorer:
    """
    Feature: Oracle sidecar scorer for gauntlet

    As the gauntlet scoring module
    I want to use the oracle daemon for inference
    So that I can benefit from ONNX Runtime without local deps
    """

    @pytest.mark.unit
    def test_not_available_when_no_port_file(self, tmp_path: Path):
        """
        Scenario: Oracle not installed or not provisioned
        Given no port file exists
        When available() is called
        Then it returns False
        """
        scorer = OnnxSidecarScorer(tmp_path / "nonexistent.port")
        assert scorer.available() is False

    @pytest.mark.unit
    def test_score_returns_zero_when_unavailable(self, tmp_path: Path):
        """
        Scenario: Oracle unavailable returns 0.0
        Given no oracle daemon running
        When score is called
        Then it returns 0.0
        """
        scorer = OnnxSidecarScorer(tmp_path / "nonexistent.port")
        assert scorer.score({"feat_a": 1.0}) == 0.0

    @pytest.mark.unit
    def test_available_when_daemon_healthy(self, tmp_path: Path):
        """
        Scenario: Oracle daemon is running and healthy
        Given a port file and a healthy daemon
        When available() is called
        Then it returns True
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok", "models": ["quality_v1"]}'
            mock_resp.__enter__ = lambda s: mock_resp
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            scorer = OnnxSidecarScorer(port_file)
            assert scorer.available() is True

    @pytest.mark.unit
    def test_score_calls_daemon_infer(self, tmp_path: Path):
        """
        Scenario: Score delegates to daemon /infer endpoint
        Given a healthy oracle daemon
        When score is called with features
        Then it returns the daemon's score
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"score": 0.87}'
            mock_resp.__enter__ = lambda s: mock_resp
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            scorer = OnnxSidecarScorer(port_file)
            result = scorer.score({"feat_a": 1.0})
            assert result == pytest.approx(0.87)

    @pytest.mark.unit
    def test_blend_weights_default(self, tmp_path: Path):
        """
        Scenario: Blend weights default to 0.4/0.6
        Given a sidecar scorer
        When blend_weights is accessed
        Then it returns (0.4, 0.6)
        """
        scorer = OnnxSidecarScorer(tmp_path / "nonexistent.port")
        assert scorer.blend_weights == (0.4, 0.6)
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Add OnnxSidecarScorer to scorer.py**

Append to the end of `plugins/gauntlet/src/gauntlet/ml/scorer.py`:

```python
# --- Phase 2: Oracle sidecar scorer ---

import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


class OnnxSidecarScorer:
    """Delegates inference to the oracle daemon over HTTP.

    Discovers the daemon via a port file. Returns 0.0 and
    reports unavailable when the daemon is not running.
    """

    def __init__(
        self,
        port_file: Path,
        model: str = "quality_v1",
        timeout: float = 2.0,
    ) -> None:
        self._port_file = port_file
        self._model = model
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

    def available(self) -> bool:
        """Check if the oracle daemon is running and healthy."""
        base = self._resolve_url()
        if base is None:
            return False
        try:
            req = Request(f"{base}/health")
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                return data.get("status") == "ok"
        except (URLError, OSError, json.JSONDecodeError):
            self._base_url = None
            return False

    def score(self, features: dict[str, float]) -> float:
        """Send features to the daemon and return a score."""
        base = self._resolve_url()
        if base is None:
            return 0.0
        try:
            body = json.dumps({
                "model": self._model,
                "features": features,
            }).encode()
            req = Request(
                f"{base}/infer",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                return float(data.get("score", 0.0))
        except (URLError, OSError, json.JSONDecodeError, ValueError):
            self._base_url = None
            return 0.0

    @property
    def blend_weights(self) -> tuple[float, float]:
        """Return default blend weights."""
        return (0.4, 0.6)
```

- [ ] **Step 4: Update gauntlet ml/__init__.py to try oracle first**

Replace `_get_scorer()` in `plugins/gauntlet/src/gauntlet/ml/__init__.py`:

```python
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from gauntlet.ml.features import extract_answer_features
from gauntlet.ml.scorer import OnnxSidecarScorer, YamlScorer

if TYPE_CHECKING:
    from gauntlet.ml.scorer import Scorer
    from gauntlet.models import Challenge

_MODEL_PATH = str(
    Path(__file__).parent / "models" / "quality_v1.yaml"
)

_scorer: Optional[YamlScorer | OnnxSidecarScorer] = None


def _get_oracle_port_file() -> Optional[Path]:
    """Find the oracle daemon's port file if it exists."""
    # Check CLAUDE_PLUGIN_DATA first (standard location)
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if plugin_data:
        # CLAUDE_PLUGIN_DATA is per-plugin; oracle's is a sibling
        oracle_port = Path(plugin_data).parent / "oracle" / "daemon.port"
        if oracle_port.exists():
            return oracle_port
    # Check fallback location
    fallback = Path.home() / ".oracle-inference" / "daemon.port"
    if fallback.exists():
        return fallback
    return None


def _get_scorer() -> "Scorer":
    """Lazy-initialize the scorer. Tries oracle sidecar first."""
    global _scorer
    if _scorer is not None:
        return _scorer

    # Try oracle sidecar
    port_file = _get_oracle_port_file()
    if port_file is not None:
        sidecar = OnnxSidecarScorer(port_file)
        if sidecar.available():
            _scorer = sidecar
            return _scorer

    # Fall back to YAML scorer
    _scorer = YamlScorer(_MODEL_PATH)
    return _scorer
```

Keep the existing `score_answer_quality()` and `get_blend_weights()` unchanged -- they call `_get_scorer()` which now auto-upgrades.

- [ ] **Step 5: Run full gauntlet test suite**

Run: `cd plugins/gauntlet && uv run pytest tests/ -v -o 'addopts='`

Expected: All 157+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/ml/scorer.py plugins/gauntlet/src/gauntlet/ml/__init__.py plugins/gauntlet/tests/unit/test_sidecar_scorer.py
git commit -m "feat(gauntlet): auto-detect oracle sidecar and upgrade scoring

Gauntlet now checks for the oracle daemon's port file on
startup. If found and healthy, scoring uses the sidecar.
If not, falls back to YamlScorer. Zero errors either way."
```

---

## Verification Checklist

After all tasks complete:

- [ ] Oracle plugin structure validates (`plugin.json` schema correct)
- [ ] Oracle daemon starts, serves /health and /infer
- [ ] Oracle client discovers daemon via port file
- [ ] Gauntlet detects oracle when available, falls back when not
- [ ] All gauntlet tests pass (157+) with oracle NOT running
- [ ] Oracle tests pass independently
- [ ] No new dependencies in gauntlet's `pyproject.toml`
- [ ] No errors when oracle is uninstalled
- [ ] `/oracle:setup` provisions venv correctly
- [ ] Hook starts daemon only when venv exists (no errors otherwise)

## Marketplace Safety Verification

- [ ] Fresh install of oracle: no downloads, no errors, no processes
- [ ] `/oracle:setup` is the only trigger for downloads
- [ ] Uninstall oracle: gauntlet scoring unchanged
- [ ] oracle without gauntlet: daemon serves but no consumer (harmless)
