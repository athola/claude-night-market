"""Validation for the frontier verdict, by replay and by sabotage.

Feature: The verdict is checked against inputs whose right answer is known.

As someone deciding whether to trust a THIN_FIELD_CANDIDATE
I want the verdict tested against deliberately broken runs
So that a signal which ignores its own controls cannot ship green

Two halves, and only one of them exists yet.

The **negative controls** below need no human labels, because their
expected answer follows from the rule rather than from anyone's opinion
about a field: a run with an injected rate limit must not yield a claim
about the world, and a session with no query record must not either.
These are what actually catch a signal that has stopped reading its
inputs, and they run today.

The **labeled corpus** in ../fixtures/frontier/labels.yaml is a
proposal awaiting human confirmation, with no recorded envelopes yet.
Nothing here asserts against those labels. Calibrating `_F_THIN`
against labels the model drafted for its own signal would be the
generator judging itself, which the repo evidence bar forbids, and
doing it silently would be worse than not doing it.

Replay, not live dispatch: agent runs are nondeterministic and
rate-limited, so validation reads recorded envelopes and exercises
parse_envelope, channel_outcomes and frontier_verdict as pure
functions. Reproducible, no network, runs in CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tome.models import Finding, ResearchSession
from tome.synthesis.frontier import (
    CANARY_SOURCE,
    INCONCLUSIVE,
    MISMATCH_SUSPECTED,
    THIN_CANDIDATE,
    frontier_verdict,
    retrieved_findings,
)
from tome.synthesis.quality import parse_envelope

FIXTURES = Path(__file__).parents[1] / "fixtures" / "frontier"
LABELS = FIXTURES / "labels.yaml"


def _load_labels() -> dict:
    return yaml.safe_load(LABELS.read_text(encoding="utf-8"))


def _session_from_envelopes(topic: str, envelopes: list[dict]) -> ResearchSession:
    """Rebuild a session from recorded agent envelopes."""
    session = ResearchSession(
        topic=topic,
        domain="software",
        triz_depth="light",
        channels=[e["channel"] for e in envelopes],
    )
    for envelope in envelopes:
        session.query_log.extend(parse_envelope(envelope))
        # Findings come from the recorded findings array and from
        # nowhere else. Synthesizing them from
        # metadata.queries[].result_count would be the tempting
        # shortcut and would quietly void the corpus: those counts
        # already drive channel_outcomes, so a total derived from them
        # would make the sparsity test and the outcome test functions
        # of one input. They would then agree by construction rather
        # than by evidence, and the confusion matrix would be scoring
        # a tautology.
        session.findings.extend(
            Finding.from_dict(f) for f in envelope.get("findings") or []
        )
    return session


def _envelope(
    channel: str, *, results: int, canary: bool = True, findings: int = 0
) -> dict:
    """A recorded-shaped envelope, with an optional passing control.

    ``results`` is what the query returned and ``findings`` is how many
    of those the agent chose to report. They are separate arguments
    because they are separate facts: agents cap their finding lists
    ("at most 10", "top 2-3 posts"), so the two numbers routinely
    disagree in a real recording, and a helper that derived one from
    the other would hide the gap the corpus is meant to expose.
    """
    queries = [
        {
            "source": channel,
            "query": f"topic query for {channel}",
            "result_count": results,
            "error": None,
        }
    ]
    if canary:
        queries.insert(
            0,
            {
                "source": CANARY_SOURCE,
                "query": "known-indexed target",
                "result_count": 1,
                "error": None,
            },
        )
    return {
        "channel": channel,
        "findings": [
            {
                "source": channel,
                "channel": channel,
                "title": f"{channel} finding {i}",
                "url": f"https://example.invalid/{channel}/{i}",
                "relevance": 0.5,
                "summary": "",
            }
            for i in range(findings)
        ],
        "errors": [],
        "metadata": {"query_count": len(queries), "queries": queries},
    }


class TestNegativeControls:
    """Feature: Deliberately broken runs must not produce claims."""

    @pytest.mark.unit
    def test_injected_rate_limit_flips_to_inconclusive(self) -> None:
        """Scenario: A rate limit voids a would-be thin-field claim.

        Given two controlled channels that came back empty
        And a verdict of THIN_FIELD_CANDIDATE
        When one channel's envelope is rewritten to carry a rate limit
        Then the verdict becomes INCONCLUSIVE
        Because if it does not, the signal is not reading its errors,
             and a rate-limited run would be published as a statement
             about the literature.
        """
        clean = [_envelope("code", results=0), _envelope("academic", results=0)]
        assert (
            frontier_verdict(_session_from_envelopes("t", clean)).verdict
            == THIN_CANDIDATE
        )

        sabotaged = json.loads(json.dumps(clean))
        sabotaged[1]["metadata"]["queries"][-1]["error"] = "rate_limit"
        assert (
            frontier_verdict(_session_from_envelopes("t", sabotaged)).verdict
            == INCONCLUSIVE
        )

    @pytest.mark.unit
    def test_removing_the_controls_flips_to_inconclusive(self) -> None:
        """Scenario: Stripping controls removes the licence to claim.

        Given a run that reached THIN_FIELD_CANDIDATE
        When its canary queries are deleted and nothing else changes
        Then the verdict becomes INCONCLUSIVE
        Because this isolates the control as the load-bearing input.
             The counts are identical across the two runs, so anything
             that still claims a thin field is deciding on counts.
        """
        controlled = [_envelope("code", results=0), _envelope("academic", results=0)]
        uncontrolled = [
            _envelope("code", results=0, canary=False),
            _envelope("academic", results=0, canary=False),
        ]
        assert (
            frontier_verdict(_session_from_envelopes("t", controlled)).verdict
            == THIN_CANDIDATE
        )
        assert (
            frontier_verdict(_session_from_envelopes("t", uncontrolled)).verdict
            == INCONCLUSIVE
        )

    @pytest.mark.unit
    def test_legacy_session_never_claims_a_thin_field(self) -> None:
        """Scenario: A session with no query record claims nothing.

        Given a session persisted before query logging existed
        Then the verdict is INCONCLUSIVE
        Because every historical session on disk looks like this, and a
             signal that read their silence as a thin field would
             retroactively invent findings for all of them.
        """
        legacy = ResearchSession(
            topic="t", domain="d", triz_depth="light", channels=["code", "academic"]
        )
        assert frontier_verdict(legacy).verdict == INCONCLUSIVE

    @pytest.mark.unit
    def test_failed_control_beats_a_clean_count(self) -> None:
        """Scenario: A blind channel voids an otherwise clean run.

        Given two channels whose topic queries ran cleanly and empty
        And one whose control could not retrieve its known target
        Then the verdict is INCONCLUSIVE
        Because the counts alone would say thin field, and the control
             is the only thing objecting.
        """
        envelopes = [_envelope("code", results=0), _envelope("academic", results=0)]
        envelopes[1]["metadata"]["queries"][0]["result_count"] = 0  # canary misses
        assert (
            frontier_verdict(_session_from_envelopes("t", envelopes)).verdict
            == INCONCLUSIVE
        )


class TestLabeledCorpusIsWellFormed:
    """Feature: The corpus is usable the moment labels are confirmed."""

    @pytest.mark.unit
    def test_corpus_names_the_human_who_confirmed_it(self) -> None:
        """Scenario: A confirmed corpus says who confirmed it.

        Given the labels fixture, confirmed on 2026-08-07
        Then it names a confirming human and is not the model's own word
        Because every label was drafted by the model that also wrote
             the verdict being tested. The confirmation is what makes
             the corpus admissible, so a status of confirmed with no
             name attached would restore exactly the
             generator-judging-itself arrangement it was meant to end.

        This replaced test_corpus_declares_itself_unconfirmed, whose
        failure on confirmation was the designed cue to get here.
        """
        labels = _load_labels()
        assert labels["status"] == "confirmed"
        confirmed_by = labels["confirmed_by"]
        assert confirmed_by, "status is confirmed but no human is named"
        assert confirmed_by != labels["drafted_by"], (
            "the drafter cannot be the confirmer"
        )

    @pytest.mark.unit
    def test_the_feature_s_own_motivating_topic_is_not_labeled_thin(self) -> None:
        """Scenario: The design does not grade its own premise.

        Given canary-queries-retrieval-health, the topic the canary
             feature was built to vindicate
        Then it is not in the thin class
        Because a corpus that labels the author's motivating example
             thin cannot be used to validate the signal that calls
             things thin. It sits in covered-obscure instead, where the
             expectation runs against the design: the work exists under
             matrix spikes, system suitability, known-item search and
             synthetic monitoring, so a THIN_FIELD_CANDIDATE here is
             the signal failing on the case its author most wanted it
             to pass.
        """
        entry = next(
            e
            for e in _load_labels()["topics"]
            if e["slug"] == "canary-queries-retrieval-health"
        )
        assert entry["label"] != "thin", (
            "the feature's motivating topic is labeled thin by the feature's "
            "own corpus; that is the circularity this test exists to block"
        )

    @pytest.mark.unit
    def test_every_topic_has_a_class_and_a_reason(self) -> None:
        """Scenario: No label arrives without its justification."""
        valid = {"covered", "covered-obscure", "thin"}
        for entry in _load_labels()["topics"]:
            assert entry["label"] in valid, entry["slug"]
            assert entry["why"].strip(), entry["slug"]
            assert entry["topic"].strip(), entry["slug"]

    @pytest.mark.unit
    def test_all_three_classes_are_represented(self) -> None:
        """Scenario: The adversarial class is not quietly missing.

        Given the corpus
        Then covered-obscure has at least five entries
        Because it is the class the design is known to fail on, and a
             corpus without it would report a flattering accuracy that
             means nothing.
        """
        counts: dict[str, int] = {}
        for entry in _load_labels()["topics"]:
            counts[entry["label"]] = counts.get(entry["label"], 0) + 1
        assert counts.get("covered-obscure", 0) >= 5, counts
        assert counts.get("thin", 0) >= 5, counts
        assert counts.get("covered", 0) >= 5, counts

    @pytest.mark.unit
    def test_no_envelopes_are_recorded_yet(self) -> None:
        """Scenario: The corpus is honest about being unrun.

        Given the fixtures directory
        Then it holds labels but no recorded envelopes
        And this test is the one to delete when recording begins
        Because a half-recorded corpus scored against confirmed labels
             would produce a real-looking confusion matrix over a
             biased subset.
        """
        recorded = sorted(p.name for p in FIXTURES.glob("*.json"))
        assert recorded == [], (
            f"envelopes recorded ({recorded}); replace this test with the "
            "confusion-matrix run and calibrate _F_THIN"
        )


class TestReplayCarriesFindings:
    """Feature: Recorded findings survive the trip back into a session.

    ``_session_from_envelopes`` rebuilt only the query log. Findings
    recorded in an envelope were dropped at the replay boundary, so
    every replayed session had ``total = 0`` regardless of what its
    envelopes held.

    The effect is asymmetric, which is why it survived. A covered topic
    still lands on COVERED: every channel reads ``ok``, nothing is
    ``proven_empty``, and the verdict falls through before the count is
    consulted. The bug bites only where exactly two of three retrieval
    channels are controlled-empty, which is the one band where
    ``_F_THIN`` changes any answer, and there it forced
    THIN_FIELD_CANDIDATE over CHANNEL_MISMATCH_SUSPECTED
    unconditionally.

    That is precisely the cell the labeled corpus exists to measure. A
    matrix scored on the unfixed harness would have looked plausible
    and been wrong exactly where it counted.
    """

    @pytest.mark.unit
    def test_recorded_findings_reach_the_verdict(self) -> None:
        """Scenario: An envelope's findings are not dropped on replay.

        Given an envelope recording four findings
        When the session is rebuilt from it
        Then retrieved_findings sees four
        Because everything downstream of this counts them, and a replay
             that silently returns zero makes the corpus unscoreable
             while still producing a confident-looking table.
        """
        session = _session_from_envelopes(
            "t", [_envelope("code", results=4, findings=4)]
        )
        assert len(retrieved_findings(session)) == 4

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "recorded,expected",
        [(3, THIN_CANDIDATE), (4, MISMATCH_SUSPECTED)],
    )
    def test_the_band_where_the_threshold_discriminates(
        self, recorded: int, expected: str
    ) -> None:
        """Scenario: Two controlled-empty channels, one holding findings.

        Given academic and discourse proved they retrieve, then found nothing
        And code holds `recorded` findings
        Then the verdict flips from thin to mismatch across _F_THIN
        Because this is the only input shape in which the constant
             changes an answer. Three of three empty yields THIN at any
             threshold, and one of three never reaches the branch. If
             the corpus is ever scored, it is scored here, so this band
             is the one that must not be replayed wrong.
        """
        session = _session_from_envelopes(
            "t",
            [
                _envelope("academic", results=0),
                _envelope("discourse", results=0),
                _envelope("code", results=recorded, findings=recorded),
            ],
        )
        assert frontier_verdict(session).verdict == expected

    @pytest.mark.unit
    def test_generated_findings_do_not_return_through_replay(self) -> None:
        """Scenario: A recorded triz envelope still does not vote.

        Given a triz envelope recording four generated analogies
        Then retrieved_findings ignores them
        Because RETRIEVAL_CHANNELS closed this leak in the verdict, and
             a replay path that re-counted them would reopen it from
             the fixtures instead of from a live run. The corpus must
             not be able to restore a hole the code removed.
        """
        session = _session_from_envelopes(
            "t", [_envelope("triz", results=4, findings=4)]
        )
        assert retrieved_findings(session) == []
