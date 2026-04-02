"""Tests for the ml module public API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import gauntlet.ml as ml_mod
import pytest
from gauntlet.ml import (
    _get_oracle_port_file,
    _get_scorer,
    get_blend_weights,
    score_answer_quality,
)
from gauntlet.ml.scorer import OnnxSidecarScorer, YamlScorer
from gauntlet.models import Challenge


def _challenge(
    challenge_type: str,
    answer: str,
) -> Challenge:
    return Challenge(
        id="ch-test-001",
        type=challenge_type,
        knowledge_entry_id="ke-test-001",
        difficulty=2,
        prompt="Test prompt",
        context="Test context about tokens and authentication",
        answer=answer,
    )


class TestScoreAnswerQuality:
    """
    Feature: ML answer quality scoring public API

    As the gauntlet scoring module
    I want a single function to get an ML quality score
    So that integration is simple and graceful degradation is automatic
    """

    @pytest.mark.unit
    def test_returns_float_for_valid_input(self):
        """
        Scenario: Valid challenge and answer produce a float score
        Given a challenge with a reference answer
        When score_answer_quality is called with a relevant answer
        Then the result is a float between 0.0 and 1.0
        """
        ch = _challenge("explain_why", "Access tokens expire after 15 minutes.")
        result = score_answer_quality(ch, "Tokens expire in 15 minutes for security.")
        assert result is not None
        assert 0.0 <= result <= 1.0

    @pytest.mark.unit
    def test_returns_none_when_model_missing(self, tmp_path: Path):
        """
        Scenario: Missing model file causes graceful degradation
        Given no model file at the expected path
        When score_answer_quality is called
        Then the result is None
        """
        with patch(
            "gauntlet.ml._MODEL_PATH",
            str(tmp_path / "nonexistent.yaml"),
        ):
            ml_mod._scorer = None
            result = score_answer_quality(
                _challenge("explain_why", "test"),
                "test",
            )
            assert result is None
        # Reset so subsequent tests get a fresh scorer with the real path.
        ml_mod._scorer = None

    @pytest.mark.unit
    def test_exact_match_scores_high(self):
        """
        Scenario: Exact answer match produces high quality score
        Given a challenge
        When the answer exactly matches the reference
        Then the score is above 0.7
        """
        text = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", text)
        result = score_answer_quality(ch, text)
        assert result is not None
        assert result > 0.7

    @pytest.mark.unit
    def test_unrelated_answer_scores_low(self):
        """
        Scenario: Unrelated answer produces low quality score
        Given a challenge about token expiry
        When the answer is about databases
        Then the score is below 0.4
        """
        ch = _challenge(
            "explain_why",
            "Access tokens expire after 15 minutes to limit exposure.",
        )
        result = score_answer_quality(ch, "PostgreSQL uses B-tree indexes.")
        assert result is not None
        assert result < 0.4

    @pytest.mark.unit
    def test_empty_answer_scores_low(self):
        """
        Scenario: Empty answer produces very low score
        Given a challenge
        When the answer is empty
        Then the score is below 0.2
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        result = score_answer_quality(ch, "")
        assert result is not None
        assert result < 0.2


class TestGetOraclePortFile:
    """
    Feature: Oracle port file discovery

    As the gauntlet ML module
    I want to locate the oracle daemon's port file
    So that I can connect to the sidecar scorer
    """

    @pytest.mark.unit
    def test_returns_port_file_from_claude_plugin_data_env(self, tmp_path: Path):
        """
        Scenario: CLAUDE_PLUGIN_DATA points to a gauntlet data directory
        Given CLAUDE_PLUGIN_DATA is set and oracle/daemon.port exists as a sibling
        When _get_oracle_port_file() is called
        Then it returns the path to oracle/daemon.port
        """
        gauntlet_data = tmp_path / "gauntlet"
        gauntlet_data.mkdir()
        oracle_dir = tmp_path / "oracle"
        oracle_dir.mkdir()
        port_file = oracle_dir / "daemon.port"
        port_file.write_text("9001")

        with patch.dict("os.environ", {"CLAUDE_PLUGIN_DATA": str(gauntlet_data)}):
            result = _get_oracle_port_file()

        assert result == port_file

    @pytest.mark.unit
    def test_returns_none_when_plugin_data_port_file_missing(self, tmp_path: Path):
        """
        Scenario: CLAUDE_PLUGIN_DATA is set but oracle port file does not exist
        Given CLAUDE_PLUGIN_DATA points to a directory with no oracle sibling
        When _get_oracle_port_file() is called
        Then it checks the fallback path and returns None if that also missing
        """
        gauntlet_data = tmp_path / "gauntlet"
        gauntlet_data.mkdir()

        with patch.dict("os.environ", {"CLAUDE_PLUGIN_DATA": str(gauntlet_data)}):
            with patch("gauntlet.ml.Path.home", return_value=tmp_path):
                result = _get_oracle_port_file()

        assert result is None

    @pytest.mark.unit
    def test_returns_fallback_port_file_when_plugin_data_unset(self, tmp_path: Path):
        """
        Scenario: CLAUDE_PLUGIN_DATA is not set, fallback path exists
        Given no CLAUDE_PLUGIN_DATA env var
        And ~/.oracle-inference/daemon.port exists
        When _get_oracle_port_file() is called
        Then it returns the fallback path
        """
        oracle_dir = tmp_path / ".oracle-inference"
        oracle_dir.mkdir()
        port_file = oracle_dir / "daemon.port"
        port_file.write_text("9002")

        with patch.dict("os.environ", {}, clear=True):
            with patch("gauntlet.ml.Path.home", return_value=tmp_path):
                result = _get_oracle_port_file()

        assert result == port_file

    @pytest.mark.unit
    def test_returns_none_when_no_port_file_anywhere(self, tmp_path: Path):
        """
        Scenario: Neither CLAUDE_PLUGIN_DATA nor fallback port file exist
        Given no CLAUDE_PLUGIN_DATA env var and no fallback path
        When _get_oracle_port_file() is called
        Then it returns None
        """
        with patch.dict("os.environ", {}, clear=True):
            with patch("gauntlet.ml.Path.home", return_value=tmp_path):
                result = _get_oracle_port_file()

        assert result is None


class TestGetScorer:
    """
    Feature: Lazy scorer initialisation

    As the gauntlet ML module
    I want to pick the best available scorer at startup
    So that ONNX acceleration is used when oracle is present
    """

    @pytest.mark.unit
    def test_returns_sidecar_when_oracle_available(self, tmp_path: Path):
        """
        Scenario: Oracle daemon is present and healthy
        Given _get_oracle_port_file returns a valid port file
        And OnnxSidecarScorer.available() returns True
        When _get_scorer() is called
        Then it returns an OnnxSidecarScorer instance
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        ml_mod._scorer = None
        try:
            with patch("gauntlet.ml._get_oracle_port_file", return_value=port_file):
                with patch.object(OnnxSidecarScorer, "available", return_value=True):
                    scorer = _get_scorer()
            assert isinstance(scorer, OnnxSidecarScorer)
        finally:
            ml_mod._scorer = None

    @pytest.mark.unit
    def test_falls_back_to_yaml_scorer_when_sidecar_unavailable(self, tmp_path: Path):
        """
        Scenario: Oracle daemon is present but unhealthy
        Given _get_oracle_port_file returns a port file
        But OnnxSidecarScorer.available() returns False
        When _get_scorer() is called
        Then it falls back to YamlScorer
        """
        port_file = tmp_path / "daemon.port"
        port_file.write_text("12345")

        ml_mod._scorer = None
        try:
            with patch("gauntlet.ml._get_oracle_port_file", return_value=port_file):
                with patch.object(OnnxSidecarScorer, "available", return_value=False):
                    scorer = _get_scorer()
            assert isinstance(scorer, YamlScorer)
        finally:
            ml_mod._scorer = None

    @pytest.mark.unit
    def test_falls_back_to_yaml_scorer_when_no_port_file(self, tmp_path: Path):
        """
        Scenario: No oracle port file found
        Given _get_oracle_port_file returns None
        When _get_scorer() is called
        Then it returns a YamlScorer
        """
        ml_mod._scorer = None
        try:
            with patch("gauntlet.ml._get_oracle_port_file", return_value=None):
                scorer = _get_scorer()
            assert isinstance(scorer, YamlScorer)
        finally:
            ml_mod._scorer = None

    @pytest.mark.unit
    def test_returns_cached_scorer_on_second_call(self):
        """
        Scenario: _get_scorer() is called twice
        Given the scorer was already initialised
        When _get_scorer() is called again
        Then it returns the same instance (singleton pattern)
        """
        ml_mod._scorer = None
        try:
            first = _get_scorer()
            second = _get_scorer()
            assert first is second
        finally:
            ml_mod._scorer = None


class TestGetBlendWeights:
    """
    Feature: Blend weight access with graceful degradation

    As the gauntlet scoring module
    I want to get blend weights from the active scorer
    So that I can combine word-overlap and ML scores appropriately
    """

    @pytest.mark.unit
    def test_returns_fallback_when_scorer_unavailable(self, tmp_path: Path):
        """
        Scenario: Model file missing, scorer unavailable
        Given no model file exists
        When get_blend_weights() is called
        Then it returns (1.0, 0.0) to use 100% word-overlap
        """
        ml_mod._scorer = None
        try:
            with patch(
                "gauntlet.ml._MODEL_PATH",
                str(tmp_path / "nonexistent.yaml"),
            ):
                ml_mod._scorer = None
                result = get_blend_weights()
            assert result == (1.0, 0.0)
        finally:
            ml_mod._scorer = None

    @pytest.mark.unit
    def test_returns_scorer_blend_when_available(self):
        """
        Scenario: Scorer loaded successfully
        Given the real model file exists
        When get_blend_weights() is called
        Then it returns the scorer's blend tuple (not the fallback)
        """
        ml_mod._scorer = None
        try:
            result = get_blend_weights()
            wo, ml = result
            assert isinstance(wo, float)
            assert isinstance(ml, float)
            assert abs(wo + ml - 1.0) < 1e-6
        finally:
            ml_mod._scorer = None
