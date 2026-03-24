"""
Feature: Cross-session research memory

As a returning researcher
I want new sessions seeded with findings from related past sessions
So that research builds on itself rather than starting from scratch
"""

from __future__ import annotations

import pytest
from tome.memory import find_related_sessions, import_prior_findings
from tome.models import ResearchSession

from tests.factories import make_finding


class TestFindRelatedSessions:
    """
    Feature: Related session discovery

    As the session manager
    I want to find past sessions on similar topics
    So that their findings can seed a new session
    """

    @pytest.mark.unit
    def test_exact_topic_match(self) -> None:
        """
        Scenario: Same topic searched before
        Given a past session on "cache eviction"
        When find_related_sessions is called with "cache eviction"
        Then the past session is returned
        """
        past = ResearchSession(
            topic="cache eviction",
            domain="algorithm",
            triz_depth="medium",
            channels=["code", "academic"],
        )

        related = find_related_sessions("cache eviction", [past])

        assert len(related) == 1
        assert related[0].topic == "cache eviction"

    @pytest.mark.unit
    def test_partial_topic_overlap(self) -> None:
        """
        Scenario: Related but not identical topic
        Given a past session on "cache eviction policy"
        When find_related_sessions is called with "cache eviction strategies"
        Then the past session is returned (word overlap)
        """
        past = ResearchSession(
            topic="cache eviction policy",
            domain="algorithm",
            triz_depth="medium",
            channels=["code"],
        )

        related = find_related_sessions("cache eviction strategies", [past])

        assert len(related) == 1

    @pytest.mark.unit
    def test_unrelated_topic_excluded(self) -> None:
        """
        Scenario: Completely different topic
        Given a past session on "react component patterns"
        When find_related_sessions is called with "cache eviction"
        Then no sessions are returned
        """
        past = ResearchSession(
            topic="react component patterns",
            domain="ui-ux",
            triz_depth="light",
            channels=["code"],
        )

        related = find_related_sessions("cache eviction", [past])

        assert len(related) == 0

    @pytest.mark.unit
    def test_empty_history(self) -> None:
        """
        Scenario: No past sessions
        Given an empty session list
        When find_related_sessions is called
        Then an empty list is returned
        """
        assert find_related_sessions("anything", []) == []


class TestImportPriorFindings:
    """
    Feature: Prior finding import

    As the research orchestrator
    I want to carry forward relevant findings from past sessions
    So that the new session starts with a knowledge base
    """

    @pytest.mark.unit
    def test_imports_findings_from_related_session(self) -> None:
        """
        Scenario: Import from a past session
        Given a past session with 3 findings
        When import_prior_findings is called
        Then findings are returned with marked source
        """
        past = ResearchSession(
            topic="cache eviction",
            domain="algorithm",
            triz_depth="medium",
            channels=["code"],
        )
        past.findings = [
            make_finding(0.8, title="Paper A"),
            make_finding(0.7, title="Paper B"),
            make_finding(0.6, title="Paper C"),
        ]

        imported = import_prior_findings([past], max_per_session=5)

        assert len(imported) == 3
        assert all(f.metadata.get("from_prior_session") is True for f in imported)

    @pytest.mark.unit
    def test_limits_per_session(self) -> None:
        """
        Scenario: Cap findings per session
        Given a past session with 10 findings
        When import_prior_findings is called with max_per_session=3
        Then only the top 3 by relevance are imported
        """
        past = ResearchSession(
            topic="cache eviction",
            domain="algorithm",
            triz_depth="medium",
            channels=["code"],
        )
        past.findings = [make_finding(0.1 * i, title=f"F{i}") for i in range(1, 11)]

        imported = import_prior_findings([past], max_per_session=3)

        assert len(imported) == 3

    @pytest.mark.unit
    def test_empty_sessions(self) -> None:
        """
        Scenario: No findings in past sessions
        Given a past session with 0 findings
        When import_prior_findings is called
        Then an empty list is returned
        """
        past = ResearchSession(
            topic="empty",
            domain="general",
            triz_depth="light",
            channels=["code"],
        )

        assert import_prior_findings([past]) == []
