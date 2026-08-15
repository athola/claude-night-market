"""A control that any result can satisfy is not a control.

Feature: Each retrieval channel has a positive control it can run.

As someone deciding whether a channel's silence means anything
I want a query whose target is known to sit in that channel's index
So that a zero from the channel is a fact about the topic, not the tool

``canary_outcomes`` asks only whether the control returned a result. So
the control has to be written such that a result can come from nothing
but the intended target. A free-text canary like "machine learning"
returns hits from any half-working index and from a broken one that
falls back to a default feed, which would hand a blind channel the
authority of a sighted one: precisely the failure the control exists
to catch.

Every target here is anchored on an identifier rather than on words:
an arXiv id, a GitHub ``repo:`` qualifier, a Hacker News story tag. It
must also run through the same endpoint the channel uses for real
queries. A canary that probes a different endpoint proves that some
other service is up.

Targets verified live on 2026-08-07:

- arXiv ``id_list=1706.03762`` returned "Attention Is All You Need".
- GitHub ``repo:torvalds/linux`` returned ``total_count: 1``.
- HN Algolia ``tags=story_1`` returned the "Y Combinator" story.

Semantic Scholar is the academic channel's other source and answered
429 from the verification environment. It is deliberately not the
academic canary: an unverified target that fails intermittently would
report a blind channel on every rate limit.
"""

from __future__ import annotations

import inspect
import re
from urllib.parse import urlparse

import pytest

from tome.channels.canary import (
    CANARY_TARGETS,
    build_canary_query,
    describe_canary_target,
)
from tome.models import RETRIEVAL_CHANNELS


class TestEveryRetrievalChannelCanBeControlled:
    """Scenario: The control mechanism is runnable, not aspirational."""

    def test_every_retrieval_channel_has_a_target(self) -> None:
        """
        Given the channels whose silence a verdict may rest on
        Then each has a canary target defined

            A retrieval channel with no target can never move off
            ``absent``, which makes every verdict inconclusive forever.
            That was the state this test was written to end.
        """
        assert set(CANARY_TARGETS) == set(RETRIEVAL_CHANNELS)

    def test_no_target_is_defined_for_a_generative_channel(self) -> None:
        """
        Given triz, which generates rather than retrieves
        Then it has no canary target

            "A document known to be in the index" is not merely unknown
            for a channel with no index, it is malformed. Defining one
            anyway would invite a maintainer to wire a control that
            cannot mean what the others mean.
        """
        assert "triz" not in CANARY_TARGETS

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_the_query_is_a_fetchable_https_url(self, channel: str) -> None:
        """
        Given a retrieval channel
        Then its canary query is an absolute https URL

            The agent passes this straight to WebFetch. A bare query
            string would need the agent to assemble an endpoint, which
            is the freehand step routing through tome removed.
        """
        parsed = urlparse(build_canary_query(channel))
        assert parsed.scheme == "https", f"{channel} canary is not https"
        assert parsed.netloc, f"{channel} canary has no host"


class TestTargetsAreIdentifierAnchored:
    """Scenario: Only the intended document can satisfy the control."""

    # The identifier that must appear in each channel's canary URL, and
    # which no topic query would produce.
    _ANCHORS = {
        "academic": "1706.03762",
        "code": "torvalds/linux",
        "discourse": "story_1",
    }

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_the_query_names_a_specific_document(self, channel: str) -> None:
        """
        Given a canary query
        Then it contains the identifier of one known document

            This is the property that makes ``result_count > 0`` mean
            "retrieved the target" rather than "returned something".
        """
        query = build_canary_query(channel)
        anchor = self._ANCHORS[channel]
        assert anchor in query.replace("%2F", "/").replace("+", " "), (
            f"{channel} canary is not anchored on {anchor!r}: {query}"
        )

    def test_the_query_carries_no_free_text_topic_terms(self) -> None:
        """
        Given the canary builder
        Then it takes the channel and nothing else

            A canary is a constant. One that took a topic argument
            would drift with the search it is supposed to audit
            independently, and a control that moves with the thing it
            measures cannot measure it.
        """
        sig = inspect.signature(build_canary_query)
        assert list(sig.parameters) == ["channel"], (
            "build_canary_query must depend on nothing but the channel"
        )

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_the_target_is_described_for_a_human(self, channel: str) -> None:
        """
        Given a canary target
        Then a human-readable description of the expected document exists

            When a control fails, the first question is whether the
            channel broke or the target moved. A description of what
            should have come back is what lets a maintainer tell those
            apart without reverse-engineering a URL.
        """
        described = describe_canary_target(channel)
        assert described and len(described) > 20, (
            f"{channel} target has no usable description"
        )


class TestCanaryEndpointsMatchTheChannelsTheyAudit:
    """Scenario: A control proves the channel works, not that a host is up."""

    _EXPECTED_HOSTS = {
        "academic": "export.arxiv.org",
        "code": "api.github.com",
        "discourse": "hn.algolia.com",
    }

    @pytest.mark.parametrize("channel", sorted(RETRIEVAL_CHANNELS))
    def test_the_canary_hits_the_same_host_the_channel_searches(
        self, channel: str
    ) -> None:
        """
        Given a canary query for a channel
        Then it targets the host that channel's real queries use

            A canary against a different service reports on that
            service. The control has to travel the same path as the
            search whose silence it is vouching for.
        """
        host = urlparse(build_canary_query(channel)).netloc
        assert host == self._EXPECTED_HOSTS[channel]

    def test_the_arxiv_canary_uses_the_id_list_parameter(self) -> None:
        """
        Given the academic canary
        Then it uses arXiv's id_list lookup rather than search_query

            ``search_query`` runs the free-text matcher, which can
            return neighbours of a missing paper. ``id_list`` returns
            that document or nothing, which is the exact-match
            behaviour the control needs.
        """
        assert re.search(r"[?&]id_list=", build_canary_query("academic"))
