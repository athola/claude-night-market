"""Channel cards: one typed record per research channel.

Adapted from the tool cards in OctoTools (arXiv 2502.11271), where each
tool carries its input and output contract, demonstrations, limitations,
and best practices, and the planner and verifier read that metadata
rather than knowing tools by name.

The card fields are typed rather than a free dict because OctoTools'
dict drifted: its shipped tools spell the key ``limitation``,
``limitations``, ``best_practice`` and ``best_practices``, and its
planner prompt asks the model to read "limitations" from whichever
spelling a tool used. A dataclass turns that drift into a ``TypeError``
at import.

The cards restate facts owned elsewhere (``RETRIEVAL_CHANNELS``,
``CANARY_TARGETS``, the agent files). ``tests/unit/test_channel_cards.py``
holds them in agreement, so a card cannot describe a pipeline that no
longer exists.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["CHANNEL_CARDS", "DEPTH_ORDER", "ChannelCard", "get_card", "render_card"]

# Depth ordinal used for channel gating. Owned here because the cards
# are what the planner gates on.
DEPTH_ORDER: dict[str, int] = {
    "light": 0,
    "medium": 1,
    "deep": 2,
    "maximum": 3,
}

_KINDS = ("retrieval", "generative")


@dataclass(frozen=True)
class ChannelCard:
    """What a channel is for, when to run it, and where it is blind.

    ``kind`` separates channels that search an external index
    (``retrieval``) from channels that write their own output
    (``generative``). Only retrieval output is evidence about what has
    been published, which is why only retrieval channels may carry a
    positive control.
    """

    name: str
    kind: str
    agent_type: str
    min_depth: str
    controlled: bool
    prompt_includes: tuple[str, ...]
    when: str
    limitations: tuple[str, ...]
    best_practices: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"kind must be one of {_KINDS}, got {self.kind!r}")
        if self.min_depth not in DEPTH_ORDER:
            raise ValueError(
                f"min_depth must be one of {sorted(DEPTH_ORDER)}, got {self.min_depth!r}"
            )
        if not self.limitations:
            raise ValueError(f"card {self.name!r} declares no limitations")
        if self.controlled and self.kind != "retrieval":
            raise ValueError(
                f"card {self.name!r} is {self.kind} and cannot be controlled: "
                "a positive control needs an index to probe"
            )


# Shared by every retrieval channel. Frontier's docstring names it as
# the blind spot no control can detect.
_VOCABULARY = (
    "A field published under different words looks absent. A passing "
    "control proves the channel can search, not that the query used the "
    "field's vocabulary."
)

# Card order is dispatch order and the order the planner lists channels.
CHANNEL_CARDS: tuple[ChannelCard, ...] = (
    ChannelCard(
        name="code",
        kind="retrieval",
        agent_type="tome:code-searcher",
        min_depth="light",
        controlled=True,
        prompt_includes=("topic",),
        when="Topics with implementations to find. Weak for pure theory or method.",
        limitations=(
            "A repository existing says nothing about whether its approach works.",
            "Findings are the subset the agent chose to report, not the "
            "number of results a query returned.",
            _VOCABULARY,
        ),
        best_practices=(
            "Run build_canary_query for this channel before any topic query.",
            "Build queries with build_github_search_queries instead of free text.",
            "Record every query, failed ones included, in the envelope.",
        ),
    ),
    ChannelCard(
        name="discourse",
        kind="retrieval",
        agent_type="tome:discourse-scanner",
        min_depth="light",
        controlled=True,
        prompt_includes=("topic", "domain", "subreddits"),
        when="Practitioner experience and failure reports. Weak without a community.",
        limitations=(
            "HN, Lobsters, Reddit and blogs share one channel name, so the "
            "channel can read clean while one of its sources is dead.",
            "Scores measure attention, not correctness.",
            "WebFetch refuses old.reddit.com in Claude Code (checked "
            "2026-09-18), so the Reddit source returns nothing. Record it as "
            "a source_error, never as an empty result.",
            _VOCABULARY,
        ),
        best_practices=(
            "Run build_canary_query for this channel before any topic query.",
            "Pick subreddits with suggest_subreddits(topic, domain).",
            "Report contrarian views next to the top-scored ones.",
        ),
    ),
    ChannelCard(
        name="academic",
        kind="retrieval",
        agent_type="tome:literature-reviewer",
        min_depth="medium",
        controlled=True,
        prompt_includes=("topic", "domain"),
        when="Formal results, benchmarks, and surveys.",
        limitations=(
            "Results from a fallback source mark the channel degraded: the "
            "findings are real, the coverage is not what was asked for.",
            "Preprints are unreviewed.",
            _VOCABULARY,
        ),
        best_practices=(
            "Run build_canary_query for this channel before any topic query.",
            "Build queries with expand_academic_queries instead of free text.",
            "Name the source that answered when a fallback was used.",
        ),
    ),
    ChannelCard(
        name="web",
        kind="retrieval",
        agent_type="tome:web-searcher",
        min_depth="medium",
        controlled=True,
        prompt_includes=("topic", "domain"),
        when="Vendor documentation, standards, comparisons, and news. Weak for "
        "code and for opinion, which have their own channels.",
        limitations=(
            "The control fetches a known page, so it proves the open web is "
            "reachable, not that a search engine ranked the topic's pages.",
            "You.com is optional. Without it the channel runs on WebSearch "
            "alone; findings record which path retrieved them in "
            "metadata.retrieved_via.",
            "Search results are ordered by an engine's relevance, not by "
            "correctness, and vendor pages argue for their vendor.",
            _VOCABULARY,
        ),
        best_practices=(
            "Run build_canary_query for this channel before any topic query.",
            "Build queries with expand_web_queries instead of free text.",
            "Report items the parser skipped beside the count each query "
            "returned, so a drifted response shape cannot read as empty.",
        ),
    ),
    ChannelCard(
        name="triz",
        kind="generative",
        agent_type="tome:triz-analyst",
        min_depth="deep",
        controlled=False,
        prompt_includes=("topic", "domain", "triz_depth"),
        when="A trade-off to break, where a distant field may hold the mechanism.",
        limitations=(
            "Writes analogies instead of retrieving records, so its output is "
            "not evidence of prior work and is excluded from the coverage "
            "verdict.",
            "Runs no positive control: there is no index to probe.",
        ),
        best_practices=(
            "State the contradiction before searching for analogies.",
            "Name what does not transfer in every bridge.",
        ),
    ),
)

_BY_NAME: dict[str, ChannelCard] = {card.name: card for card in CHANNEL_CARDS}


def get_card(name: str) -> ChannelCard:
    """Return the card for channel ``name``.

    Raises:
        KeyError: When no card exists. A missing card is a pipeline
            defect, never a channel to skip quietly.
    """
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(
            f"no channel card named {name!r}; have {sorted(_BY_NAME)}"
        ) from None


def render_card(card: ChannelCard) -> str:
    """Render a card as the markdown block a dispatch prompt embeds.

    OctoTools hands tool metadata to both the planner and the command
    generator. The equivalent here is the agent's own prompt: an agent
    told where its channel is blind can say so in its envelope.
    """
    evidence = (
        "Output is evidence about published work."
        if card.kind == "retrieval"
        else "Output is not evidence of prior work."
    )
    lines = [
        f"### Channel card: {card.name} ({card.agent_type})",
        f"Kind: {card.kind}. {evidence}",
        f"Use when: {card.when}",
        "Return: your final message is exactly one fenced ```json block holding "
        f"the envelope documented in agents/{card.agent_type.partition(':')[2]}.md: "
        "channel, findings, errors, metadata.queries with one entry per query "
        "run. `error` is for failed queries only. Prose outside the block is "
        "dropped.",
        "Limitations:",
        *(f"- {item}" for item in card.limitations),
        "Best practices:",
        *(f"- {item}" for item in card.best_practices),
    ]
    return "\n".join(lines)
