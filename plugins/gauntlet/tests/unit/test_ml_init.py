"""Tests for the ml module public API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import gauntlet.ml as ml_mod
import pytest
from gauntlet.ml import score_answer_quality
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
