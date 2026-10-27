"""Regression tests for defects found in the 2026-10 bug review."""

from __future__ import annotations

import io
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from daemon_lifecycle import _get_event

from oracle.daemon import InferenceDaemon

MODEL = "weights:\n  a: 1.0\nintercept: 0.0\nsigmoid: true\n"


@pytest.mark.unit
@pytest.mark.parametrize("payload", ["null", "[]", '"Stop"', "3"])
def test_get_event_survives_non_object_payload(monkeypatch, payload: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))

    assert _get_event() == ""


@pytest.mark.unit
def test_get_event_survives_undecodable_stdin(monkeypatch) -> None:
    stdin = io.TextIOWrapper(io.BytesIO(b"\xff\xfe\x00"), encoding="utf-8")
    monkeypatch.setattr("sys.stdin", stdin)

    assert _get_event() == ""


def _post(port: int, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/infer",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as reply:
            return reply.status, json.loads(reply.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


@pytest.fixture
def daemon(tmp_path: Path):
    (tmp_path / "m.yaml").write_text(MODEL)
    server = InferenceDaemon(models_dir=tmp_path)
    thread = threading.Thread(target=server._server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.mark.unit
@pytest.mark.parametrize("model", [["m"], {"m": 1}, 7])
def test_infer_answers_400_for_non_string_model(daemon, model) -> None:
    status, _ = _post(daemon.port, {"model": model, "features": {"a": 1}})

    assert status == 400


@pytest.mark.unit
def test_infer_rejects_non_finite_feature(daemon) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{daemon.port}/infer",
        data=b'{"model": "m", "features": {"a": NaN}}',
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(request, timeout=5)

    assert caught.value.code == 400
