"""Tests for the Scorer protocol and YamlScorer."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from gauntlet.ml.scorer import YamlScorer


@pytest.fixture()
def model_yaml(tmp_path: Path) -> Path:
    """Create a minimal test model YAML file."""
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
        "metadata:\n"
        "  trained_on: test\n"
    )
    model_path = tmp_path / "test_model.yaml"
    model_path.write_text(content)
    return model_path


@pytest.fixture()
def model_no_sigmoid(tmp_path: Path) -> Path:
    """Create a model YAML without sigmoid."""
    content = (
        "schema_version: 1\n"
        "model_type: logistic_regression\n"
        "features:\n"
        "  - feat_a\n"
        "weights:\n"
        "  feat_a: 1.0\n"
        "intercept: 0.0\n"
        "sigmoid: false\n"
        "blend:\n"
        "  word_overlap_weight: 0.5\n"
        "  ml_weight: 0.5\n"
    )
    model_path = tmp_path / "no_sigmoid.yaml"
    model_path.write_text(content)
    return model_path


class TestYamlScorer:
    """
    Feature: YAML-backed logistic regression scorer

    As the gauntlet ML module
    I want to load model coefficients from YAML
    So that inference requires zero external dependencies
    """

    @pytest.mark.unit
    def test_available_with_valid_model(self, model_yaml: Path):
        """
        Scenario: Scorer loads a valid model file
        Given a valid model YAML
        When YamlScorer is initialized
        Then available() returns True
        """
        scorer = YamlScorer(str(model_yaml))
        assert scorer.available() is True

    @pytest.mark.unit
    def test_not_available_with_missing_file(self):
        """
        Scenario: Scorer handles missing model gracefully
        Given a path to a nonexistent file
        When YamlScorer is initialized
        Then available() returns False
        """
        scorer = YamlScorer("/nonexistent/model.yaml")
        assert scorer.available() is False

    @pytest.mark.unit
    def test_not_available_with_corrupt_yaml(self, tmp_path: Path):
        """
        Scenario: Scorer handles corrupt YAML gracefully
        Given a file with invalid YAML content
        When YamlScorer is initialized
        Then available() returns False
        """
        bad = tmp_path / "bad.yaml"
        bad.write_text(": : : not valid yaml [[[")
        scorer = YamlScorer(str(bad))
        assert scorer.available() is False

    @pytest.mark.unit
    def test_dot_product_with_sigmoid(self, model_yaml: Path):
        """
        Scenario: Score computes dot product + sigmoid correctly
        Given weights feat_a=2.0, feat_b=-1.0, intercept=0.5, sigmoid=true
        When score({feat_a: 1.0, feat_b: 0.5}) is called
        Then result is sigmoid(2.0*1.0 + (-1.0)*0.5 + 0.5) = sigmoid(2.0)
        """
        scorer = YamlScorer(str(model_yaml))
        result = scorer.score({"feat_a": 1.0, "feat_b": 0.5})
        expected = 1.0 / (1.0 + math.exp(-2.0))
        assert result == pytest.approx(expected, abs=1e-6)

    @pytest.mark.unit
    def test_dot_product_without_sigmoid(self, model_no_sigmoid: Path):
        """
        Scenario: Score computes raw dot product when sigmoid is false
        Given weights feat_a=1.0, intercept=0.0, sigmoid=false
        When score({feat_a: 3.0}) is called
        Then result is 3.0
        """
        scorer = YamlScorer(str(model_no_sigmoid))
        result = scorer.score({"feat_a": 3.0})
        assert result == pytest.approx(3.0)

    @pytest.mark.unit
    def test_missing_feature_treated_as_zero(self, model_yaml: Path):
        """
        Scenario: Missing features default to 0.0
        Given a model expecting feat_a and feat_b
        When score is called with only feat_a
        Then feat_b is treated as 0.0
        """
        scorer = YamlScorer(str(model_yaml))
        result = scorer.score({"feat_a": 1.0})
        expected = 1.0 / (1.0 + math.exp(-2.5))
        assert result == pytest.approx(expected, abs=1e-6)

    @pytest.mark.unit
    def test_blend_weights_accessible(self, model_yaml: Path):
        """
        Scenario: Blend weights are readable from the model
        Given a model with blend weights 0.4 and 0.6
        When blend_weights is accessed
        Then it returns the correct tuple
        """
        scorer = YamlScorer(str(model_yaml))
        assert scorer.blend_weights == (0.4, 0.6)

    @pytest.mark.unit
    def test_score_returns_zero_when_unavailable(self):
        """
        Scenario: Unavailable scorer returns 0.0
        Given a scorer that failed to load
        When score is called
        Then it returns 0.0
        """
        scorer = YamlScorer("/nonexistent/model.yaml")
        assert scorer.score({"feat_a": 1.0}) == 0.0

    @pytest.mark.unit
    def test_not_available_when_yaml_is_not_a_dict(self, tmp_path: Path):
        """
        Scenario: YAML file parses but contains a list, not a mapping
        Given a YAML file that is a top-level list
        When YamlScorer is initialized
        Then available() returns False (non-dict guard on line 58)
        """
        yaml_list = tmp_path / "list.yaml"
        yaml_list.write_text("- item_one\n- item_two\n")
        scorer = YamlScorer(str(yaml_list))
        assert scorer.available() is False

    @pytest.mark.unit
    def test_blend_weights_default_when_both_zero(self, tmp_path: Path):
        """
        Scenario: Blend weights are both 0.0 in the model file
        Given a model YAML with word_overlap_weight=0.0 and ml_weight=0.0
        When YamlScorer is initialized
        Then blend_weights falls back to (0.5, 0.5) to avoid zero division
        """
        content = (
            "weights:\n"
            "  feat_a: 1.0\n"
            "intercept: 0.0\n"
            "sigmoid: false\n"
            "blend:\n"
            "  word_overlap_weight: 0.0\n"
            "  ml_weight: 0.0\n"
        )
        model_path = tmp_path / "zero_blend.yaml"
        model_path.write_text(content)
        scorer = YamlScorer(str(model_path))
        assert scorer.blend_weights == (0.5, 0.5)
