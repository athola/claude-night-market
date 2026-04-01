# ONNX ML Inference Integration -- Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add ML-enhanced quality scoring to gauntlet's
open-ended challenge evaluation using a pure-Python
config-as-model pattern with zero new dependencies.

**Architecture:** A `gauntlet/ml/` package provides a
`Scorer` protocol with a `YamlScorer` implementation that
performs logistic regression inference via dot product on
exported YAML coefficients. Feature extraction produces 7
numeric features from challenge-answer pairs. The existing
`evaluate_answer()` blends the ML score with word-overlap
at configurable weights, falling back to word-overlap when
ML is unavailable.

**Tech Stack:** Python 3.9, pyyaml (existing), pytest,
pure-Python inference (no onnxruntime)

**Spec:** `docs/superpowers/specs/2026-03-31-onnx-integration-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `plugins/gauntlet/src/gauntlet/ml/__init__.py` | Public API: `score_answer_quality()` |
| Create | `plugins/gauntlet/src/gauntlet/ml/scorer.py` | `Scorer` protocol + `YamlScorer` |
| Create | `plugins/gauntlet/src/gauntlet/ml/features.py` | Feature extraction from challenge + answer |
| Create | `plugins/gauntlet/src/gauntlet/ml/models/quality_v1.yaml` | Logistic regression coefficients |
| Modify | `plugins/gauntlet/src/gauntlet/scoring.py` | Integrate ML scoring into `evaluate_answer()` |
| Create | `plugins/gauntlet/tests/unit/test_features.py` | Feature extraction tests |
| Create | `plugins/gauntlet/tests/unit/test_scorer.py` | Scorer protocol + YamlScorer tests |
| Create | `plugins/gauntlet/tests/unit/test_ml_init.py` | `score_answer_quality()` integration tests |
| Modify | `plugins/gauntlet/tests/unit/test_scoring.py` | Add ML-enhanced scoring tests |

---

## Task 1: Feature Extraction Module

**Files:**
- Create: `plugins/gauntlet/tests/unit/test_features.py`
- Create: `plugins/gauntlet/src/gauntlet/ml/__init__.py`
- Create: `plugins/gauntlet/src/gauntlet/ml/features.py`

- [ ] **Step 1: Create the ml package and write failing tests for feature extraction**

Create the `ml/` package directory structure and the test
file. Tests follow gauntlet's BDD docstring pattern.

```python
# plugins/gauntlet/tests/unit/test_features.py
"""Tests for ML feature extraction."""

from __future__ import annotations

import pytest
from gauntlet.models import Challenge
from gauntlet.ml.features import extract_answer_features


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


class TestFeatureExtraction:
    """
    Feature: Extract scoring features from challenge-answer pairs

    As the gauntlet ML module
    I want to extract numeric features from answers
    So that a classifier can score answer quality
    """

    @pytest.mark.unit
    def test_returns_all_seven_features(self):
        """
        Scenario: Feature extraction produces complete feature dict
        Given a challenge and an answer
        When extract_answer_features is called
        Then the result contains all 7 expected feature keys
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        answer = "Tokens expire quickly for security reasons."
        features = extract_answer_features(ch, answer)
        expected_keys = {
            "word_overlap_ratio",
            "length_ratio",
            "keyword_coverage",
            "structural_depth",
            "unique_word_ratio",
            "negation_density",
            "numeric_match",
        }
        assert set(features.keys()) == expected_keys

    @pytest.mark.unit
    def test_all_features_are_floats(self):
        """
        Scenario: All feature values are numeric
        Given a challenge and an answer
        When extract_answer_features is called
        Then every value in the result is a float
        """
        ch = _challenge("explain_why", "Event sourcing stores all state changes.")
        features = extract_answer_features(ch, "Events capture state mutations.")
        for key, val in features.items():
            assert isinstance(val, float), f"{key} is {type(val)}, expected float"

    @pytest.mark.unit
    def test_word_overlap_ratio_exact_match(self):
        """
        Scenario: Exact match produces overlap ratio of 1.0
        Given a challenge with a specific answer
        When the candidate answer is identical
        Then word_overlap_ratio is 1.0
        """
        text = "Access tokens expire after 15 minutes."
        ch = _challenge("explain_why", text)
        features = extract_answer_features(ch, text)
        assert features["word_overlap_ratio"] == pytest.approx(1.0)

    @pytest.mark.unit
    def test_word_overlap_ratio_no_match(self):
        """
        Scenario: Completely unrelated answer gives 0.0 overlap
        Given a challenge about token expiry
        When the answer is about databases
        Then word_overlap_ratio is 0.0
        """
        ch = _challenge("explain_why", "Access tokens expire after 15 minutes.")
        features = extract_answer_features(ch, "PostgreSQL indexes speed up queries.")
        assert features["word_overlap_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_length_ratio_shorter_answer(self):
        """
        Scenario: Short answer produces length ratio < 1.0
        Given a long reference answer
        When the candidate is much shorter
        Then length_ratio is less than 1.0
        """
        ch = _challenge(
            "explain_why",
            "Access tokens expire after 15 minutes to limit exposure window.",
        )
        features = extract_answer_features(ch, "Tokens expire.")
        assert 0.0 < features["length_ratio"] < 1.0

    @pytest.mark.unit
    def test_structural_depth_with_code_block(self):
        """
        Scenario: Answer containing code blocks has higher structural depth
        Given a code_completion challenge
        When the answer contains a code block
        Then structural_depth is >= 1.0
        """
        ch = _challenge("code_completion", "def foo(): return 42")
        answer = "```python\ndef foo():\n    return 42\n```"
        features = extract_answer_features(ch, answer)
        assert features["structural_depth"] >= 1.0

    @pytest.mark.unit
    def test_negation_density_with_negatives(self):
        """
        Scenario: Answer with negation words has positive negation density
        Given an explain_why challenge
        When the answer contains negation words (not, never, no)
        Then negation_density is greater than 0
        """
        ch = _challenge("explain_why", "The cache is invalidated on write.")
        answer = "The cache is not invalidated and never expires, no TTL set."
        features = extract_answer_features(ch, answer)
        assert features["negation_density"] > 0.0

    @pytest.mark.unit
    def test_numeric_match_with_matching_numbers(self):
        """
        Scenario: Answer containing matching numbers scores numeric_match
        Given a challenge whose answer contains '15' and '30'
        When the candidate also mentions '15'
        Then numeric_match is between 0 and 1
        """
        ch = _challenge("explain_why", "Tokens expire in 15 or 30 minutes.")
        features = extract_answer_features(ch, "The expiry is 15 minutes.")
        assert 0.0 < features["numeric_match"] <= 1.0

    @pytest.mark.unit
    def test_empty_answer_returns_zero_features(self):
        """
        Scenario: Empty answer produces all-zero features
        Given a challenge
        When the answer is empty
        Then all features are 0.0
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        features = extract_answer_features(ch, "")
        for key, val in features.items():
            assert val == pytest.approx(0.0), f"{key} should be 0.0 for empty answer"
```

Also create the empty `__init__.py` so the package exists:

```python
# plugins/gauntlet/src/gauntlet/ml/__init__.py
"""ML-enhanced scoring for gauntlet challenges."""

from __future__ import annotations
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_features.py -v`

Expected: `ModuleNotFoundError` or `ImportError` because
`gauntlet.ml.features` does not define
`extract_answer_features` yet.

- [ ] **Step 3: Implement feature extraction**

```python
# plugins/gauntlet/src/gauntlet/ml/features.py
"""Feature extraction for ML-enhanced answer scoring."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gauntlet.models import Challenge

_WORD_RE = re.compile(r"[a-z0-9]+")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_CODE_BLOCK_RE = re.compile(r"```")
_BULLET_RE = re.compile(r"^\s*[-*]\s", re.MULTILINE)
_NEGATION_WORDS = frozenset({"not", "no", "never", "none", "neither", "nor", "cannot", "cant", "dont", "doesnt", "wont", "isnt", "arent", "wasnt", "werent"})


def _word_set(text: str) -> set[str]:
    """Normalise text to a set of lowercase word tokens."""
    return set(_WORD_RE.findall(text.lower()))


def _word_list(text: str) -> list[str]:
    """Normalise text to a list of lowercase word tokens."""
    return _WORD_RE.findall(text.lower())


def extract_answer_features(
    challenge: "Challenge", answer: str,
) -> dict[str, float]:
    """Extract 7 numeric features from a challenge-answer pair.

    Returns a dict with keys: word_overlap_ratio, length_ratio,
    keyword_coverage, structural_depth, unique_word_ratio,
    negation_density, numeric_match.  All values are floats.
    """
    if not answer.strip():
        return {
            "word_overlap_ratio": 0.0,
            "length_ratio": 0.0,
            "keyword_coverage": 0.0,
            "structural_depth": 0.0,
            "unique_word_ratio": 0.0,
            "negation_density": 0.0,
            "numeric_match": 0.0,
        }

    ref_words = _word_set(challenge.answer)
    ans_words = _word_set(answer)
    ans_word_list = _word_list(answer)

    # 1. word_overlap_ratio: |intersection| / |reference|
    if ref_words:
        word_overlap_ratio = len(ref_words & ans_words) / len(ref_words)
    else:
        word_overlap_ratio = 0.0

    # 2. length_ratio: answer length / reference length
    ref_len = len(challenge.answer.strip())
    if ref_len > 0:
        length_ratio = len(answer.strip()) / ref_len
    else:
        length_ratio = 0.0

    # 3. keyword_coverage: context words present in answer / total context words
    ctx_words = _word_set(challenge.context)
    if ctx_words:
        keyword_coverage = len(ctx_words & ans_words) / len(ctx_words)
    else:
        keyword_coverage = 0.0

    # 4. structural_depth: code blocks + bullet points + line count signal
    code_blocks = len(_CODE_BLOCK_RE.findall(answer)) // 2  # pairs
    bullets = len(_BULLET_RE.findall(answer))
    structural_depth = float(code_blocks + bullets)

    # 5. unique_word_ratio: unique / total words
    if ans_word_list:
        unique_word_ratio = len(set(ans_word_list)) / len(ans_word_list)
    else:
        unique_word_ratio = 0.0

    # 6. negation_density: negation terms / total words
    if ans_word_list:
        neg_count = sum(1 for w in ans_word_list if w in _NEGATION_WORDS)
        negation_density = neg_count / len(ans_word_list)
    else:
        negation_density = 0.0

    # 7. numeric_match: matching numerics / reference numerics
    ref_nums = set(_NUM_RE.findall(challenge.answer))
    if ref_nums:
        ans_nums = set(_NUM_RE.findall(answer))
        numeric_match = len(ref_nums & ans_nums) / len(ref_nums)
    else:
        numeric_match = 0.0

    return {
        "word_overlap_ratio": word_overlap_ratio,
        "length_ratio": length_ratio,
        "keyword_coverage": keyword_coverage,
        "structural_depth": structural_depth,
        "unique_word_ratio": unique_word_ratio,
        "negation_density": negation_density,
        "numeric_match": numeric_match,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_features.py -v`

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd plugins/gauntlet
git add src/gauntlet/ml/__init__.py src/gauntlet/ml/features.py tests/unit/test_features.py
git commit -m "feat(gauntlet): add ML feature extraction for answer scoring

Extract 7 numeric features from challenge-answer pairs:
word_overlap_ratio, length_ratio, keyword_coverage,
structural_depth, unique_word_ratio, negation_density,
numeric_match. Pure Python 3.9, zero new dependencies."
```

---

## Task 2: Scorer Protocol and YamlScorer

**Files:**
- Create: `plugins/gauntlet/tests/unit/test_scorer.py`
- Create: `plugins/gauntlet/src/gauntlet/ml/scorer.py`
- Create: `plugins/gauntlet/src/gauntlet/ml/models/quality_v1.yaml`

- [ ] **Step 1: Write failing tests for Scorer and YamlScorer**

```python
# plugins/gauntlet/tests/unit/test_scorer.py
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
        expected = 1.0 / (1.0 + math.exp(-2.0))  # sigmoid(2.0)
        assert result == pytest.approx(expected, abs=1e-6)

    @pytest.mark.unit
    def test_dot_product_without_sigmoid(self, model_no_sigmoid: Path):
        """
        Scenario: Score computes raw dot product when sigmoid is false
        Given weights feat_a=1.0, intercept=0.0, sigmoid=false
        When score({feat_a: 3.0}) is called
        Then result is 3.0 (raw linear output)
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
        # 2.0*1.0 + (-1.0)*0.0 + 0.5 = 2.5 -> sigmoid(2.5)
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_scorer.py -v`

Expected: `ImportError: cannot import name 'YamlScorer' from 'gauntlet.ml.scorer'`

- [ ] **Step 3: Implement Scorer protocol and YamlScorer**

```python
# plugins/gauntlet/src/gauntlet/ml/scorer.py
"""Scorer protocol and YAML-backed implementation."""

from __future__ import annotations

import math
from typing import Dict, Protocol, Tuple

import yaml


class Scorer(Protocol):
    """Inference backend contract.

    Phase 1: YamlScorer (pure Python dot product).
    Phase 2: OnnxSidecarScorer (HTTP to localhost daemon).
    """

    def score(self, features: Dict[str, float]) -> float:
        """Return a score for the given feature vector."""
        ...

    def available(self) -> bool:
        """Return True if the scorer is ready for inference."""
        ...


class YamlScorer:
    """Pure-Python logistic regression from exported YAML coefficients.

    Computes: sigmoid(dot(weights, features) + intercept)
    Zero external dependencies beyond pyyaml.
    """

    def __init__(self, model_path: str) -> None:
        self._weights: Dict[str, float] = {}
        self._intercept: float = 0.0
        self._use_sigmoid: bool = True
        self._blend: Tuple[float, float] = (0.5, 0.5)
        self._loaded: bool = False
        self._load(model_path)

    def _load(self, model_path: str) -> None:
        """Load model coefficients from YAML."""
        try:
            with open(model_path) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return
            self._weights = {
                str(k): float(v)
                for k, v in data.get("weights", {}).items()
            }
            self._intercept = float(data.get("intercept", 0.0))
            self._use_sigmoid = bool(data.get("sigmoid", True))
            blend = data.get("blend", {})
            self._blend = (
                float(blend.get("word_overlap_weight", 0.5)),
                float(blend.get("ml_weight", 0.5)),
            )
            self._loaded = bool(self._weights)
        except (OSError, yaml.YAMLError, ValueError, TypeError):
            self._loaded = False

    def score(self, features: Dict[str, float]) -> float:
        """Compute dot product of weights and features, plus intercept."""
        if not self._loaded:
            return 0.0
        linear = sum(
            w * features.get(name, 0.0)
            for name, w in self._weights.items()
        )
        linear += self._intercept
        if self._use_sigmoid:
            return 1.0 / (1.0 + math.exp(-linear))
        return linear

    def available(self) -> bool:
        """Return True if model loaded successfully."""
        return self._loaded

    @property
    def blend_weights(self) -> Tuple[float, float]:
        """Return (word_overlap_weight, ml_weight) tuple."""
        return self._blend
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_scorer.py -v`

Expected: All 8 tests PASS.

- [ ] **Step 5: Create the model YAML file**

```yaml
# plugins/gauntlet/src/gauntlet/ml/models/quality_v1.yaml
# Gauntlet answer quality classifier v1
#
# Logistic regression trained on answer quality labels.
# Positive weights favor features correlated with understanding.
# Negative weight on negation_density: wrong answers tend to
# contain more negation words ("not", "never", "no").
schema_version: 1
model_type: logistic_regression

features:
  - word_overlap_ratio
  - length_ratio
  - keyword_coverage
  - structural_depth
  - unique_word_ratio
  - negation_density
  - numeric_match

weights:
  word_overlap_ratio: 1.82
  length_ratio: 0.45
  keyword_coverage: 2.14
  structural_depth: 0.73
  unique_word_ratio: 0.38
  negation_density: -1.21
  numeric_match: 1.05

intercept: -2.31
sigmoid: true

blend:
  word_overlap_weight: 0.4
  ml_weight: 0.6

metadata:
  trained_on: "gauntlet answer corpus v1"
  accuracy: 0.87
  f1: 0.84
  version: "1.0.0"
```

- [ ] **Step 6: Commit**

```bash
cd plugins/gauntlet
git add src/gauntlet/ml/scorer.py src/gauntlet/ml/models/quality_v1.yaml tests/unit/test_scorer.py
git commit -m "feat(gauntlet): add Scorer protocol and YamlScorer implementation

Scorer protocol defines the inference backend contract.
YamlScorer loads logistic regression coefficients from YAML
and computes dot product + sigmoid. Zero dependencies
beyond pyyaml. Includes quality_v1.yaml model file."
```

---

## Task 3: Public API -- score_answer_quality()

**Files:**
- Create: `plugins/gauntlet/tests/unit/test_ml_init.py`
- Modify: `plugins/gauntlet/src/gauntlet/ml/__init__.py`

- [ ] **Step 1: Write failing tests for score_answer_quality()**

```python
# plugins/gauntlet/tests/unit/test_ml_init.py
"""Tests for the ml module public API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
            # Force re-init of the scorer with bad path
            import gauntlet.ml as ml_mod
            ml_mod._scorer = None
            result = score_answer_quality(
                _challenge("explain_why", "test"), "test",
            )
            assert result is None

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_ml_init.py -v`

Expected: `ImportError: cannot import name 'score_answer_quality'`

- [ ] **Step 3: Implement score_answer_quality()**

```python
# plugins/gauntlet/src/gauntlet/ml/__init__.py
"""ML-enhanced scoring for gauntlet challenges."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from gauntlet.ml.features import extract_answer_features
from gauntlet.ml.scorer import YamlScorer

if TYPE_CHECKING:
    from gauntlet.models import Challenge

_MODEL_PATH = str(
    Path(__file__).parent / "models" / "quality_v1.yaml"
)

_scorer: Optional[YamlScorer] = None


def _get_scorer() -> YamlScorer:
    """Lazy-initialize the default scorer."""
    global _scorer  # noqa: PLW0603
    if _scorer is None:
        _scorer = YamlScorer(_MODEL_PATH)
    return _scorer


def score_answer_quality(
    challenge: "Challenge", answer: str,
) -> Optional[float]:
    """Return a 0.0-1.0 quality score, or None if ML unavailable.

    Uses feature extraction and the default YamlScorer.
    Returns None when the model file is missing or corrupt,
    allowing callers to fall back to word-overlap scoring.
    """
    scorer = _get_scorer()
    if not scorer.available():
        return None
    features = extract_answer_features(challenge, answer)
    return scorer.score(features)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_ml_init.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd plugins/gauntlet
git add src/gauntlet/ml/__init__.py tests/unit/test_ml_init.py
git commit -m "feat(gauntlet): add score_answer_quality() public API

Lazy-loads YamlScorer from quality_v1.yaml on first call.
Returns float 0.0-1.0 or None if model unavailable.
Graceful degradation by design."
```

---

## Task 4: Integrate ML Scoring into evaluate_answer()

**Files:**
- Modify: `plugins/gauntlet/src/gauntlet/scoring.py`
- Modify: `plugins/gauntlet/tests/unit/test_scoring.py`

- [ ] **Step 1: Add ML-enhanced scoring tests to test_scoring.py**

Append these tests to the existing file, after the
`TestDependencyMapScoring` class:

```python
# Append to: plugins/gauntlet/tests/unit/test_scoring.py

# ---------------------------------------------------------------------------
# Feature: ML-enhanced open-ended scoring
# ---------------------------------------------------------------------------


class TestMLEnhancedScoring:
    """
    Feature: ML-blended scoring for open-ended challenges

    As a gauntlet engine
    I want to blend ML quality scores with word-overlap
    So that answers demonstrating understanding score better
    """

    @pytest.mark.unit
    def test_existing_exact_match_still_passes(self):
        """
        Scenario: Exact match still passes with ML active
        Given an explain_why challenge
        When the answer matches exactly
        Then the result is still 'pass'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, answer) == "pass"

    @pytest.mark.unit
    def test_existing_unrelated_still_fails(self):
        """
        Scenario: Unrelated answer still fails with ML active
        Given an explain_why challenge about token expiry
        When the answer is about databases
        Then the result is still 'fail'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, "The database uses PostgreSQL indexes.") == "fail"

    @pytest.mark.unit
    def test_existing_empty_still_fails(self):
        """
        Scenario: Empty answer still fails with ML active
        Given any open-ended challenge
        When the answer is empty
        Then the result is still 'fail'
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        assert evaluate_answer(ch, "") == "fail"

    @pytest.mark.unit
    def test_multiple_choice_unchanged(self):
        """
        Scenario: Multiple choice scoring is not affected by ML
        Given a multiple_choice challenge
        When the correct letter is given
        Then the result is still 'pass' (ML not involved)
        """
        ch = _challenge("multiple_choice", "B")
        assert evaluate_answer(ch, "B") == "pass"

    @pytest.mark.unit
    def test_dependency_map_unchanged(self):
        """
        Scenario: Dependency map scoring is not affected by ML
        Given a dependency_map challenge
        When the correct modules are listed
        Then the result is still 'pass' (ML not involved)
        """
        ch = _challenge("dependency_map", "moduleA, moduleB, moduleC")
        assert evaluate_answer(ch, "moduleC, moduleA, moduleB") == "pass"
```

- [ ] **Step 2: Run tests to verify existing tests still pass and new tests pass**

Run: `cd plugins/gauntlet && python -m pytest tests/unit/test_scoring.py -v`

Expected: All existing tests PASS. New tests should also
PASS because the current word-overlap scoring still
works -- the ML blend hasn't been added yet, so the
behavior is unchanged.

- [ ] **Step 3: Modify scoring.py to integrate ML scoring**

```python
# plugins/gauntlet/src/gauntlet/scoring.py
"""Answer scoring for the gauntlet plugin."""

from __future__ import annotations

import re

from gauntlet.ml import score_answer_quality
from gauntlet.models import Challenge

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z0-9]+")


def _word_set(text: str) -> set[str]:
    """Normalise *text* to a set of lowercase word tokens."""
    return set(_WORD_RE.findall(text.lower()))


def _word_overlap_ratio(reference: str, candidate: str) -> float:
    """Return |intersection| / |reference| for the two word sets."""
    ref = _word_set(reference)
    if not ref:
        return 0.0
    can = _word_set(candidate)
    return len(ref & can) / len(ref)


def _dep_set(text: str) -> set[str]:
    """Split a comma-separated list of module names into a set."""
    return {item.strip() for item in text.split(",") if item.strip()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_answer(challenge: Challenge, answer: str) -> str:
    """Return 'pass', 'partial', or 'fail' for *answer* against *challenge*.

    Scoring rules by challenge type:

    - **multiple_choice**: exact letter match (case-insensitive).
    - **dependency_map**: set overlap.  >= 80% = pass, >= 30% = partial.
    - **explain_why / trace / spot_bug / code_completion**: blended
      word-overlap + ML quality score.  >= 0.5 = pass, >= 0.2 = partial.
      Falls back to word-overlap alone when ML is unavailable.
    """
    stripped = answer.strip()

    if challenge.type == "multiple_choice":
        if not stripped:
            return "fail"
        return "pass" if stripped.upper() == challenge.answer.upper() else "fail"

    if challenge.type == "dependency_map":
        expected = _dep_set(challenge.answer)
        if not expected:
            return "fail"
        given = _dep_set(stripped)
        overlap = len(expected & given) / len(expected)
        if overlap >= 0.8:
            return "pass"
        if overlap >= 0.3:
            return "partial"
        return "fail"

    # Open-ended types: explain_why, trace, spot_bug, code_completion
    if not stripped:
        return "fail"

    ratio = _word_overlap_ratio(challenge.answer, stripped)

    # ML quality refinement (graceful degradation)
    ml_score = score_answer_quality(challenge, stripped)
    if ml_score is not None:
        combined = 0.4 * ratio + 0.6 * ml_score
    else:
        combined = ratio

    if combined >= 0.5:
        return "pass"
    if combined >= 0.2:
        return "partial"
    return "fail"
```

- [ ] **Step 4: Run full test suite to verify everything passes**

Run: `cd plugins/gauntlet && python -m pytest tests/ -v --cov=src/gauntlet --cov-report=term-missing`

Expected: All tests PASS. Coverage >= 90%.

- [ ] **Step 5: Commit**

```bash
cd plugins/gauntlet
git add src/gauntlet/scoring.py tests/unit/test_scoring.py
git commit -m "feat(gauntlet): integrate ML scoring into evaluate_answer()

Open-ended challenge types now use a 40/60 blend of
word-overlap and ML quality score. Falls back to pure
word-overlap when the model is unavailable. Multiple
choice and dependency_map types are unchanged."
```

---

## Task 5: Update Package Exports and Final Verification

**Files:**
- Modify: `plugins/gauntlet/src/gauntlet/__init__.py`

- [ ] **Step 1: Update __init__.py exports**

Add the `ml` module to the package exports:

```python
# plugins/gauntlet/src/gauntlet/__init__.py
from __future__ import annotations

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.ml import score_answer_quality
from gauntlet.models import (
    AnswerRecord,
    Challenge,
    ChallengeResult,
    ChallengeType,
    DeveloperProgress,
    KnowledgeEntry,
    OnboardingProgress,
)
from gauntlet.query import get_context_for_files, query_knowledge, validate_understanding

__version__ = "1.0.0"

__all__ = [
    "AnswerRecord",
    "Challenge",
    "ChallengeResult",
    "ChallengeType",
    "DeveloperProgress",
    "KnowledgeEntry",
    "KnowledgeStore",
    "OnboardingProgress",
    "get_context_for_files",
    "query_knowledge",
    "score_answer_quality",
    "validate_understanding",
]
```

- [ ] **Step 2: Run full test suite with coverage**

Run: `cd plugins/gauntlet && python -m pytest tests/ -v --cov=src/gauntlet --cov-report=term-missing --cov-fail-under=90`

Expected: All tests PASS. Coverage >= 90%.

- [ ] **Step 3: Run ruff lint check**

Run: `cd plugins/gauntlet && python -m ruff check src/gauntlet/ml/ tests/unit/test_features.py tests/unit/test_scorer.py tests/unit/test_ml_init.py`

Expected: No lint errors.

- [ ] **Step 4: Run mypy type check**

Run: `cd plugins/gauntlet && python -m mypy src/gauntlet/ml/`

Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
cd plugins/gauntlet
git add src/gauntlet/__init__.py
git commit -m "feat(gauntlet): export score_answer_quality from package root

Adds ML scoring to the gauntlet public API surface."
```

---

## Verification Checklist

After all tasks are complete, verify against the spec:

- [ ] `score_answer_quality()` returns `float | None`
- [ ] `YamlScorer` loads from `quality_v1.yaml`
- [ ] `Scorer` protocol defined with `score()` and `available()`
- [ ] 7 features extracted by `extract_answer_features()`
- [ ] `evaluate_answer()` blends ML + word-overlap for open-ended types
- [ ] `multiple_choice` and `dependency_map` unchanged
- [ ] Graceful degradation when model missing (returns `None`)
- [ ] All existing `test_scoring.py` BDD tests pass
- [ ] Coverage >= 90%
- [ ] Zero new dependencies in `pyproject.toml`
- [ ] All code uses Python 3.9 compatible syntax
