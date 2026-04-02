"""Integration tests for oracle HTTP inference daemon."""

from __future__ import annotations

import json
import math
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from oracle.daemon import InferenceDaemon

TEST_MODEL_YAML = """\
schema_version: 1
model_type: logistic_regression
features:
  - feat_a
  - feat_b
weights:
  feat_a: 2.0
  feat_b: -1.0
intercept: 0.5
sigmoid: true
blend:
  word_overlap_weight: 0.4
  ml_weight: 0.6
"""

LINEAR_MODEL_YAML = """\
schema_version: 1
model_type: linear_regression
features:
  - feat_a
weights:
  feat_a: 3.0
intercept: 1.0
sigmoid: false
"""

ZERO_BLEND_MODEL_YAML = """\
schema_version: 1
model_type: logistic_regression
features:
  - feat_a
weights:
  feat_a: 1.0
intercept: 0.0
sigmoid: true
blend:
  word_overlap_weight: 0.0
  ml_weight: 0.0
"""


@pytest.fixture
def daemon_with_linear(tmp_path: Path):
    """Start a daemon that also exposes a non-sigmoid linear model."""
    models_dir = tmp_path / "models_linear"
    models_dir.mkdir()
    (models_dir / "test.yaml").write_text(TEST_MODEL_YAML)
    (models_dir / "linear.yaml").write_text(LINEAR_MODEL_YAML)

    port_file = tmp_path / "oracle_linear.port"
    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=models_dir,
        port_file=port_file,
    )
    t = threading.Thread(target=d.serve_forever, daemon=True)
    t.start()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if port_file.exists() and port_file.read_text().strip():
            break
        time.sleep(0.05)
    yield d
    d.shutdown()
    t.join(timeout=5.0)


@pytest.fixture
def daemon_no_port_file(tmp_path: Path):
    """Start a daemon with no port file (port_file=None path)."""
    models_dir = tmp_path / "models_nopf"
    models_dir.mkdir()
    (models_dir / "test.yaml").write_text(TEST_MODEL_YAML)

    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=models_dir,
        port_file=None,
    )
    t = threading.Thread(target=d.serve_forever, daemon=True)
    t.start()
    # Give it a moment to bind
    time.sleep(0.15)
    yield d
    d.shutdown()
    t.join(timeout=5.0)


@pytest.fixture
def daemon_with_zero_blend(tmp_path: Path):
    """Start a daemon with a model whose blend weights both equal zero."""
    models_dir = tmp_path / "models_zero_blend"
    models_dir.mkdir()
    (models_dir / "zeroblend.yaml").write_text(ZERO_BLEND_MODEL_YAML)

    port_file = tmp_path / "oracle_zero_blend.port"
    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=models_dir,
        port_file=port_file,
    )
    t = threading.Thread(target=d.serve_forever, daemon=True)
    t.start()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if port_file.exists() and port_file.read_text().strip():
            break
        time.sleep(0.05)
    yield d
    d.shutdown()
    t.join(timeout=5.0)


@pytest.fixture
def daemon_instance(tmp_path: Path):
    """
    Start an InferenceDaemon on a random port in a daemon thread.

    Yields the running daemon and shuts it down on cleanup.
    """
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "test.yaml").write_text(TEST_MODEL_YAML)

    port_file = tmp_path / "oracle.port"

    d = InferenceDaemon(
        host="127.0.0.1",
        port=0,
        models_dir=models_dir,
        port_file=port_file,
    )

    t = threading.Thread(target=d.serve_forever, daemon=True)
    t.start()

    # Wait for port file to be written with content (not just created)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if port_file.exists() and port_file.read_text().strip():
            break
        time.sleep(0.05)

    yield d

    d.shutdown()
    t.join(timeout=5.0)


class TestHealthEndpoint:
    """
    Feature: Health check endpoint

    As a caller
    I want GET /health to confirm the daemon is alive and list loaded models
    So that I can verify the daemon is ready before sending inference requests
    """

    @pytest.mark.integration
    def test_health_returns_ok_and_model_list(self, daemon_instance: InferenceDaemon):
        """
        Scenario: Daemon is running with one model loaded
        Given a daemon started with a single 'test' model
        When GET /health is called
        Then the response is 200 with status ok and models list ['test']
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310 - localhost-only test server
            body = json.loads(resp.read())

        assert resp.status == 200
        assert body["status"] == "ok"
        assert body["models"] == ["test"]


class TestInferEndpoint:
    """
    Feature: Inference endpoint

    As a caller
    I want POST /infer to run a logistic regression model against supplied features
    So that I can obtain a probability score for a candidate
    """

    @pytest.mark.integration
    def test_valid_infer_returns_score(self, daemon_instance: InferenceDaemon):
        """
        Scenario: Valid model name and feature dict supplied
        Given the 'test' model with weights feat_a=2.0, feat_b=-1.0, intercept=0.5
        When POST /infer is sent with feat_a=1.0, feat_b=1.0
        Then the response contains a 'score' equal to sigmoid(2.0 - 1.0 + 0.5)
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/infer"
        payload = json.dumps(
            {"model": "test", "features": {"feat_a": 1.0, "feat_b": 1.0}}
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310 - localhost-only test server
            body = json.loads(resp.read())

        # linear = 2.0*1.0 + (-1.0)*1.0 + 0.5 = 1.5
        expected = 1.0 / (1.0 + math.exp(-1.5))
        assert resp.status == 200
        assert "score" in body
        assert abs(body["score"] - expected) < 1e-9
        # Blend weights from the model YAML (0.4 / 0.6)
        assert "blend" in body
        assert abs(body["blend"]["word_overlap_weight"] - 0.4) < 1e-9
        assert abs(body["blend"]["ml_weight"] - 0.6) < 1e-9

    @pytest.mark.integration
    def test_unknown_model_returns_error(self, daemon_instance: InferenceDaemon):
        """
        Scenario: Caller requests a model that was never loaded
        Given only the 'test' model is available
        When POST /infer is sent with model='nonexistent'
        Then the response is 404 and contains an 'error' field
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/infer"
        payload = json.dumps(
            {"model": "nonexistent", "features": {"feat_a": 1.0}}
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)  # nosec B310 - localhost-only test server

        assert exc_info.value.code == 404
        body = json.loads(exc_info.value.read())
        assert "error" in body

    @pytest.mark.integration
    def test_empty_body_returns_error(self, daemon_instance: InferenceDaemon):
        """
        Scenario: POST /infer is called with an empty request body
        Given the daemon is running
        When POST /infer is sent with no body
        Then the response is 400 and contains an 'error' field
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/infer"
        req = urllib.request.Request(
            url,
            data=b"",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)  # nosec B310 - localhost-only test server

        assert exc_info.value.code == 400
        body = json.loads(exc_info.value.read())
        assert "error" in body


class TestPortFile:
    """
    Feature: Port file written on startup

    As a client process
    I want to read the port file to discover which port the daemon bound to
    So that I do not need a hardcoded port
    """

    @pytest.mark.integration
    def test_port_file_contains_correct_port(
        self, daemon_instance: InferenceDaemon, tmp_path: Path
    ):
        """
        Scenario: Daemon has started successfully
        Given the daemon bound to a random port
        When the port file is read
        Then it contains only the port number as text
        """
        port_file = daemon_instance.port_file
        assert port_file.exists()
        written_port = int(port_file.read_text().strip())
        assert written_port == daemon_instance.port


class TestLinearModel:
    """
    Feature: Non-sigmoid linear regression model

    As a caller
    I want POST /infer to return a raw linear score when sigmoid is false
    So that I can use the daemon with regression models too
    """

    @pytest.mark.integration
    def test_linear_model_returns_raw_score(self, daemon_with_linear: InferenceDaemon):
        """
        Scenario: Model has sigmoid=false
        Given the 'linear' model with weight feat_a=3.0 and intercept=1.0
        When POST /infer is sent with feat_a=2.0
        Then the response score equals 3.0*2.0 + 1.0 = 7.0 (no sigmoid)
        """
        port = daemon_with_linear.port
        url = f"http://127.0.0.1:{port}/infer"
        payload = json.dumps({"model": "linear", "features": {"feat_a": 2.0}}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310 - localhost-only test server
            body = json.loads(resp.read())

        assert resp.status == 200
        assert abs(body["score"] - 7.0) < 1e-9
        # Linear model has no blend config, so defaults to 0.5/0.5
        assert "blend" in body
        assert abs(body["blend"]["word_overlap_weight"] - 0.5) < 1e-9
        assert abs(body["blend"]["ml_weight"] - 0.5) < 1e-9


class TestEdgeCasePaths:
    """
    Feature: Error handling for malformed requests

    As a caller
    I want descriptive errors for bad paths and payloads
    So that I can debug integration issues quickly
    """

    @pytest.mark.integration
    def test_get_unknown_path_returns_404(self, daemon_instance: InferenceDaemon):
        """
        Scenario: GET request to an unknown path
        Given the daemon is running
        When GET /unknown is called
        Then the response is 404
        """
        port = daemon_instance.port
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/unknown", timeout=5)  # nosec B310 - localhost-only test server
        assert exc_info.value.code == 404

    @pytest.mark.integration
    def test_post_to_unknown_path_returns_404(self, daemon_instance: InferenceDaemon):
        """
        Scenario: POST request to an unknown path
        Given the daemon is running
        When POST /unknown is called
        Then the response is 404
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/unknown"
        req = urllib.request.Request(
            url,
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)  # nosec B310 - localhost-only test server
        assert exc_info.value.code == 404

    @pytest.mark.integration
    def test_invalid_json_body_returns_400(self, daemon_instance: InferenceDaemon):
        """
        Scenario: POST /infer with malformed JSON
        Given the daemon is running
        When POST /infer is sent with non-JSON bytes
        Then the response is 400 with an error field
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/infer"
        req = urllib.request.Request(
            url,
            data=b"not-json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)  # nosec B310 - localhost-only test server
        assert exc_info.value.code == 400
        body = json.loads(exc_info.value.read())
        assert "error" in body

    @pytest.mark.integration
    def test_missing_model_field_returns_400(self, daemon_instance: InferenceDaemon):
        """
        Scenario: POST /infer with JSON that omits the 'model' key
        Given the daemon is running
        When POST /infer is sent without a model field
        Then the response is 400 with an error field
        """
        port = daemon_instance.port
        url = f"http://127.0.0.1:{port}/infer"
        payload = json.dumps({"features": {"feat_a": 1.0}}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)  # nosec B310 - localhost-only test server
        assert exc_info.value.code == 400
        body = json.loads(exc_info.value.read())
        assert "error" in body


class TestNoPortFile:
    """
    Feature: Daemon can start without writing a port file

    As an operator
    I want to run the daemon without a port file
    So that I can use it in environments where file I/O for discovery is not needed
    """

    @pytest.mark.integration
    def test_daemon_starts_without_port_file(
        self, daemon_no_port_file: InferenceDaemon
    ):
        """
        Scenario: Daemon started with port_file=None
        Given a daemon with no port file configured
        When GET /health is called
        Then the daemon responds normally
        """
        port = daemon_no_port_file.port
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310 - localhost-only test server
            body = json.loads(resp.read())
        assert body["status"] == "ok"
        assert daemon_no_port_file.port_file is None


class TestZeroBlendFallback:
    """
    Feature: Zero-sum blend weights fall back to 0.5/0.5

    As a model author
    I want the daemon to handle both blend weights being zero gracefully
    So that division-by-zero is avoided and a sensible default is used
    """

    @pytest.mark.integration
    def test_zero_blend_weights_normalize_to_default(
        self, daemon_with_zero_blend: InferenceDaemon
    ):
        """
        Scenario: Model specifies word_overlap_weight=0 and ml_weight=0
        Given the 'zeroblend' model with both blend weights set to 0.0
        When POST /infer is sent
        Then the response blend weights are both 0.5
        """
        port = daemon_with_zero_blend.port
        url = f"http://127.0.0.1:{port}/infer"
        payload = json.dumps(
            {"model": "zeroblend", "features": {"feat_a": 1.0}}
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
            body = json.loads(resp.read())

        assert resp.status == 200
        assert abs(body["blend"]["word_overlap_weight"] - 0.5) < 1e-9
        assert abs(body["blend"]["ml_weight"] - 0.5) < 1e-9
