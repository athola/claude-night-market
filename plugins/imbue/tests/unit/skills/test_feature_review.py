"""Tests for feature-review skill scoring and classification logic.

This module tests the RICE+WSJF hybrid scoring framework and the
Static/Dynamic, Proactive/Reactive classification system.

Following TDD/BDD principles to ensure scoring calculations are accurate
and classification logic correctly categorizes features.
"""

from __future__ import annotations

import pytest


class TestScoringFramework:
    """Feature: RICE+WSJF hybrid scoring produces accurate prioritization.

    As a product manager
    I want features scored consistently
    So that prioritization decisions are data-driven
    """

    @pytest.fixture
    def sample_feature_scores(self):
        """Sample feature with all scoring factors."""
        return {
            "name": "Auto-save drafts",
            "value": {
                "reach": 8,  # Most users write drafts
                "impact": 5,  # Significant UX improvement
                "business_value": 3,  # Supports retention KR
                "time_criticality": 3,  # Should do this quarter
            },
            "cost": {
                "effort": 3,  # 3-5 days
                "risk": 2,  # Low risk, understood problem
                "complexity": 3,  # Moderate, needs state management
            },
            "confidence": 0.8,  # Similar features built before
        }

    @pytest.fixture
    def default_weights(self):
        """Return default scoring weights configuration."""
        return {
            "value": {
                "reach": 0.25,
                "impact": 0.30,
                "business_value": 0.25,
                "time_criticality": 0.20,
            },
            "cost": {
                "effort": 0.40,
                "risk": 0.30,
                "complexity": 0.30,
            },
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_value_score_calculation(self, sample_feature_scores) -> None:
        """Scenario: Value score is calculated from value factors.

        Given a feature with value factor scores
        When calculating the value score
        Then it should equal the average of value factors.
        """
        # Arrange
        value = sample_feature_scores["value"]

        # Act - Calculate unweighted average
        value_score = (
            value["reach"]
            + value["impact"]
            + value["business_value"]
            + value["time_criticality"]
        ) / 4

        # Assert
        assert value_score == 4.75
        assert value_score == (8 + 5 + 3 + 3) / 4

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cost_score_calculation(self, sample_feature_scores) -> None:
        """Scenario: Cost score is calculated from cost factors.

        Given a feature with cost factor scores
        When calculating the cost score
        Then it should equal the average of cost factors.
        """
        # Arrange
        cost = sample_feature_scores["cost"]

        # Act - Calculate unweighted average
        cost_score = (cost["effort"] + cost["risk"] + cost["complexity"]) / 3

        # Assert
        expected = (3 + 2 + 3) / 3
        assert abs(cost_score - expected) < 0.01  # Float comparison
        assert abs(cost_score - 2.67) < 0.01

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_feature_score_calculation(self, sample_feature_scores) -> None:
        """Scenario: Feature score combines value, cost, and confidence.

        Given a feature with value, cost, and confidence scores
        When calculating the final feature score
        Then it should equal (value / cost) * confidence.
        """
        # Arrange
        value = sample_feature_scores["value"]
        cost = sample_feature_scores["cost"]
        confidence = sample_feature_scores["confidence"]

        # Act
        value_score = (
            value["reach"]
            + value["impact"]
            + value["business_value"]
            + value["time_criticality"]
        ) / 4
        cost_score = (cost["effort"] + cost["risk"] + cost["complexity"]) / 3
        feature_score = (value_score / cost_score) * confidence

        # Assert
        expected = (4.75 / 2.67) * 0.8
        assert abs(feature_score - expected) < 0.01
        assert abs(feature_score - 1.42) < 0.05  # Approximate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weighted_value_score(self, sample_feature_scores, default_weights) -> None:
        """Scenario: Weighted value score applies configured weights.

        Given a feature with value scores and custom weights
        When calculating weighted value score
        Then weights should be applied to each factor.
        """
        # Arrange
        value = sample_feature_scores["value"]
        weights = default_weights["value"]

        # Act - Calculate weighted average
        weighted_value = (
            value["reach"] * weights["reach"]
            + value["impact"] * weights["impact"]
            + value["business_value"] * weights["business_value"]
            + value["time_criticality"] * weights["time_criticality"]
        )

        # Assert
        expected = 8 * 0.25 + 5 * 0.30 + 3 * 0.25 + 3 * 0.20
        assert abs(weighted_value - expected) < 0.01
        assert abs(weighted_value - 4.85) < 0.01

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "score,expected_priority",
        [
            (3.0, "High"),
            (2.5, "Medium"),  # Boundary: not > 2.5
            (2.0, "Medium"),
            (1.5, "Medium"),  # Boundary: >= 1.5
            (1.2, "Low"),
            (1.0, "Low"),  # Boundary: >= 1.0
            (0.8, "Very Low"),
        ],
        ids=[
            "high-score",
            "high-medium-boundary",
            "mid-medium",
            "medium-low-boundary",
            "mid-low",
            "low-very-low-boundary",
            "very-low-score",
        ],
    )
    def test_priority_thresholds(self, score, expected_priority) -> None:
        """Scenario: Feature scores map to priority levels.

        Given the scoring threshold configuration
        When a feature score is evaluated
        Then it should map to the correct priority level.
        """
        # Arrange - thresholds from scoring-framework.md
        thresholds = {"high": 2.5, "medium": 1.5, "low": 1.0}

        # Act
        if score > thresholds["high"]:
            priority = "High"
        elif score >= thresholds["medium"]:
            priority = "Medium"
        elif score >= thresholds["low"]:
            priority = "Low"
        else:
            priority = "Very Low"

        # Assert
        assert priority == expected_priority

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_confidence_adjustment(self) -> None:
        """Scenario: Low confidence features are flagged for research.

        Given a feature with low confidence
        When evaluating the feature
        Then it should be flagged for research if confidence < 0.5.
        """
        # Arrange
        low_confidence_feature = {
            "name": "AI-powered suggestions",
            "value_score": 5.0,
            "cost_score": 2.0,
            "confidence": 0.3,  # Speculative
        }

        high_confidence_feature = {
            "name": "Form validation",
            "value_score": 3.0,
            "cost_score": 2.0,
            "confidence": 0.9,  # Well-understood
        }

        # Act
        def needs_research(feature: dict) -> bool:
            return feature["confidence"] < 0.5

        # Assert
        assert needs_research(low_confidence_feature) is True
        assert needs_research(high_confidence_feature) is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weight_normalization(self, default_weights) -> None:
        """Scenario: Weights must sum to 1.0 within each category.

        Given a weight configuration
        When validating weights
        Then value weights should sum to 1.0
        And cost weights should sum to 1.0.
        """
        # Arrange
        value_weights = default_weights["value"]
        cost_weights = default_weights["cost"]

        # Act
        value_sum = sum(value_weights.values())
        cost_sum = sum(cost_weights.values())

        # Assert
        assert abs(value_sum - 1.0) < 0.001
        assert abs(cost_sum - 1.0) < 0.001

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_zero_weight_handling(self) -> None:
        """Scenario: Zero weights effectively disable factors.

        Given a weight configuration with some zero weights
        When calculating weighted score
        Then zero-weighted factors should not contribute.
        """
        # Arrange
        scores = {"reach": 10, "impact": 10, "business_value": 10}
        weights = {"reach": 0.5, "impact": 0.5, "business_value": 0.0}

        # Act
        weighted_sum = sum(scores[k] * weights[k] for k in scores if weights[k] > 0)
        weight_total = sum(w for w in weights.values() if w > 0)
        normalized = weighted_sum / weight_total if weight_total > 0 else 0

        # Assert
        assert weighted_sum == 10.0  # Only reach and impact contribute
        assert normalized == 10.0  # Normalized by non-zero weights

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_dimension_handling(self) -> None:
        """Scenario: Missing dimensions use default values.

        Given a feature with missing scoring dimensions
        When calculating scores
        Then missing dimensions should use sensible defaults.
        """
        # Arrange - feature missing some dimensions
        partial_feature = {
            "value": {"reach": 5, "impact": 3},  # Missing BV and TC
            "cost": {"effort": 3},  # Missing risk and complexity
            "confidence": 0.7,
        }

        defaults = {
            "value": {
                "reach": 3,
                "impact": 3,
                "business_value": 3,
                "time_criticality": 3,
            },
            "cost": {"effort": 3, "risk": 3, "complexity": 3},
        }

        # Act - merge with defaults
        merged_value = {**defaults["value"], **partial_feature["value"]}
        merged_cost = {**defaults["cost"], **partial_feature["cost"]}

        # Assert
        assert merged_value["reach"] == 5  # From feature
        assert merged_value["impact"] == 3  # From feature
        assert merged_value["business_value"] == 3  # From default
        assert merged_value["time_criticality"] == 3  # From default
        assert merged_cost["effort"] == 3  # From feature
        assert merged_cost["risk"] == 3  # From default


class TestClassificationSystem:
    """Feature: Features are classified along two orthogonal axes.

    As a system architect
    I want features classified by behavior and data patterns
    So that I can choose appropriate implementation strategies
    """

    @pytest.fixture
    def feature_examples(self):
        """Return example features for classification testing."""
        return {
            "auto_save": {
                "name": "Auto-save drafts",
                "triggered_by_user": False,
                "anticipates_need": True,
                "data_changes_realtime": False,
                "cache_friendly": True,
            },
            "search": {
                "name": "Full-text search",
                "triggered_by_user": True,
                "anticipates_need": False,
                "data_changes_realtime": True,
                "cache_friendly": False,
            },
            "config_loader": {
                "name": "Configuration loader",
                "triggered_by_user": True,
                "anticipates_need": False,
                "data_changes_realtime": False,
                "cache_friendly": True,
            },
            "suggestions": {
                "name": "AI suggestions",
                "triggered_by_user": False,
                "anticipates_need": True,
                "data_changes_realtime": True,
                "cache_friendly": False,
            },
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proactive_classification(self, feature_examples) -> None:
        """Scenario: Proactive features anticipate user needs.

        Given a feature that acts before user request
        When classifying the feature
        Then it should be classified as Proactive.
        """
        # Arrange
        auto_save = feature_examples["auto_save"]
        suggestions = feature_examples["suggestions"]

        # Act
        def is_proactive(feature: dict) -> bool:
            return feature["anticipates_need"] and not feature["triggered_by_user"]

        # Assert
        assert is_proactive(auto_save) is True
        assert is_proactive(suggestions) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reactive_classification(self, feature_examples) -> None:
        """Scenario: Reactive features respond to explicit input.

        Given a feature that responds to user action
        When classifying the feature
        Then it should be classified as Reactive.
        """
        # Arrange
        search = feature_examples["search"]
        config_loader = feature_examples["config_loader"]

        # Act
        def is_reactive(feature: dict) -> bool:
            return feature["triggered_by_user"]

        # Assert
        assert is_reactive(search) is True
        assert is_reactive(config_loader) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_static_classification(self, feature_examples) -> None:
        """Scenario: Static features have incremental data updates.

        Given a feature with version-controlled data
        When classifying the feature
        Then it should be classified as Static.
        """
        # Arrange
        auto_save = feature_examples["auto_save"]
        config_loader = feature_examples["config_loader"]

        # Act
        def is_static(feature: dict) -> bool:
            return feature["cache_friendly"] and not feature["data_changes_realtime"]

        # Assert
        assert is_static(auto_save) is True
        assert is_static(config_loader) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dynamic_classification(self, feature_examples) -> None:
        """Scenario: Dynamic features have continuous data changes.

        Given a feature with real-time data
        When classifying the feature
        Then it should be classified as Dynamic.
        """
        # Arrange
        search = feature_examples["search"]
        suggestions = feature_examples["suggestions"]

        # Act
        def is_dynamic(feature: dict) -> bool:
            return feature["data_changes_realtime"]

        # Assert
        assert is_dynamic(search) is True
        assert is_dynamic(suggestions) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "feature_key,expected_archetype",
        [
            ("auto_save", "Predictive Cache"),
            ("suggestions", "Smart Assistant"),
            ("config_loader", "Reference Lookup"),
            ("search", "Interactive Query"),
        ],
        ids=[
            "proactive-static-is-predictive-cache",
            "proactive-dynamic-is-smart-assistant",
            "reactive-static-is-reference-lookup",
            "reactive-dynamic-is-interactive-query",
        ],
    )
    def test_2x2_matrix_classification(
        self,
        feature_examples,
        feature_key,
        expected_archetype,
    ) -> None:
        """Scenario: Features map to one of four archetypes.

        Given the 2x2 classification matrix
        When classifying features
        Then each should map to exactly one archetype.
        """
        # Arrange
        feature = feature_examples[feature_key]

        # Act
        is_proactive = feature["anticipates_need"] and not feature["triggered_by_user"]
        is_dynamic = feature["data_changes_realtime"]

        if is_proactive and not is_dynamic:
            archetype = "Predictive Cache"
        elif is_proactive and is_dynamic:
            archetype = "Smart Assistant"
        elif not is_proactive and not is_dynamic:
            archetype = "Reference Lookup"
        else:
            archetype = "Interactive Query"

        # Assert
        assert archetype == expected_archetype


class TestKanoClassification:
    """Feature: Features are classified using Kano model.

    As a product manager
    I want features categorized by user satisfaction impact
    So that I can prioritize appropriately
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_performance_features_scale_linearly(self) -> None:
        """Scenario: Performance features have linear satisfaction.

        Given a Performance (Linear) feature
        When quality increases
        Then satisfaction increases proportionally.
        """
        # Arrange
        performance_feature = {
            "name": "Page load speed",
            "kano_type": "Performance",
            "satisfaction_curve": "Linear",
        }

        # Verify feature is configured correctly
        assert performance_feature["satisfaction_curve"] == "Linear"

        # Simulate satisfaction at different quality levels
        def satisfaction(quality: int) -> int:
            return quality  # Linear relationship

        # Assert
        assert satisfaction(1) == 1
        assert satisfaction(5) == 5
        assert satisfaction(10) == 10


class TestTradeoffDimensions:
    """Feature: Features are evaluated across quality dimensions.

    As a technical lead
    I want features evaluated on multiple quality axes
    So that I can understand implementation tradeoffs
    """

    @pytest.fixture
    def sample_tradeoffs(self):
        """Sample tradeoff evaluation."""
        return {
            "quality": 4,
            "latency": 3,
            "token_usage": 5,
            "resource_usage": 3,
            "redundancy": 4,
            "readability": 5,
            "scalability": 3,
            "integration": 4,
            "api_surface": 4,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_minimum_dimensions_required(self, sample_tradeoffs) -> None:
        """Scenario: At least 5 tradeoff dimensions must be evaluated.

        Given the guardrail requiring minimum dimensions
        When evaluating a feature
        Then at least 5 dimensions must be scored.
        """
        # Arrange
        min_dimensions = 5

        # Act
        scored_dimensions = len([v for v in sample_tradeoffs.values() if v > 0])

        # Assert
        assert scored_dimensions >= min_dimensions
        assert scored_dimensions == 9  # All dimensions scored

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dimension_scale_validation(self, sample_tradeoffs) -> None:
        """Scenario: All dimensions use 1-5 scale.

        Given the tradeoff scoring scale
        When evaluating dimensions
        Then all scores should be between 1 and 5.
        """
        # Assert
        for dimension, score in sample_tradeoffs.items():
            assert 1 <= score <= 5, f"{dimension} score {score} out of range"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weighted_tradeoff_score(self, sample_tradeoffs) -> None:
        """Scenario: Tradeoff scores can be weighted.

        Given dimension weights from configuration
        When calculating overall tradeoff score
        Then weights should be applied correctly.
        """
        # Arrange
        weights = {
            "quality": 1.0,
            "latency": 1.0,
            "token_usage": 1.0,
            "resource_usage": 0.8,
            "redundancy": 0.5,
            "readability": 1.0,
            "scalability": 0.8,
            "integration": 1.0,
            "api_surface": 1.0,
        }

        # Act
        weighted_sum = sum(
            sample_tradeoffs[dim] * weights[dim] for dim in sample_tradeoffs
        )
        weight_total = sum(weights.values())
        weighted_avg = weighted_sum / weight_total

        # Assert
        assert weighted_sum > 0
        assert 1 <= weighted_avg <= 5


class TestIntegration:
    """Feature: Feature review integrates with GitHub.

    As a developer
    I want feature suggestions to become GitHub issues
    So that they are tracked and actionable
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_title_format(self) -> None:
        """Scenario: Generated issues follow conventional commit format.

        Given a feature suggestion
        When generating a GitHub issue
        Then the title should use conventional commit format.
        """
        # Arrange
        suggestion = {
            "type": "feat",
            "scope": "auth",
            "description": "Add OAuth2 support",
        }

        # Act
        title = (
            f"{suggestion['type']}({suggestion['scope']}): {suggestion['description']}"
        )

        # Assert
        assert title == "feat(auth): Add OAuth2 support"
        assert title.startswith("feat(")

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "score,expected_label",
        [
            (3.0, "priority:high"),
            (2.0, "priority:medium"),
            (1.0, "priority:low"),
        ],
        ids=[
            "high-score-gets-high-label",
            "medium-score-gets-medium-label",
            "low-score-gets-low-label",
        ],
    )
    def test_suggestion_labels(self, score, expected_label) -> None:
        """Scenario: Suggestions get appropriate labels based on priority.

        Given a feature suggestion with a priority score
        When creating a GitHub issue
        Then it should have appropriate priority labels.
        """

        # Arrange
        def get_labels(s: float) -> list[str]:
            labels = ["enhancement"]
            if s > 2.5:
                labels.append("priority:high")
            elif s >= 1.5:
                labels.append("priority:medium")
            else:
                labels.append("priority:low")
            return labels

        # Act
        labels = get_labels(score)

        # Assert
        assert expected_label in labels
        assert "enhancement" in labels
        assert len(labels) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_backlog_limit_guardrail(self) -> None:
        """Scenario: Backlog is limited to prevent suggestion overload.

        Given the backlog limit guardrail (25 items)
        When suggestions exceed the limit
        Then older/lower-priority items should be pruned.
        """
        # Arrange
        max_backlog = 25
        suggestions = [{"id": i, "score": 2.0 - (i * 0.05)} for i in range(30)]

        # Act - keep highest scoring
        prioritized = sorted(suggestions, key=lambda s: s["score"], reverse=True)
        limited = prioritized[:max_backlog]

        # Assert
        assert len(limited) == max_backlog
        assert limited[0]["score"] > limited[-1]["score"]


class TestResearchEnrichment:
    """Feature: Research enrichment adjusts scores with external
    evidence from the tome plugin.

    As a product manager
    I want scores grounded in external evidence
    So that prioritization reflects real-world signals
    """

    FIBONACCI = [1, 2, 3, 5, 8, 13]

    @pytest.fixture
    def research_config(self):
        """Default research enrichment configuration."""
        return {
            "evidence_threshold": 0.3,
            "max_delta": 2,
            "timeout_seconds": 120,
            "channels": {
                "code_search": True,
                "discourse": True,
                "papers": False,
                "triz": False,
            },
        }

    @pytest.fixture
    def feature_with_initial_scores(self):
        """Feature with initial scoring before research."""
        return {
            "name": "Auto-save drafts",
            "value": {
                "reach": 5,
                "impact": 3,
                "business_value": 3,
                "time_criticality": 3,
            },
            "cost": {
                "effort": 3,
                "risk": 2,
                "complexity": 3,
            },
            "confidence": 0.8,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_delta_calculation(self, research_config) -> None:
        """Scenario: Research delta adjusts scores correctly.

        Given research findings with consensus and strength
        When calculating the applied delta
        Then delta equals consensus * strength * channel_weight.
        """
        # Arrange
        findings_consensus = 1.5  # Positive direction
        evidence_strength = 0.8  # Strong evidence
        channel_weight = 0.8  # code-search channel

        # Act
        raw_delta = findings_consensus * evidence_strength * channel_weight

        # Assert
        assert abs(raw_delta - 0.96) < 0.01
        assert raw_delta > research_config["evidence_threshold"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_threshold_discard(self, research_config) -> None:
        """Scenario: Low-evidence deltas are discarded.

        Given research findings below evidence threshold
        When calculating the applied delta
        Then delta should be discarded (set to 0).
        """
        # Arrange - weak evidence
        findings_consensus = 1.0
        evidence_strength = 0.2  # Below threshold
        channel_weight = 0.8

        # Act
        raw_delta = findings_consensus * evidence_strength * channel_weight

        # Assert
        if abs(raw_delta) < research_config["evidence_threshold"]:
            applied_delta = 0
        else:
            applied_delta = raw_delta

        assert applied_delta == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fibonacci_clamping(self) -> None:
        """Scenario: Adjusted scores clamp to nearest Fibonacci.

        Given a raw adjusted score
        When clamping to the Fibonacci scale
        Then result is the nearest valid Fibonacci number.
        """
        # Arrange
        fib = self.FIBONACCI

        # Act
        def clamp_to_fibonacci(raw: float) -> int:
            return min(fib, key=lambda f: abs(f - raw))

        # Assert
        assert clamp_to_fibonacci(2.8) == 3  # Closer to 3 than 2
        assert clamp_to_fibonacci(4.5) == 5  # Closer to 5 than 3
        assert clamp_to_fibonacci(1.0) == 1
        assert clamp_to_fibonacci(12.9) == 13
        assert clamp_to_fibonacci(6.8) == 8

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_max_delta_constraint(self) -> None:
        """Scenario: Adjustments capped at max_delta Fibonacci steps.

        Given a max_delta of 2 Fibonacci steps
        When a raw delta would exceed max_delta
        Then the result is capped at max_delta steps away.
        """
        # Arrange
        fib = self.FIBONACCI
        max_steps = 2

        # Act
        def max_delta_clamp(initial: int, target: int, max_s: int = max_steps) -> int:
            initial_idx = fib.index(initial)
            target_idx = fib.index(target)
            if abs(target_idx - initial_idx) <= max_s:
                return target
            direction = 1 if target_idx > initial_idx else -1
            return fib[initial_idx + direction * max_s]

        # Assert - within bounds
        assert max_delta_clamp(3, 8, 2) == 8  # 2 steps: OK
        # Exceeds bounds: 3 -> 13 is 4 steps
        assert max_delta_clamp(3, 13, 2) == 8  # Capped at 2 steps up
        # Negative direction
        assert max_delta_clamp(8, 2, 2) == 3  # Capped at 2 steps down

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graceful_degradation(self, feature_with_initial_scores) -> None:
        """Scenario: Scores unchanged when research unavailable.

        Given the tome plugin is not installed
        When research enrichment is attempted
        Then initial scores should remain unchanged.
        """
        # Arrange
        initial = feature_with_initial_scores
        tome_available = False

        # Act
        if not tome_available:
            adjusted = initial["value"].copy()
        else:
            adjusted = dict(initial["value"].items())  # Would apply deltas

        # Assert - scores identical
        assert adjusted == initial["value"]
        assert adjusted["reach"] == 5
        assert adjusted["impact"] == 3

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_channel_factor_mapping(self) -> None:
        """Scenario: Research channels map to correct scoring
        factors.

        Given the channel-to-factor mapping table
        When looking up a channel's primary factor
        Then it should map to the correct scoring factor.
        """
        # Arrange
        channel_mapping = {
            "code_search": ("reach", "complexity"),
            "discourse": ("impact", "business_value"),
            "papers": ("impact", "risk"),
            "triz": ("business_value", "impact"),
        }

        # Assert
        assert channel_mapping["code_search"][0] == "reach"
        assert channel_mapping["discourse"][0] == "impact"
        assert channel_mapping["papers"][0] == "impact"
        assert channel_mapping["triz"][0] == "business_value"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_adjusted_score_with_research(self) -> None:
        """Scenario: Research enriches a feature's score.

        Given a feature with initial scores and research findings
        When applying research deltas
        Then the adjusted score reflects external evidence.
        """
        # Arrange
        initial_reach = 3
        research_delta = 2  # Strong adoption signal
        fib = self.FIBONACCI

        # Act - apply delta and clamp
        raw_adjusted = initial_reach + research_delta
        adjusted = min(fib, key=lambda f: abs(f - raw_adjusted))

        # Assert
        assert adjusted == 5  # 3 + 2 = 5, exact Fibonacci match
        assert adjusted > initial_reach  # Research increased score

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_research_does_not_reduce_below_minimum(
        self,
    ) -> None:
        """Scenario: Research cannot reduce score below 1.

        Given a feature with low initial score
        When negative research delta is applied
        Then adjusted score is at least 1 (minimum Fibonacci).
        """
        # Arrange
        fib = self.FIBONACCI
        initial = 2
        negative_delta = -5

        # Act
        raw = initial + negative_delta  # -3
        adjusted = max(min(fib, key=lambda f: abs(f - raw)), 1)

        # Assert
        assert adjusted == 1  # Floor is 1
