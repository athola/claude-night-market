"""Score the corpus with a harness built before the results exist.

Feature: The frontier verdict is scored against human labels, offline.

As someone deciding whether to trust a THIN_FIELD_CANDIDATE
I want the verdict scored against a labeled corpus and a threshold sweep
So that the signal's error rate is measured rather than asserted

Three numbers, and the second is the one that matters.

**The confusion matrix** of human label against verdict, over whatever
topics are recorded.

**The false-THIN rate on the adversarial class.** ``covered-obscure``
topics are abundantly published under vocabulary the obvious query
misses. No mechanism in the design detects vocabulary mismatch, so some
of these will read THIN. ``labels.yaml`` names that rate "the bound on
the signal's value". It is the honest headline.

**The threshold sweep.** ``_F_THIN`` changes a verdict only when
exactly two of three retrieval channels are controlled-empty and the
third holds few findings. Sweeping it over a range and reporting how
many verdicts move is what "calibrated" can honestly mean here. If the
answer is "none, across the whole range", that is a finding about the
constant rather than a failure to tune it.

This harness is written before the corpus is recorded, on purpose. A
scorer built while looking at results is a scorer shaped by the results
its author wanted, and the corpus header already warns that this
signal's author is the same model that drafted its labels.

No numeric accuracy is asserted anywhere in this file. Thresholds in a
test would enshrine a calibration through the back door and turn honest
degradation into a red build. The tests hold the harness's shape; the
numbers live in the report.
"""

from __future__ import annotations

import pytest

from tome.metrics.frontier_matrix import (
    MatrixReport,
    RecordedTopic,
    score_corpus,
    sweep_threshold,
)
from tome.synthesis.frontier import (
    CANARY_SOURCE,
    COVERED,
    MISMATCH_SUSPECTED,
    THIN_CANDIDATE,
)


def _envelope(channel: str, *, results: int, findings: int = 0) -> dict:
    queries = [
        {
            "source": CANARY_SOURCE,
            "query": "known-indexed target",
            "result_count": 1,
            "error": None,
        },
        {
            "source": channel,
            "query": f"topic query for {channel}",
            "result_count": results,
            "error": None,
        },
    ]
    return {
        "channel": channel,
        "findings": [
            {
                "source": channel,
                "channel": channel,
                "title": f"{channel}-{i}",
                "url": f"https://example.invalid/{channel}/{i}",
                "relevance": 0.5,
                "summary": "",
            }
            for i in range(findings)
        ],
        "errors": [],
        "metadata": {"query_count": len(queries), "queries": queries},
    }


def _topic(slug: str, label: str, *, third: int) -> RecordedTopic:
    """A topic in the band where the threshold discriminates.

    Two channels controlled and empty, the third holding ``third``
    findings. Outside this band the constant is inert, so a fixture
    built anywhere else would make the sweep look flat for the wrong
    reason.
    """
    return RecordedTopic(
        slug=slug,
        topic=f"topic {slug}",
        label=label,
        envelopes=[
            _envelope("academic", results=0),
            _envelope("discourse", results=0),
            _envelope("code", results=third, findings=third),
        ],
    )


class TestScoringACorpus:
    """Scenario: Recorded topics become a label-by-verdict matrix."""

    def test_an_empty_corpus_scores_without_pretending(self) -> None:
        """
        Given no topics recorded
        Then the report renders and says nothing was scored

            The harness ships before the corpus. One that crashed or,
            worse, printed a 0.0 error rate on zero topics would be
            read as a result.
        """
        report = score_corpus([], n_labeled=23)
        assert report.n_recorded == 0
        assert report.n_labeled == 23
        rendered = report.render()
        assert "0/23" in rendered

    def test_the_matrix_counts_label_against_verdict(self) -> None:
        """
        Given one thin topic whose verdict is THIN_FIELD_CANDIDATE
        Then the matrix records that pairing
        """
        report = score_corpus([_topic("a", "thin", third=0)], n_labeled=1)
        assert report.matrix[("thin", THIN_CANDIDATE)] == 1

    def test_the_report_names_the_topics_behind_each_cell(self) -> None:
        """
        Given a scored corpus
        Then each cell can be traced back to the topics in it

            A rate with no way back to the runs behind it cannot be
            disagreed with, which is the property this whole feature
            was built to avoid in the verdict itself.
        """
        report = score_corpus(
            [_topic("a", "thin", third=0), _topic("b", "thin", third=0)],
            n_labeled=2,
        )
        assert sorted(report.topics_in(("thin", THIN_CANDIDATE))) == ["a", "b"]


class TestTheAdversarialClassRate:
    """Scenario: The bound on the signal's value is computed, not asserted."""

    def test_a_covered_obscure_topic_reading_thin_is_counted_against(self) -> None:
        """
        Given a covered-obscure topic the verdict calls THIN
        Then the false-THIN rate reflects it

            This is the failure the design knows it cannot detect: a
            field published under other words looks exactly like an
            absent one. Measuring the rate is the whole point of the
            adversarial class.
        """
        report = score_corpus([_topic("a", "covered-obscure", third=0)], n_labeled=1)
        assert report.false_thin_rate == 1.0

    def test_a_covered_obscure_topic_reading_otherwise_is_not(self) -> None:
        """
        Given a covered-obscure topic the verdict does not call THIN
        Then the false-THIN rate is zero
        """
        report = score_corpus([_topic("a", "covered-obscure", third=9)], n_labeled=1)
        assert report.false_thin_rate == 0.0

    def test_the_rate_is_none_when_the_class_is_unrecorded(self) -> None:
        """
        Given no covered-obscure topics recorded
        Then the rate is None rather than zero

            Zero would read as "the signal never fails on the
            adversarial class", which is the opposite of "the
            adversarial class was not tested".
        """
        report = score_corpus([_topic("a", "thin", third=0)], n_labeled=1)
        assert report.false_thin_rate is None


class TestTheThresholdSweep:
    """Scenario: How much the constant actually moves the answer."""

    def test_the_sweep_reports_a_verdict_distribution_per_threshold(self) -> None:
        """
        Given a topic in the discriminating band with 3 findings
        Then the sweep shows the verdict changing across the threshold

            Two controlled-empty channels and a third holding 3: below
            the threshold this is THIN, at or above it the third
            channel dominates and it is MISMATCH. This is the only
            shape in which the constant does anything.
        """
        sweep = sweep_threshold([_topic("a", "thin", third=3)], thresholds=range(0, 6))
        assert sweep[0]["a"] == MISMATCH_SUSPECTED
        assert sweep[3]["a"] == THIN_CANDIDATE

    def test_a_topic_outside_the_band_is_flat_across_the_sweep(self) -> None:
        """
        Given a covered topic where no channel is controlled-empty
        Then its verdict is identical at every threshold

            The negative half. If everything looked flat the sweep
            would be measuring nothing, so at least one shape has to
            move and at least one has to hold still.
        """
        covered = RecordedTopic(
            slug="c",
            topic="covered",
            label="covered",
            envelopes=[
                _envelope("academic", results=5, findings=5),
                _envelope("discourse", results=5, findings=5),
                _envelope("code", results=5, findings=5),
            ],
        )
        sweep = sweep_threshold([covered], thresholds=range(0, 6))
        assert {s["c"] for s in sweep.values()} == {COVERED}

    def test_the_sweep_is_rendered_with_the_band_explained(self) -> None:
        """
        Given a rendered report
        Then it states when the constant discriminates at all

            A reader seeing a flat sweep needs to know whether the
            constant is inert in general or merely inert on this
            corpus, and those have different consequences.
        """
        report = score_corpus([_topic("a", "thin", third=3)], n_labeled=1)
        rendered = report.render()
        assert "controlled-empty" in rendered


class TestTheReportRefusesToOverclaim:
    """Scenario: One nondeterministic sample per topic is not an accuracy."""

    @pytest.mark.parametrize(
        "caveat", ["one recorded run", "not a repeatable accuracy"]
    )
    def test_the_report_carries_its_own_caveats(self, caveat: str) -> None:
        """
        Given any rendered report
        Then it says what the numbers are not

            Each topic is recorded once, from a nondeterministic,
            rate-limited pipeline. The matrix measures the pipeline and
            the verdict jointly. A reader who takes it for a property
            of the verdict function will over-trust it exactly as much
            as this project's own evidence bar forbids.
        """
        report = score_corpus([_topic("a", "thin", third=0)], n_labeled=1)
        assert caveat in report.render().lower()

    def test_the_report_is_a_matrix_report(self) -> None:
        """Scenario: score_corpus returns the documented type."""
        assert isinstance(score_corpus([], n_labeled=0), MatrixReport)
