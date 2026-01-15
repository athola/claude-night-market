"""Tests for feature-review skill scoring and classification logic.

This module tests the RICE+WSJF hybrid scoring framework and the
Static/Dynamic, Proactive/Reactive classification system.

Following TDD/BDD principles to ensure scoring calculations are accurate
and classification logic correctly categorizes features.
"""

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
    def test_priority_thresholds(self) -> None:
        """Scenario: Feature scores map to priority levels.

        Given the scoring threshold configuration
        When a feature score is evaluated
        Then it should map to the correct priority level.
        """
        # Arrange - thresholds from scoring-framework.md
        thresholds = {"high": 2.5, "medium": 1.5, "low": 1.0}

        # Act & Assert
        def get_priority(score: float) -> str:
            if score > thresholds["high"]:
                return "High"
            elif score >= thresholds["medium"]:
                return "Medium"
            elif score >= thresholds["low"]:
                return "Low"
            else:
                return "Very Low"

        assert get_priority(3.0) == "High"
        assert get_priority(2.5) == "Medium"  # Boundary: not > 2.5
        assert get_priority(2.0) == "Medium"
        assert get_priority(1.5) == "Medium"  # Boundary: >= 1.5
        assert get_priority(1.2) == "Low"
        assert get_priority(1.0) == "Low"  # Boundary: >= 1.0
        assert get_priority(0.8) == "Very Low"

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
    def test_2x2_matrix_classification(self, feature_examples) -> None:
        """Scenario: Features map to one of four archetypes.

        Given the 2x2 classification matrix
        When classifying features
        Then each should map to exactly one archetype.
        """

        # Arrange
        def classify(feature: dict) -> str:
            is_proactive = (
                feature["anticipates_need"] and not feature["triggered_by_user"]
            )
            is_dynamic = feature["data_changes_realtime"]

            if is_proactive and not is_dynamic:
                return "Predictive Cache"
            elif is_proactive and is_dynamic:
                return "Smart Assistant"
            elif not is_proactive and not is_dynamic:
                return "Reference Lookup"
            else:
                return "Interactive Query"

        # Act & Assert
        assert classify(feature_examples["auto_save"]) == "Predictive Cache"
        assert classify(feature_examples["suggestions"]) == "Smart Assistant"
        assert classify(feature_examples["config_loader"]) == "Reference Lookup"
        assert classify(feature_examples["search"]) == "Interactive Query"

    @pytest.mark.unit
    def test_archetype_characteristics(self) -> None:
        """Scenario: Each archetype has expected characteristics.

        Given the four archetypes
        When examining their characteristics
        Then they should have expected latency and complexity profiles.
        """
        # Arrange
        archetypes = {
            "Predictive Cache": {"latency": "Low", "complexity": "Low"},
            "Smart Assistant": {"latency": "Medium", "complexity": "High"},
            "Reference Lookup": {"latency": "Very Low", "complexity": "Low"},
            "Interactive Query": {"latency": "Low", "complexity": "Medium"},
        }

        # Assert
        assert archetypes["Predictive Cache"]["complexity"] == "Low"
        assert archetypes["Smart Assistant"]["complexity"] == "High"
        assert archetypes["Reference Lookup"]["latency"] == "Very Low"
        assert archetypes["Interactive Query"]["complexity"] == "Medium"


class TestKanoClassification:
    """Feature: Features are classified using Kano model.

    As a product manager
    I want features categorized by user satisfaction impact
    So that I can prioritize appropriately
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_basic_features_must_exist(self) -> None:
        """Scenario: Basic features are expected by users.

        Given a Basic (Must-Have) feature
        When the feature is missing
        Then users are dissatisfied
        And when present, satisfaction is neutral.
        """
        # Arrange
        basic_feature = {
            "name": "Login functionality",
            "kano_type": "Basic",
            "absence_impact": "Dissatisfaction",
            "presence_impact": "Neutral",
        }

        # Assert
        assert basic_feature["kano_type"] == "Basic"
        assert basic_feature["absence_impact"] == "Dissatisfaction"
        assert basic_feature["presence_impact"] == "Neutral"

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

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_delighter_features_surprise_users(self) -> None:
        """Scenario: Delighter features create unexpected joy.

        Given a Delighter (Wow Factor) feature
        When the feature is absent
        Then users are not dissatisfied
        And when present, users are delighted.
        """
        # Arrange
        delighter_feature = {
            "name": "AI-powered suggestions",
            "kano_type": "Delighter",
            "absence_impact": "Neutral",
            "presence_impact": "Delight",
        }

        # Assert
        assert delighter_feature["kano_type"] == "Delighter"
        assert delighter_feature["absence_impact"] == "Neutral"
        assert delighter_feature["presence_impact"] == "Delight"

    @pytest.mark.unit
    def test_kano_priority_order(self) -> None:
        """Scenario: Kano types have a recommended implementation order.

        Given features of different Kano types
        When prioritizing implementation
        Then Basic features should come first
        And Delighters should come after Performance.
        """
        # Arrange
        priority_order = ["Basic", "Performance", "Delighter", "Indifferent"]

        # Assert
        assert priority_order.index("Basic") < priority_order.index("Performance")
        assert priority_order.index("Performance") < priority_order.index("Delighter")
        assert priority_order.index("Delighter") < priority_order.index("Indifferent")


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
    def test_suggestion_labels(self) -> None:
        """Scenario: Suggestions get appropriate labels based on priority.

        Given a feature suggestion with a priority score
        When creating a GitHub issue
        Then it should have appropriate priority labels.
        """

        # Arrange
        def get_labels(score: float) -> list[str]:
            labels = ["enhancement"]
            if score > 2.5:
                labels.append("priority:high")
            elif score >= 1.5:
                labels.append("priority:medium")
            else:
                labels.append("priority:low")
            return labels

        # Assert
        assert "priority:high" in get_labels(3.0)
        assert "priority:medium" in get_labels(2.0)
        assert "priority:low" in get_labels(1.0)
        assert "enhancement" in get_labels(2.0)

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
