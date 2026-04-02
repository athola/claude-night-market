"""Tests for the OnnxSidecarScorer (oracle daemon client)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import pytest
from gauntlet.ml.scorer import OnnxSidecarScorer

from tests.conftest import make_urlopen_response


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
            mock_urlopen.return_value = make_urlopen_response(
                b'{"status": "ok", "models": ["quality_v1"]}'
            )
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
            mock_urlopen.return_value = make_urlopen_response(b'{"score": 0.87}')
            scorer = OnnxSidecarScorer(port_file)
            result = scorer.score({"feat_a": 1.0})
            assert result == pytest.approx(0.87)

    @pytest.mark.unit
    def test_blend_weights_default_before_inference(self, tmp_path: Path):
        """
        Scenario: Blend weights default to 0.5/0.5 before first inference
        Given a sidecar scorer that has not called score() yet
        When blend_weights is accessed
        Then it returns the neutral default (0.5, 0.5)
        """
        scorer = OnnxSidecarScorer(tmp_path / "nonexistent.port")
        assert scorer.blend_weights == (0.5, 0.5)

    # ------------------------------------------------------------------
    # _resolve_url cache hit (line 58)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_resolve_url_uses_cached_base_url(self, tmp_path: Path):
        """
        Scenario: Port file is only read once; subsequent calls use the cache
        Given a scorer whose _base_url is already populated
        When available() is called a second time
        Then urlopen is called with the cached URL, not the port file again
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("9000")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(b'{"status": "ok"}')
            # First call populates _base_url cache.
            scorer.available()
            _ = mock_urlopen.call_count  # populate cache

        # Remove the port file; a second available() must still work via cache.
        port_file.unlink()
        scorer._base_url = "http://127.0.0.1:9000"

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen2:
            mock_urlopen2.return_value = make_urlopen_response(b'{"status": "ok"}')
            result = scorer.available()

        assert result is True
        assert mock_urlopen2.call_count == 1

    # ------------------------------------------------------------------
    # _resolve_url non-integer port file (line 71 - ValueError branch)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_not_available_when_port_file_has_non_integer_content(self, tmp_path: Path):
        """
        Scenario: Port file contains garbage text, not a port number
        Given a port file that contains "not-a-port"
        When available() is called
        Then it returns False without raising
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("not-a-port")
        scorer = OnnxSidecarScorer(port_file)
        assert scorer.available() is False

    @pytest.mark.unit
    def test_score_returns_zero_when_port_file_has_non_integer_content(
        self, tmp_path: Path
    ):
        """
        Scenario: score() returns 0.0 when port file is non-integer
        Given a port file that contains "garbage"
        When score() is called
        Then it returns 0.0
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("garbage")
        scorer = OnnxSidecarScorer(port_file)
        assert scorer.score({"feat_a": 1.0}) == 0.0

    # ------------------------------------------------------------------
    # Health check network errors (lines 126, 133-134)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_available_returns_false_on_url_error(self, tmp_path: Path):
        """
        Scenario: Network error during health check
        Given a valid port file but the daemon is unreachable
        When available() is called and urlopen raises URLError
        Then it returns False and resets the cached URL
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch(
            "gauntlet.ml.scorer.urlopen", side_effect=URLError("connection refused")
        ):
            result = scorer.available()

        assert result is False
        assert scorer._base_url is None

    @pytest.mark.unit
    def test_available_returns_false_on_malformed_json(self, tmp_path: Path):
        """
        Scenario: Daemon returns malformed JSON on /health
        Given a valid port file but the health response is not valid JSON
        When available() is called
        Then it returns False and resets the cached URL
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(b"not json {{")
            result = scorer.available()

        assert result is False
        assert scorer._base_url is None

    @pytest.mark.unit
    def test_available_returns_false_when_status_not_ok(self, tmp_path: Path):
        """
        Scenario: Daemon returns JSON with status != "ok"
        Given a valid port file and a daemon that reports an error status
        When available() is called
        Then it returns False
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(b'{"status": "degraded"}')
            result = scorer.available()

        assert result is False

    # ------------------------------------------------------------------
    # /infer blend weight caching (lines 146-148)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_score_caches_blend_weights_from_response(self, tmp_path: Path):
        """
        Scenario: Daemon returns blend weights alongside the score
        Given a daemon that returns blend weights in its /infer response
        When score() is called
        Then blend_weights reflects the daemon's configuration
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        payload = (
            b'{"score": 0.75, "blend": {"word_overlap_weight": 0.3, "ml_weight": 0.7}}'
        )

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(payload)
            result = scorer.score({"feat_a": 0.5})

        assert result == pytest.approx(0.75)
        assert scorer.blend_weights == pytest.approx((0.3, 0.7))

    @pytest.mark.unit
    def test_blend_weights_returns_cached_value_after_inference(self, tmp_path: Path):
        """
        Scenario: blend_weights returns the cached tuple after score()
        Given a scorer whose _blend has been populated via score()
        When blend_weights is accessed
        Then it returns the cached value, not the default
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        payload = (
            b'{"score": 0.6, "blend": {"word_overlap_weight": 0.4, "ml_weight": 0.6}}'
        )

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(payload)
            scorer.score({"feat_a": 0.5})

        # Now access blend_weights without patching — must use the cache (line 192).
        assert scorer.blend_weights == pytest.approx((0.4, 0.6))

    # ------------------------------------------------------------------
    # /infer network errors (lines 175, 180-182)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_score_returns_zero_on_url_error_during_infer(self, tmp_path: Path):
        """
        Scenario: Network error during /infer call
        Given a valid port file but urlopen raises URLError on /infer
        When score() is called
        Then it returns 0.0 and resets the cached URL
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen", side_effect=URLError("timeout")):
            result = scorer.score({"feat_a": 1.0})

        assert result == 0.0
        assert scorer._base_url is None

    @pytest.mark.unit
    def test_score_returns_zero_on_malformed_json_from_infer(self, tmp_path: Path):
        """
        Scenario: Daemon returns malformed JSON on /infer
        Given a valid port file and a daemon that returns bad JSON
        When score() is called
        Then it returns 0.0 and resets the cached URL
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(b"{{bad json}}")
            result = scorer.score({"feat_a": 1.0})

        assert result == 0.0
        assert scorer._base_url is None

    @pytest.mark.unit
    def test_score_returns_zero_on_value_error_from_infer(self, tmp_path: Path):
        """
        Scenario: Daemon returns JSON with a non-numeric score field
        Given a valid port file and a daemon that returns {"score": "NaN"}
        When score() is called
        Then it returns 0.0 and resets the cached URL
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        scorer = OnnxSidecarScorer(port_file)

        with patch("gauntlet.ml.scorer.urlopen") as mock_urlopen:
            mock_urlopen.return_value = make_urlopen_response(
                b'{"score": "not-a-float"}'
            )
            result = scorer.score({"feat_a": 1.0})

        assert result == 0.0
        assert scorer._base_url is None
