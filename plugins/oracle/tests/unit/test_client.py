"""Tests for the oracle HTTP client."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest
from oracle.client import OracleClient


def _make_response(body: dict, status: int = 200) -> MagicMock:
    """Build a mock urlopen response context manager."""
    payload = json.dumps(body).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.status = status
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestIsAvailable:
    """
    Feature: Daemon availability check

    As a plugin using the oracle client
    I want to know if the inference daemon is reachable
    So that I can degrade gracefully when it is not
    """

    @pytest.mark.unit
    def test_returns_true_when_daemon_healthy(self, tmp_path: Path):
        """
        Scenario: Daemon is running and healthy
        Given a port file exists and /health returns status ok
        When is_available is called
        Then it returns True
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        with patch(
            "oracle.client.urlopen", return_value=_make_response({"status": "ok"})
        ):
            assert client.is_available() is True

    @pytest.mark.unit
    def test_returns_false_when_no_port_file(self, tmp_path: Path):
        """
        Scenario: Port file does not exist
        Given no port file on disk
        When is_available is called
        Then it returns False without attempting a network call
        """
        client = OracleClient(port_file=tmp_path / "missing.port")

        with patch("oracle.client.urlopen") as mock_urlopen:
            result = client.is_available()

        assert result is False
        mock_urlopen.assert_not_called()

    @pytest.mark.unit
    def test_returns_false_when_health_status_not_ok(self, tmp_path: Path):
        """
        Scenario: Daemon responds but reports unhealthy status
        Given a port file exists and /health returns status not ok
        When is_available is called
        Then it returns False
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        with patch(
            "oracle.client.urlopen",
            return_value=_make_response({"status": "starting"}),
        ):
            assert client.is_available() is False


class TestResolveUrl:
    """
    Feature: Port file parsing and URL caching

    As the oracle client internals
    I want a stable base URL resolved once from disk
    So that repeated calls avoid redundant file reads
    """

    @pytest.mark.unit
    def test_caches_url_after_first_read(self, tmp_path: Path):
        """
        Scenario: URL is cached after first successful resolve
        Given a port file exists
        When _resolve_url is called twice
        Then the port file is read only once
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        url1 = client._resolve_url()
        url2 = client._resolve_url()

        assert url1 == "http://127.0.0.1:18080"
        assert url1 == url2

    @pytest.mark.unit
    def test_returns_none_for_non_integer_port(self, tmp_path: Path):
        """
        Scenario: Port file contains non-numeric content
        Given a port file with invalid content
        When _resolve_url is called
        Then it returns None
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("not-a-port")
        client = OracleClient(port_file=port_file)

        assert client._resolve_url() is None


class TestInfer:
    """
    Feature: Inference delegation

    As a plugin using the oracle client
    I want to send features and receive a float score
    So that I can use model predictions in my workflow
    """

    @pytest.mark.unit
    def test_returns_float_score_on_success(self, tmp_path: Path):
        """
        Scenario: Daemon returns a valid score
        Given a running daemon with a port file
        When infer is called with model name and features
        Then it returns the float score from the response
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        with patch(
            "oracle.client.urlopen",
            return_value=_make_response({"score": 0.92}),
        ):
            result = client.infer("relevance", {"token_count": 512.0, "depth": 3.0})

        assert isinstance(result, float)
        assert abs(result - 0.92) < 1e-9

    @pytest.mark.unit
    def test_returns_none_when_daemon_unavailable(self, tmp_path: Path):
        """
        Scenario: Port file is missing
        Given no port file on disk
        When infer is called
        Then it returns None
        """
        client = OracleClient(port_file=tmp_path / "missing.port")
        result = client.infer("relevance", {"x": 1.0})
        assert result is None

    @pytest.mark.unit
    def test_returns_none_on_timeout(self, tmp_path: Path):
        """
        Scenario: Daemon does not respond within the timeout
        Given a port file exists but the request times out
        When infer is called with a very small timeout
        Then it returns None
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file, timeout=0.001)

        with patch("oracle.client.urlopen", side_effect=URLError("timed out")):
            result = client.infer("relevance", {"x": 1.0})

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_response_has_no_score(self, tmp_path: Path):
        """
        Scenario: Daemon returns a response without a score field
        Given a port file exists and /infer returns an unexpected payload
        When infer is called
        Then it returns None
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        with patch(
            "oracle.client.urlopen",
            return_value=_make_response({"error": "model not loaded"}),
        ):
            result = client.infer("relevance", {"x": 1.0})

        assert result is None

    @pytest.mark.unit
    def test_returns_false_on_network_error_during_health(self, tmp_path: Path):
        """
        Scenario: Daemon connection refused on health check
        Given a port file exists but the daemon is not listening
        When is_available is called
        Then it returns False
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        with patch("oracle.client.urlopen", side_effect=URLError("connection refused")):
            assert client.is_available() is False

    @pytest.mark.unit
    def test_resets_cached_url_on_network_error(self, tmp_path: Path):
        """
        Scenario: Network error clears URL cache so next call re-reads port file
        Given a port file exists and the first call fails with URLError
        When infer is called twice (first fails, second succeeds)
        Then the second call re-reads the port file and succeeds
        """
        port_file = tmp_path / "oracle.port"
        port_file.write_text("18080")
        client = OracleClient(port_file=port_file)

        success_resp = _make_response({"score": 0.5})
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise URLError("connection refused")
            return success_resp

        with patch("oracle.client.urlopen", side_effect=side_effect):
            first = client.infer("m", {"x": 1.0})
            second = client.infer("m", {"x": 1.0})

        assert first is None
        assert second == 0.5
