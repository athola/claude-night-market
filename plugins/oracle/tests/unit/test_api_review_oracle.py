"""Regression tests for verified API-review findings in oracle."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from oracle.client import OracleClient
from oracle.daemon import InferenceDaemon


@pytest.fixture
def live_daemon(tmp_path: Path):
    models = tmp_path / "models"
    models.mkdir()
    (models / "m.yaml").write_text("weights: {a: 1.0}\nintercept: 0.0\n")
    daemon = InferenceDaemon(models_dir=models, port_file=tmp_path / "port")
    thread = threading.Thread(target=daemon.serve_forever, daemon=True)
    thread.start()
    yield daemon
    daemon.shutdown()


def _post(port: int, body: bytes) -> tuple[int, dict]:
    req = Request(
        f"http://127.0.0.1:{port}/infer",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=5) as resp:  # noqa: S310 - fixed http URL to the local test daemon
            return resp.status, json.loads(resp.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_non_object_json_body_gets_400(live_daemon: InferenceDaemon):
    status, body = _post(live_daemon.port, b"[1]")
    assert status == 400
    assert "JSON object" in body["error"]


def test_empty_model_yaml_fails_at_startup(tmp_path: Path):
    models = tmp_path / "models"
    models.mkdir()
    (models / "empty.yaml").write_text("")
    with pytest.raises(ValueError, match="empty"):
        InferenceDaemon(models_dir=models)


def test_missing_models_dir_fails_at_startup(tmp_path: Path):
    with pytest.raises(ValueError, match="models"):
        InferenceDaemon(models_dir=tmp_path / "nope")


def test_client_keeps_base_url_after_http_error(
    live_daemon: InferenceDaemon, tmp_path: Path
):
    client = OracleClient(tmp_path / "port")
    assert client.infer("unknown", {}) is None
    assert client._base_url is not None
