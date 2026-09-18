"""
Feature: Paradigm recommendation reads its data file and ranks candidates

As architecture-aware-init
I want the recommender to score every paradigm the matrix and modifiers
name, and to say how sure it is
So that a project type or security level can change the answer, and a
close call is reported as one

Two defects found in the 2026-09 audit (ADR-0025). The YAML modifiers
use the keys ``preferred``, ``avoid`` and ``recommended`` while the code
read ``preferred_paradigm``, ``fallback_paradigm`` and
``promote_patterns``, so no modifier had ever changed a recommendation.
And ``recommend`` returned one paradigm with ``confidence="high"``
hard-coded, whatever the margin over the runner-up.
"""

from __future__ import annotations

import pytest

from architecture_researcher import (
    ArchitectureResearcher,
    ProjectContext,
    load_decision_matrix,
)


def _context(**overrides: str) -> ProjectContext:
    fields = {
        "project_type": "web-api",
        "domain_complexity": "moderate",
        "team_size": "5-15",
    }
    fields.update(overrides)
    return ProjectContext(**fields)


class TestTheCodeReadsTheKeysTheDataUses:
    """Scenario: modifier keys in the YAML are the keys the code reads."""

    @pytest.mark.unit
    def test_every_modifier_key_in_the_data_is_consumed(self) -> None:
        """
        Given the shipped decision matrix
        Then every key under each modifier block is one the ranker reads

            A key the ranker ignores is a rule that never fires, which
            is how the project-type modifiers went unused.
        """
        data = load_decision_matrix()
        consumed = ArchitectureResearcher.CONSUMED_MODIFIER_KEYS
        for block in (
            "project_type_modifiers",
            "scalability_modifiers",
            "security_modifiers",
        ):
            for name, rules in data[block].items():
                unknown = set(rules) - consumed
                assert not unknown, (
                    f"{block}.{name} has keys the ranker ignores: {unknown}"
                )


class TestModifiersChangeTheAnswer:
    """Scenario: project type, scalability and security move the ranking."""

    @pytest.mark.unit
    def test_a_cli_tool_avoids_microservices_even_for_a_large_team(self) -> None:
        """
        Given a 15-50 team with moderate complexity (matrix says microservices)
        And a cli-tool project type, whose modifier avoids microservices
        Then microservices is not the top recommendation
        """
        researcher = ArchitectureResearcher(
            _context(team_size="15-50", project_type="cli-tool")
        )
        assert researcher.recommend().primary != "microservices"

    @pytest.mark.unit
    def test_critical_security_demotes_layered(self) -> None:
        """
        Given a small team with simple complexity (matrix says layered)
        And critical security, whose modifier avoids layered
        Then layered is not the top recommendation
        """
        researcher = ArchitectureResearcher(
            _context(
                team_size="<5",
                domain_complexity="simple",
                security_requirements="critical",
            )
        )
        assert researcher.recommend().primary != "layered"

    @pytest.mark.unit
    def test_extreme_scalability_promotes_a_distributed_paradigm(self) -> None:
        """Extreme scalability puts a distributed paradigm in the top two."""
        researcher = ArchitectureResearcher(_context(scalability_needs="extreme"))
        top_two = [c.paradigm for c in researcher.rank()[:2]]
        assert any(p in ("microservices", "event-driven", "cqrs-es") for p in top_two)


class TestTheRankingIsOrderedAndExplained:
    """Scenario: rank is sorted, explained, and recommend is its head."""

    @pytest.mark.unit
    def test_rank_is_sorted_by_score_and_names_the_rules(self) -> None:
        """Candidates come best first and each names its scoring rules."""
        candidates = ArchitectureResearcher(_context()).rank()
        scores = [c.score for c in candidates]
        assert scores == sorted(scores, reverse=True)
        assert all(c.rules for c in candidates), (
            "every candidate names the rules that scored it"
        )
        assert candidates[0].paradigm == "modular-monolith"

    @pytest.mark.unit
    def test_recommend_is_the_top_of_rank(self) -> None:
        """recommend() and rank()[0] agree."""
        researcher = ArchitectureResearcher(_context())
        assert researcher.recommend().primary == researcher.rank()[0].paradigm

    @pytest.mark.unit
    def test_alternatives_carry_the_runners_up(self) -> None:
        """The runners-up travel with the recommendation."""
        recommendation = ArchitectureResearcher(_context()).recommend()
        assert recommendation.alternatives, "runners-up are reported, not dropped"
        assert recommendation.alternatives[0]["paradigm"] == recommendation.secondary


class TestConfidenceComesFromTheMargin:
    """Scenario: confidence reflects the gap to the runner-up."""

    @pytest.mark.unit
    def test_a_clear_winner_is_high_confidence(self) -> None:
        """
        Given a medium team, moderate complexity, web-api, standard security
        Then the matrix primary is preferred by the project type too and wins clearly
        """
        assert ArchitectureResearcher(_context()).recommend().confidence == "high"

    @pytest.mark.unit
    def test_a_close_call_is_not_high_confidence(self) -> None:
        """
        Given a medium team with moderate complexity (matrix: modular-monolith)
        And extreme scalability, which recommends the distributed paradigms
        Then modular-monolith and microservices tie and confidence is not high
        """
        researcher = ArchitectureResearcher(_context(scalability_needs="extreme"))
        recommendation = researcher.recommend()
        first, second = researcher.rank()[:2]
        assert (
            first.score - second.score < ArchitectureResearcher.HIGH_CONFIDENCE_MARGIN
        )
        assert recommendation.confidence != "high"


class TestUnknownContextStillFailsLoudly:
    """Scenario: an unknown context is refused, not guessed."""

    @pytest.mark.unit
    def test_unknown_team_size_raises(self) -> None:
        """A team size the matrix lacks raises ValueError."""
        with pytest.raises(ValueError, match="team size"):
            ArchitectureResearcher(_context(team_size="1000")).rank()


class TestResearchFindingsReachTheRanking:
    """Scenario: research the session gathered changes the recommendation.

    ``perform_online_research`` printed queries and returned ``{}``, so
    the skill's "selects via research" claim had nothing behind it. A
    findings dict with ``preferred`` and ``avoid`` lists is now a fourth
    modifier, and its rules name themselves.
    """

    @pytest.mark.unit
    def test_research_avoid_demotes_the_matrix_primary(self) -> None:
        """Research that avoids modular-monolith moves it off the top."""
        researcher = ArchitectureResearcher(_context())
        plain = researcher.recommend()
        informed = researcher.recommend_paradigm({"avoid": ["modular-monolith"]})
        assert plain.primary == "modular-monolith"
        assert informed.primary != "modular-monolith"
        assert any(
            "research" in rule for rule in informed.rationale.split("; ")
        ) or any("research" in alt["rationale"] for alt in informed.alternatives)

    @pytest.mark.unit
    def test_research_preferred_paradigm_is_named_in_a_rule(self) -> None:
        """A preferred paradigm gains points from a rule that says research."""
        researcher = ArchitectureResearcher(_context())
        ranked = researcher.rank(research={"preferred": ["event-driven"]})
        event_driven = next(c for c in ranked if c.paradigm == "event-driven")
        assert any("research" in rule for rule in event_driven.rules)

    @pytest.mark.unit
    def test_empty_research_changes_nothing(self) -> None:
        """No findings is the old behavior, exactly."""
        researcher = ArchitectureResearcher(_context())
        assert researcher.recommend_paradigm({}) == researcher.recommend()
