"""
Feature: Tome core data models

As a research pipeline component
I want well-typed, constructible data models
So that classifiers, planners, and channels can exchange data reliably
"""

from __future__ import annotations

import pytest
from tome.models import (
    DomainClassification,
    Finding,
    ResearchPlan,
    ResearchSession,
    SessionSummary,
)


class TestDomainClassification:
    """
    Feature: DomainClassification model

    As a domain classifier
    I want a typed container for classification results
    So that downstream planners receive consistent structured data
    """

    @pytest.mark.unit
    def test_construction_with_required_fields(self) -> None:
        """
        Scenario: Construct a classification from required fields
        Given valid domain, depth, weights, and confidence
        When DomainClassification is instantiated
        Then all fields are accessible and match inputs
        """
        weights = {"code": 0.25, "discourse": 0.20, "academic": 0.40, "triz": 0.15}
        dc = DomainClassification(
            domain="algorithm",
            triz_depth="medium",
            channel_weights=weights,
            confidence=0.82,
        )

        assert dc.domain == "algorithm"
        assert dc.triz_depth == "medium"
        assert dc.channel_weights == weights
        assert dc.confidence == 0.82

    @pytest.mark.unit
    def test_channel_weights_are_independent_per_instance(self) -> None:
        """
        Scenario: Each instance owns its own weights dict
        Given two classifications with different weights
        When comparing their channel_weights
        Then they do not share the same dict object
        """
        w1 = {"code": 0.35, "discourse": 0.40, "academic": 0.15, "triz": 0.10}
        w2 = {"code": 0.25, "discourse": 0.15, "academic": 0.35, "triz": 0.25}
        dc1 = DomainClassification("ui-ux", "light", w1, 0.75)
        dc2 = DomainClassification("data-structure", "deep", w2, 0.90)

        assert dc1.channel_weights is not dc2.channel_weights


class TestResearchPlan:
    """
    Feature: ResearchPlan model

    As a research orchestrator
    I want a typed container for planned research channels and budgets
    So that channel runners know what to execute and at what cost
    """

    @pytest.mark.unit
    def test_construction_with_all_channels(self) -> None:
        """
        Scenario: Build a deep research plan with all channels
        Given a deep triz_depth and four active channels
        When ResearchPlan is instantiated
        Then channels list and budget are preserved
        """
        plan = ResearchPlan(
            channels=["code", "discourse", "academic", "triz"],
            weights={"code": 0.25, "discourse": 0.15, "academic": 0.35, "triz": 0.25},
            triz_depth="deep",
            estimated_budget=6000,
        )

        assert plan.channels == ["code", "discourse", "academic", "triz"]
        assert plan.triz_depth == "deep"
        assert plan.estimated_budget == 6000
        assert plan.weights["code"] == 0.25

    @pytest.mark.unit
    def test_construction_with_light_channels(self) -> None:
        """
        Scenario: Build a light plan with only two channels
        Given a light triz_depth and two channels
        When ResearchPlan is instantiated
        Then estimated_budget is the light tier value
        """
        plan = ResearchPlan(
            channels=["code", "discourse"],
            weights={"code": 0.35, "discourse": 0.40, "academic": 0.15, "triz": 0.10},
            triz_depth="light",
            estimated_budget=2000,
        )

        assert plan.channels == ["code", "discourse"]
        assert plan.estimated_budget == 2000
        assert plan.weights["code"] == 0.35


class TestFinding:
    """
    Feature: Finding model

    As a channel runner
    I want a typed container for individual research results
    So that synthesis can aggregate results from multiple sources uniformly
    """

    @pytest.mark.unit
    def test_construction_with_metadata(self) -> None:
        """
        Scenario: Construct a finding with full metadata
        Given all fields including metadata dict
        When Finding is instantiated
        Then all fields are accessible
        """
        finding = Finding(
            source="github",
            channel="code",
            title="example/async-patterns",
            url="https://github.com/example/async-patterns",
            relevance=0.85,
            summary="Async patterns library",
            metadata={"stars": 1200},
        )

        assert finding.source == "github"
        assert finding.channel == "code"
        assert finding.metadata == {"stars": 1200}

    @pytest.mark.unit
    def test_metadata_defaults_to_empty_dict(self) -> None:
        """
        Scenario: Omit metadata on construction
        Given only required fields
        When Finding is instantiated without metadata
        Then metadata is an empty dict, not None
        """
        finding = Finding(
            source="arxiv",
            channel="academic",
            title="A Survey",
            url="https://arxiv.org/abs/1234",
            relevance=0.90,
            summary="A survey paper",
        )

        assert finding.metadata == {}
        assert isinstance(finding.metadata, dict)

    @pytest.mark.unit
    def test_metadata_not_shared_across_instances(self) -> None:
        """
        Scenario: Two findings without metadata have independent dicts
        Given two findings constructed without metadata
        When one's metadata is mutated
        Then the other is unaffected
        """
        f1 = Finding("s1", "code", "t1", "u1", 0.5, "s1")
        f2 = Finding("s2", "code", "t2", "u2", 0.5, "s2")
        f1.metadata["key"] = "value"

        assert "key" not in f2.metadata


class TestResearchSession:
    """
    Feature: ResearchSession model

    As the research orchestrator
    I want a session container that tracks topic, findings, and status
    So that session state can be persisted and resumed
    """

    @pytest.mark.unit
    def test_construction_with_defaults(self) -> None:
        """
        Scenario: Create a minimal session
        Given only required fields
        When ResearchSession is instantiated
        Then findings defaults to empty list and status to 'pending'
        """
        session = ResearchSession(
            id="sess-001",
            topic="async python patterns",
            domain="algorithm",
            triz_depth="medium",
            channels=["code", "discourse", "academic"],
        )

        assert session.findings == []
        assert session.status in ("active", "pending")
        assert session.created_at is None

    @pytest.mark.unit
    def test_findings_list_not_shared_across_instances(self) -> None:
        """
        Scenario: Two sessions without explicit findings have independent lists
        Given two sessions constructed without findings
        When one's findings list is appended to
        Then the other session's findings remain empty
        """
        s1 = ResearchSession("s1", "topic1", "algorithm", "medium", ["code"])
        s2 = ResearchSession("s2", "topic2", "algorithm", "medium", ["code"])

        s1.findings.append(Finding("github", "code", "t", "u", 0.5, "summary"))

        assert len(s2.findings) == 0


class TestSessionSummary:
    """
    Feature: SessionSummary model

    As a session listing command
    I want a lightweight summary of a session
    So that lists of sessions can be displayed without loading all findings
    """

    @pytest.mark.unit
    def test_construction_with_required_fields(self) -> None:
        """
        Scenario: Construct a summary from session metadata
        Given id, topic, domain, count, and status
        When SessionSummary is instantiated
        Then all fields are accessible
        """
        summary = SessionSummary(
            id="sess-001",
            topic="async python patterns",
            domain="algorithm",
            finding_count=12,
            status="complete",
        )

        assert summary.id == "sess-001"
        assert summary.finding_count == 12
        assert summary.created_at is None
