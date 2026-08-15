"""Positive controls: can this channel retrieve at all?

A channel that returns nothing has told you one of two things and you
cannot tell which. Either the topic is thin, or the channel is blind.
Analytical chemistry settles the same ambiguity by running a spiked
sample: an instrument that cannot detect a known quantity of analyte
does not get to report that a sample contained none.

A canary is that spike. It asks the channel for one document known to
be in its index, through the same endpoint the channel uses for real
queries. Retrieved, and the channel's silence on the topic is evidence.
Not retrieved, and nothing the channel said is evidence about anything.

Two properties do the work, and both are load-bearing:

**Identifier anchored.** ``canary_outcomes`` only checks whether a
result came back, so the query must be one that nothing but the target
can satisfy: an arXiv id, a ``repo:`` qualifier, a story tag. A
free-text canary would be answered by any index with a default feed,
including a broken one, which hands a blind channel the authority of a
sighted one.

**Constant.** The canary takes no topic. A control that varied with
the search it audits would drift alongside the thing it is supposed to
measure independently.

Targets are verified against the live services before being recorded
here, because a stale target reports a defect in a healthy channel and
sends a maintainer after the wrong thing.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CANARY_TARGETS",
    "CanaryTarget",
    "build_canary_query",
    "describe_canary_target",
]


@dataclass(frozen=True)
class CanaryTarget:
    """One channel's positive control.

    ``expected`` is prose on purpose. When a control fails, the first
    question is whether the channel broke or the target moved, and a
    maintainer answers it by opening the URL and comparing what came
    back against what should have. A URL alone does not support that.
    """

    channel: str
    url: str
    expected: str
    verified_on: str


# Verified live on 2026-08-07. Re-verify before trusting a failure:
# these are third-party services and a moved target is indistinguishable
# from a broken channel from inside the verdict.
#
# Semantic Scholar is the academic channel's other source and is not
# used here. It answered 429 during verification, and a canary that
# fails on rate limits would report a blind channel every time the API
# throttles, which is a loud false positive on the one signal that is
# supposed to be trustworthy. arXiv covers the channel; per-source
# blindness inside a channel is a known and documented gap.
CANARY_TARGETS: dict[str, CanaryTarget] = {
    "academic": CanaryTarget(
        channel="academic",
        # id_list, not search_query: the free-text matcher can return
        # neighbours of a missing paper, which would pass a control
        # that the target itself failed.
        url="https://export.arxiv.org/api/query?id_list=1706.03762",
        expected=(
            "One Atom entry whose title is 'Attention Is All You Need' "
            "(arXiv:1706.03762). Zero entries means arXiv did not serve a "
            "paper that has been in its index since 2017."
        ),
        verified_on="2026-08-07",
    ),
    "code": CanaryTarget(
        channel="code",
        # The repo: qualifier restricts the search to one repository,
        # so total_count is 1 or 0 and never a partial match.
        url="https://api.github.com/search/repositories?q=repo:torvalds/linux",
        expected=(
            "JSON with total_count 1 and items[0].full_name 'torvalds/linux'. "
            "A total_count of 0 means repository search did not return the "
            "most-starred repository on the platform."
        ),
        verified_on="2026-08-07",
    ),
    "discourse": CanaryTarget(
        channel="discourse",
        # tags=story_<id> pins the result set to a single story rather
        # than matching its words.
        url="https://hn.algolia.com/api/v1/search?tags=story_1",
        expected=(
            "JSON with one hit, title 'Y Combinator', author 'pg': the first "
            "story on Hacker News. An empty hits array means Algolia did not "
            "serve story 1."
        ),
        verified_on="2026-08-07",
    ),
}


def build_canary_query(channel: str) -> str:
    """The URL to fetch as this channel's positive control.

    Args:
        channel: A retrieval channel name. Takes no topic, deliberately:
            see the module docstring on why a control must be constant.

    Returns:
        An absolute https URL suitable for a WebFetch call.

    Raises:
        KeyError: if the channel has no control. Generative channels
            have no index to probe, and a caller asking for one has
            confused the two kinds. Raising beats returning a
            placeholder URL that would be recorded as a passing
            control.
    """
    try:
        return CANARY_TARGETS[channel].url
    except KeyError:
        raise KeyError(
            f"no canary target for channel {channel!r}; controls are defined "
            f"only for retrieval channels {sorted(CANARY_TARGETS)}. A channel "
            "that does not search an index cannot be asked to retrieve a "
            "document known to be in one."
        ) from None


def describe_canary_target(channel: str) -> str:
    """What a passing control should have returned, in prose.

    Used when a control fails, to tell a broken channel apart from a
    target that moved.

    Raises:
        KeyError: as ``build_canary_query``.
    """
    try:
        target = CANARY_TARGETS[channel]
    except KeyError:
        raise KeyError(
            f"no canary target for channel {channel!r}; "
            f"defined for {sorted(CANARY_TARGETS)}"
        ) from None
    return f"{target.expected} (target verified {target.verified_on})"
