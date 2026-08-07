"""Is this topic thin, or was the search bad?

The two produce the same observable: few results. Nothing computed from
result counts can separate them, because count is what they share. The
separation comes from a **positive control** measured independently of
result volume, which is the mechanism analytical chemistry uses and
made a precondition for reporting: a batch is not reportable unless a
spiked sample demonstrated the instrument could detect the analyte.

Here the control is a canary query whose target is known to be in the
channel's index. A channel that cannot retrieve it is not reporting on
the world, whatever its topic queries returned. See ADR-0020 for why
capture-recapture and query-performance prediction were rejected in
favor of this.

The strongest verdict is ``THIN_FIELD_CANDIDATE``, never
``THIN_FIELD``. It claims the search was well formed enough to deserve
a human look. It does not claim the literature is empty, and no
mechanism here could support that claim: a field published under
different vocabulary is indistinguishable from an absent one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tome.synthesis.quality import _SKEW_THRESHOLD, CANARY_SOURCE, channel_outcomes

if TYPE_CHECKING:
    from tome.models import ResearchSession

__all__ = [
    "ACT",
    "CANARY_SOURCE",
    "COVERED",
    "DECLINE",
    "DEFER",
    "INCONCLUSIVE",
    "MISMATCH_SUSPECTED",
    "THIN_CANDIDATE",
    "UNDECIDED",
    "ResearchStory",
    "Verdict",
    "canary_outcomes",
    "frontier_stories",
    "frontier_verdict",
]

INCONCLUSIVE = "INCONCLUSIVE"
THIN_CANDIDATE = "THIN_FIELD_CANDIDATE"
MISMATCH_SUSPECTED = "CHANNEL_MISMATCH_SUSPECTED"
COVERED = "COVERED"

# Total findings at or below which a topic is sparse enough to consider.
# unvalidated: no source, not calibrated. Calibration needs the labeled
# corpus in tests/fixtures/frontier/, which needs human-confirmed labels.
_F_THIN = 3

# Outcomes under which a channel's silence says something about the
# topic rather than about the run.
_CLEAN = ("ok", "empty")


@dataclass
class Verdict:
    """A verdict, the reason for it, and the evidence behind it.

    The reason is not decoration. A bare label is the confident-looking
    output this module exists to avoid, and a reader who cannot see the
    evidence cannot disagree with the conclusion.
    """

    verdict: str
    reason: str
    evidence: dict[str, str] = field(default_factory=dict)


def canary_outcomes(session: ResearchSession) -> dict[str, str]:
    """Per planned channel: did its positive control pass?

    ``pass`` the channel retrieved a document known to be in its index.
    ``fail`` it did not, so it cannot be trusted to report absence.
    ``absent`` no control was run, so nothing is known either way.

    ``absent`` is deliberately not ``pass``. Treating a missing control
    as a passing one is how an uninstrumented run acquires the
    authority of an instrumented one.
    """
    outcomes: dict[str, str] = {}
    for channel in session.channels:
        controls = [
            q
            for q in session.query_log
            if q.channel == channel and q.source == CANARY_SOURCE
        ]
        if not controls:
            outcomes[channel] = "absent"
        elif any(q.succeeded and q.result_count > 0 for q in controls):
            outcomes[channel] = "pass"
        else:
            outcomes[channel] = "fail"
    return outcomes


def frontier_verdict(session: ResearchSession) -> Verdict:
    """Classify why this session found what it found.

    Rules, first match wins:

    1. Any planned channel that errored, was rate-limited, or has no
       record at all: ``INCONCLUSIVE``. The run is not evidence.
    2. Any control that failed: ``INCONCLUSIVE``. A blind channel
       cannot testify about absence.
    3. Two or more channels whose controls passed, which searched
       cleanly, with few findings overall: ``THIN_FIELD_CANDIDATE``.
       Any degraded channel demotes this, since partial coverage is not
       a clean probe.
    4. One channel holding most findings while a control-passing
       channel came back empty: ``CHANNEL_MISMATCH_SUSPECTED``. A topic
       living in one venue and not another is more often a vocabulary
       mismatch than a thin field.
    5. Otherwise ``COVERED``.

    What this cannot see, and the docstring says so because the report
    will not:

    - **Vocabulary mismatch.** A field published under other words
      looks exactly like an absent one. Controls prove a channel can
      see; they cannot prove the query used the field's language.
    - **Silent zero-result APIs.** A source answering 200 with an empty
      set for a malformed query is indistinguishable from one with
      nothing to give, unless the agent noticed and said so.
    - **Per-source blindness inside a channel.** ``discourse`` covers
      four sources under one name, so a channel can read clean while
      one of its sources is dead.
    - **Transcription.** Counts reach here through an agent's report of
      its own work. Routing agents through tome's query builders raised
      that bar; it did not remove it.
    """
    outcomes = channel_outcomes(session)
    controls = canary_outcomes(session)

    broken = [c for c in session.channels if outcomes.get(c, "unknown") not in _CLEAN]
    if broken:
        detail = ", ".join(f"{c} ({outcomes.get(c, 'unknown')})" for c in broken)
        return Verdict(
            INCONCLUSIVE,
            f"{len(broken)} channel(s) did not search cleanly, so absence "
            "in this run is evidence about the run rather than the topic.",
            {"channels_not_clean": detail},
        )

    blind = [c for c in session.channels if controls.get(c) == "fail"]
    if blind:
        return Verdict(
            INCONCLUSIVE,
            f"{len(blind)} channel(s) failed a positive control: they could "
            "not retrieve a document known to be in their index, so they "
            "cannot testify about what is absent.",
            {"failed_controls": ", ".join(blind)},
        )

    proven_empty = [
        c
        for c in session.channels
        if controls.get(c) == "pass" and outcomes.get(c) == "empty"
    ]
    unproven = [c for c in session.channels if controls.get(c) == "absent"]
    total = len(session.findings)

    if len(proven_empty) >= 2 and total <= _F_THIN:
        return Verdict(
            THIN_CANDIDATE,
            f"{len(proven_empty)} channels proved they can retrieve, then "
            f"returned nothing for this topic, with {total} finding(s) "
            "overall. Worth a human look. This is a claim about the "
            "search being well formed, not about the literature being "
            "empty: a field published under different words looks the "
            "same from here.",
            {
                "controlled_empty_channels": ", ".join(proven_empty),
                "total_findings": str(total),
            },
        )

    counts: dict[str, int] = {}
    for f in session.findings:
        counts[f.channel] = counts.get(f.channel, 0) + 1
    dominant = [c for c, n in counts.items() if total and n / total > _SKEW_THRESHOLD]
    if dominant and proven_empty:
        return Verdict(
            MISMATCH_SUSPECTED,
            f"{dominant[0]} holds most findings while "
            f"{', '.join(proven_empty)} proved it can retrieve and still "
            "returned nothing. A topic living in one venue and not "
            "another is more often a vocabulary or venue mismatch than a "
            "thin field. Try reformulating for the empty channel before "
            "concluding anything.",
            {"dominant_channel": dominant[0], "empty": ", ".join(proven_empty)},
        )

    # An empty channel with no control is the original conflation in
    # miniature: it came back with nothing and there is no way to tell
    # whether it could have come back with something. Reaching COVERED
    # here because a *different* channel found things would let the
    # working channel vouch for the silent one.
    uncontrolled_empty = [
        c
        for c in session.channels
        if controls.get(c) == "absent" and outcomes.get(c) == "empty"
    ]
    if uncontrolled_empty or (unproven and not total):
        silent = uncontrolled_empty or unproven
        return Verdict(
            INCONCLUSIVE,
            f"{len(silent)} channel(s) returned nothing without running a "
            "positive control, so there is no evidence they could have "
            "returned anything. Their silence carries no weight in either "
            "direction.",
            {"uncontrolled_channels": ", ".join(silent)},
        )

    return Verdict(
        COVERED,
        f"{total} finding(s) across {len(counts)} channel(s); no channel "
        "both proved it can retrieve and came back empty.",
        {"total_findings": str(total)},
    )


# A story's disposition is a judgment about what is worth this
# project's time. Nothing in a search record supports making it, so
# every story arrives here and a person moves it.
UNDECIDED = "undecided"
ACT = "act"
DEFER = "defer"
DECLINE = "decline"


@dataclass
class ResearchStory:
    """A gap worth triaging, with the evidence for it.

    Three kinds, deliberately separated because they route to different
    people. ``thin-field-candidate`` points at the world and is a
    research direction. ``blind-channel`` and ``uncontrolled-channel``
    point at the tooling and are maintenance. Filing them together
    invites someone to read a broken scraper as a finding about a field.
    """

    kind: str
    title: str
    evidence: str
    next_action: str
    disposition: str = UNDECIDED


def frontier_stories(session: ResearchSession) -> list[ResearchStory]:
    """Turn this session's gaps into candidates a human can dispose of.

    A verdict describes one run and scrolls away. The gaps behind it
    outlive the run: a controlled channel that came back empty is a
    research direction, and a channel that failed its control is a
    maintenance task. Both belong in a backlog.

    Returns an empty list when nothing is missing, because a backlog
    that fills up on healthy runs is one nobody reads.
    """
    outcomes = channel_outcomes(session)
    controls = canary_outcomes(session)
    stories: list[ResearchStory] = []

    proven_empty = [
        c
        for c in session.channels
        if controls.get(c) == "pass" and outcomes.get(c) == "empty"
    ]
    if proven_empty:
        stories.append(
            ResearchStory(
                kind="thin-field-candidate",
                title=f"Little published work found on {session.topic!r}",
                evidence=(
                    f"Channels {', '.join(proven_empty)} each retrieved a "
                    "document known to be in their index, then returned "
                    f"nothing for this topic. {len(session.findings)} "
                    "finding(s) overall."
                ),
                next_action=(
                    "Re-run with reformulated vocabulary before treating this "
                    "as a gap in the literature. A field published under other "
                    "words is indistinguishable from an absent one here. If a "
                    "reformulated run is also empty, this is a candidate "
                    "research direction worth an issue."
                ),
            )
        )

    blind = [c for c in session.channels if controls.get(c) == "fail"]
    if blind:
        stories.append(
            ResearchStory(
                kind="blind-channel",
                title=f"Channel(s) failed a positive control: {', '.join(blind)}",
                evidence=(
                    "These channels could not retrieve a document known to be "
                    "in their index, so nothing they returned or failed to "
                    "return is evidence about any topic."
                ),
                next_action=(
                    "Check the channel's query builder and the canary target. "
                    "A stale canary reports a false defect; a real one means "
                    "every recent session using this channel is suspect."
                ),
            )
        )

    unproven = [c for c in session.channels if controls.get(c) == "absent"]
    if unproven:
        stories.append(
            ResearchStory(
                kind="uncontrolled-channel",
                title=f"Channel(s) ran without a control: {', '.join(unproven)}",
                evidence=(
                    "No canary query was recorded, so these channels cannot "
                    "support any claim about absence, however many queries "
                    "they ran."
                ),
                next_action=(
                    "Add a canary target for each channel. Until then their "
                    "silence carries no weight and the verdict stays "
                    "inconclusive whenever they are the evidence."
                ),
            )
        )

    return stories
