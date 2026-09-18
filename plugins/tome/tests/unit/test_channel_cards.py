"""
Feature: Channel cards

As the research orchestrator
I want each channel's role, depth gate, and limitations in one typed record
So that the planner, the dispatch prompts, and the stop decision read the
same facts instead of three hand-kept copies

OctoTools (arXiv 2502.11271) calls these tool cards. Its own cards keep
limitations in an untyped dict, and the keys drifted across tools
(``limitation``, ``limitations``, ``best_practice``, ``best_practices``),
so a planner reading one spelling silently missed the others. These tests
pin the cards to the code constants they describe, so a card that drifts
from the pipeline turns red rather than misleading a prompt.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tome.channels.canary import CANARY_TARGETS
from tome.channels.cards import CHANNEL_CARDS, ChannelCard, get_card, render_card
from tome.models import _VALID_CHANNELS, RETRIEVAL_CHANNELS, DomainClassification
from tome.scripts import research_planner

_AGENTS_DIR = Path(__file__).parents[2] / "agents"


def _card(**overrides: object) -> ChannelCard:
    fields: dict[str, Any] = {
        "name": "code",
        "kind": "retrieval",
        "agent_type": "tome:code-searcher",
        "min_depth": "light",
        "controlled": True,
        "prompt_includes": ("topic",),
        "when": "Always.",
        "limitations": ("One limitation.",),
        "best_practices": ("One practice.",),
    }
    fields.update(overrides)
    return ChannelCard(**fields)


class TestCardsDescribeThePipelineThatExists:
    """Scenario: every card agrees with the constant it describes."""

    @pytest.mark.unit
    def test_one_card_per_valid_channel(self) -> None:
        """
        Given the channels Finding accepts
        Then there is exactly one card for each, and no extra cards
        """
        names = [card.name for card in CHANNEL_CARDS]
        assert len(names) == len(set(names))
        assert set(names) == set(_VALID_CHANNELS)

    @pytest.mark.unit
    def test_retrieval_kind_matches_the_verdict_channels(self) -> None:
        """
        Given RETRIEVAL_CHANNELS decides who may testify in the verdict
        Then the cards marked retrieval are exactly those channels

            A generative card marked retrieval would tell the stop
            decision that analogies are evidence of prior work.
        """
        retrieval = {c.name for c in CHANNEL_CARDS if c.kind == "retrieval"}
        assert retrieval == set(RETRIEVAL_CHANNELS)

    @pytest.mark.unit
    def test_controlled_flag_matches_canary_targets(self) -> None:
        """
        Given CANARY_TARGETS defines which channels run a positive control
        Then a card claims a control exactly when a target exists
        """
        controlled = {c.name for c in CHANNEL_CARDS if c.controlled}
        assert controlled == set(CANARY_TARGETS)

    @pytest.mark.unit
    @pytest.mark.parametrize("card", CHANNEL_CARDS, ids=lambda c: c.name)
    def test_agent_type_names_a_shipped_agent(self, card: ChannelCard) -> None:
        """
        Given a card routes its channel to an agent
        Then that agent's definition ships in this plugin
        """
        plugin, _, agent = card.agent_type.partition(":")
        assert plugin == "tome"
        assert (_AGENTS_DIR / f"{agent}.md").is_file()

    @pytest.mark.unit
    @pytest.mark.parametrize("card", CHANNEL_CARDS, ids=lambda c: c.name)
    def test_the_workflow_routes_to_the_cards_agent(self, card: ChannelCard) -> None:
        """
        Given workflows/research.js keeps its own channel table
        Then each card's channel routes to the same agent there

            The workflow is JavaScript and cannot import the cards, so
            this is the only thing holding the two routing tables
            together.
        """
        script = (_AGENTS_DIR.parent / "workflows" / "research.js").read_text(
            encoding="utf-8"
        )
        assert f"key: '{card.name}', agentType: '{card.agent_type}'" in script

    @pytest.mark.unit
    def test_get_card_returns_the_named_card(self) -> None:
        assert get_card("triz").kind == "generative"

    @pytest.mark.unit
    def test_get_card_rejects_an_unknown_channel(self) -> None:
        with pytest.raises(KeyError, match="nope"):
            get_card("nope")


class TestCardsRejectMalformedFacts:
    """Scenario: a bad card fails at construction, not in a prompt."""

    @pytest.mark.unit
    def test_unknown_kind_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="kind"):
            _card(kind="oracle")

    @pytest.mark.unit
    def test_unknown_depth_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="min_depth"):
            _card(min_depth="bottomless")

    @pytest.mark.unit
    def test_a_card_without_limitations_is_rejected(self) -> None:
        """
        Given limitations are what the stop decision and the agent read
        When a card declares none
        Then construction fails

            Every channel has a blind spot. A card claiming none is a
            card nobody finished writing.
        """
        with pytest.raises(ValueError, match="limitations"):
            _card(limitations=())

    @pytest.mark.unit
    def test_a_generative_card_cannot_claim_a_control(self) -> None:
        """
        Given a positive control proves an index can be searched
        When a generative channel, which has no index, claims one
        Then construction fails
        """
        with pytest.raises(ValueError, match="controlled"):
            _card(kind="generative", controlled=True)

    @pytest.mark.unit
    def test_an_unknown_field_is_rejected(self) -> None:
        """
        Given OctoTools lost limitations to a misspelled dict key
        When a card is built with a misspelled field
        Then construction fails instead of dropping the value
        """
        with pytest.raises(TypeError):
            _card(limitation=("typo",))


class TestRenderedCardsCarryTheLimitations:
    """Scenario: the dispatch prompt gets the card's cautions."""

    @pytest.mark.unit
    def test_render_includes_every_limitation_and_practice(self) -> None:
        card = get_card("discourse")
        text = render_card(card)
        assert card.agent_type in text
        for line in (*card.limitations, *card.best_practices):
            assert line in text

    @pytest.mark.unit
    def test_render_says_generative_output_is_not_evidence(self) -> None:
        """
        Given triz output is excluded from the coverage verdict
        Then its rendered card tells the agent so
        """
        assert "not evidence" in render_card(get_card("triz")).lower()

    @pytest.mark.unit
    @pytest.mark.parametrize("card", CHANNEL_CARDS, ids=lambda c: c.name)
    def test_render_points_at_the_documented_envelope(self, card: ChannelCard) -> None:
        """
        Given each agent file documents the envelope parse_envelope reads
        Then the rendered card tells the agent to return that envelope

            OctoTools' cards carry an output_type. Without one here, a
            dispatch prompt once dictated its own return shape, the agent
            obeyed it, and the query log lost its canary.
        """
        text = render_card(card)
        assert "metadata.queries" in text
        assert f"agents/{card.agent_type.partition(':')[2]}.md" in text

    @pytest.mark.unit
    def test_discourse_card_names_the_dead_reddit_source(self) -> None:
        """
        Given WebFetch refuses old.reddit.com in Claude Code (checked
        2026-09-18: "Claude Code is unable to fetch from old.reddit.com")
        Then the discourse card says so, so the agent files a
        source_error instead of an empty result
        """
        text = render_card(get_card("discourse")).lower()
        assert "reddit" in text and "source_error" in text

    @pytest.mark.unit
    def test_render_demands_the_envelope_as_the_final_message(self) -> None:
        """
        Given a card that only pointed at the agent's envelope file
        When a code-searcher was dispatched with it (ADR-0024 pass 2)
        Then it returned prose and no envelope at all

            A pointer is not an instruction. The card states the output
            contract inline: one fenced JSON block, last message.
        """
        text = render_card(get_card("code"))
        assert "final message" in text
        assert "```json" in text

    @pytest.mark.unit
    @pytest.mark.parametrize("card", CHANNEL_CARDS, ids=lambda c: c.name)
    def test_every_function_a_card_names_exists(self, card: ChannelCard) -> None:
        """
        Given a best practice names a tome query builder
        Then that builder is importable from tome.channels

            A card naming a function that does not exist sends the agent
            to improvise, which is the failure the builders prevent.
        """
        modules = [
            importlib.import_module(f"tome.channels.{name}")
            for name in ("canary", "github", "discourse", "academic", "triz")
        ]
        named = re.findall(r"\b(?:build|expand|suggest)_\w+", render_card(card))
        for function in named:
            assert any(hasattr(m, function) for m in modules), function


class TestThePlannerGatesOnCards:
    """Scenario: the channel list comes from the cards, not an if-ladder."""

    @pytest.mark.unit
    def test_a_card_depth_change_changes_the_plan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given the triz card is lowered to medium depth
        When a medium-depth topic is planned
        Then triz is in the plan

            Before cards, the depth gate lived in research_planner as
            hard-coded comparisons, so a card could say one thing and
            the planner do another.
        """
        lowered = tuple(
            replace(c, min_depth="medium") if c.name == "triz" else c
            for c in CHANNEL_CARDS
        )
        monkeypatch.setattr(research_planner, "CHANNEL_CARDS", lowered)
        classification = DomainClassification(
            domain="algorithm",
            triz_depth="medium",
            channel_weights={
                "code": 1.0,
                "discourse": 1.0,
                "academic": 1.0,
                "triz": 1.0,
            },
            confidence=0.9,
        )
        assert research_planner.plan(classification).channels == [
            "code",
            "discourse",
            "academic",
            "triz",
        ]
