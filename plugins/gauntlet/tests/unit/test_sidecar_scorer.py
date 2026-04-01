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
