"""Tests for the negation-density check.

A regex counts instances. It cannot measure "overly relies on", which
is a property of the document rather than of any one sentence: a page
where most sentences say what something will not do reads as evasive
even when every sentence is individually correct.

The check is advisory by construction. Precise negation is how
contracts and trust boundaries are written, so a high ratio is a
prompt to reread, never a merge gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scribe.negation import (
    DEFAULT_MIN_SENTENCES,
    DEFAULT_THRESHOLD,
    check_negation_density,
)

_NEGATIVE_DOC = """
The parser does not accept nested blocks. It will not recover from a
partial write. The exporter cannot emit CSV. None of the adapters
handle Unicode. The daemon never retries. There is no way to override
the timeout. The cache does not persist. Nothing here is configurable.
"""

_POSITIVE_DOC = """
The parser accepts flat blocks. It recovers from a partial write by
replaying the journal. The exporter emits JSON and Parquet. Every
adapter handles Unicode. The daemon retries three times. The timeout
is set with SCRIBE_TIMEOUT. The cache persists to disk. Each field is
configurable.
"""


class TestDensityIsMeasured:
    """Feature: the check reports a ratio a reader can verify."""

    @pytest.mark.unit
    def test_a_mostly_negative_document_is_flagged(self) -> None:
        """Scenario: most sentences say what the thing will not do."""
        findings = check_negation_density(_NEGATIVE_DOC)
        assert len(findings) == 1
        assert findings[0].ratio > DEFAULT_THRESHOLD

    @pytest.mark.unit
    def test_a_positive_document_is_clean(self) -> None:
        """Scenario: the same facts stated positively raise nothing."""
        assert check_negation_density(_POSITIVE_DOC) == []

    @pytest.mark.unit
    def test_the_finding_carries_its_own_arithmetic(self) -> None:
        """Scenario: the reader can check the number without rerunning."""
        finding = check_negation_density(_NEGATIVE_DOC)[0]
        assert finding.total_sentences >= DEFAULT_MIN_SENTENCES
        assert 0 < finding.negative_sentences <= finding.total_sentences
        assert finding.ratio == pytest.approx(
            finding.negative_sentences / finding.total_sentences
        )
        assert str(finding.negative_sentences) in finding.detail


class TestSmallSamplesAreNotJudged:
    """Feature: a short passage cannot be over-reliant on anything."""

    @pytest.mark.unit
    def test_below_the_sentence_floor_nothing_is_reported(self) -> None:
        """Scenario: two negative sentences are a coincidence, not a habit."""
        assert check_negation_density("It does not work. It cannot run.") == []

    @pytest.mark.unit
    def test_empty_text_is_clean(self) -> None:
        """Scenario: no sentences means no ratio to compute."""
        assert check_negation_density("") == []


class TestCodeDoesNotCount:
    """Feature: negation inside code is syntax, not prose."""

    @pytest.mark.unit
    def test_fenced_code_is_excluded(self) -> None:
        """Scenario: a fence full of `not` does not move the ratio."""
        prose = (
            _POSITIVE_DOC
            + """
```python
if not ready and not started and not done:
    raise RuntimeError("not ready")
```
"""
        )
        assert check_negation_density(prose) == []

    @pytest.mark.unit
    def test_inline_code_is_excluded(self) -> None:
        """Scenario: `not None` in a sentence is a symbol, not a stance."""
        text = _POSITIVE_DOC.replace(
            "The cache persists to disk.",
            "The cache persists when `value is not None` and `not stale`.",
        )
        assert check_negation_density(text) == []


class TestThresholdIsCallerControlled:
    """Feature: the bar is an argument, so an audit can tighten it."""

    @pytest.mark.unit
    def test_a_stricter_threshold_flags_a_lightly_negative_document(self) -> None:
        """Scenario: lowering the bar surfaces even sparse negation.

        The document below clears the default bar with one negative
        sentence in eight. An audit that wants every instance sets the
        threshold to zero and gets it.
        """
        mixed = _POSITIVE_DOC.replace(
            "The cache persists to disk.",
            "The cache does not persist across restarts.",
        )
        assert check_negation_density(mixed) == []
        assert check_negation_density(mixed, threshold=0.0)

    @pytest.mark.unit
    def test_a_looser_threshold_clears_a_negative_document(self) -> None:
        """Scenario: raising the bar past 1.0 can never fire."""
        assert check_negation_density(_NEGATIVE_DOC, threshold=1.01) == []
