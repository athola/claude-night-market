"""Tests for ImprovementMemory persistent improvement insight store."""

from pathlib import Path

import pytest

from abstract.improvement_memory import ImprovementMemory, ImprovementOutcome

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem(tmp_path: Path) -> ImprovementMemory:
    """Fresh ImprovementMemory backed by a temp file."""
    return ImprovementMemory(tmp_path / "improvement_memory.json")


@pytest.fixture()
def mem_file(tmp_path: Path) -> Path:
    """Return the path used by the shared memory fixture."""
    return tmp_path / "improvement_memory.json"


# ---------------------------------------------------------------------------
# Insight recording
# ---------------------------------------------------------------------------


class TestRecordInsight:
    """Record synthesized insights with category validation."""

    def test_record_insight_valid_categories(self, mem: ImprovementMemory) -> None:
        """Scenario: All five valid categories are accepted
        Given a fresh memory store
        When record_insight is called with each valid category
        Then each call returns True and the insight is stored
        """
        for category in ImprovementMemory.CATEGORIES:
            result = mem.record_insight(
                skill_ref="abstract:test-skill",
                category=category,
                insight=f"Insight for {category}",
            )
            assert result is True, f"Expected True for category {category!r}"

        stored = mem.insights["abstract:test-skill"]
        assert len(stored) == len(ImprovementMemory.CATEGORIES)

    def test_record_insight_invalid_category(
        self, mem: ImprovementMemory, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: Unknown category is rejected
        Given a fresh memory store
        When record_insight is called with an unknown category
        Then it returns False and emits a warning to stderr
        """
        result = mem.record_insight(
            skill_ref="abstract:test-skill",
            category="totally_made_up",
            insight="Should not be stored",
        )
        assert result is False
        captured = capsys.readouterr()
        assert "totally_made_up" in captured.err
        assert "abstract:test-skill" not in mem.insights  # nothing stored

    def test_record_insight_stores_evidence(self, mem: ImprovementMemory) -> None:
        """Scenario: Evidence list is persisted alongside the insight
        Given a fresh memory store
        When record_insight is called with an evidence list
        Then the stored entry contains that evidence
        """
        mem.record_insight(
            skill_ref="abstract:test-skill",
            category="causal_hypothesis",
            insight="Adding examples improved pass rate",
            evidence=["run-001", "run-002"],
        )
        entry = mem.insights["abstract:test-skill"][0]
        assert entry["evidence"] == ["run-001", "run-002"]

    def test_record_insight_defaults_evidence_to_empty(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Omitting evidence defaults to an empty list
        Given a fresh memory store
        When record_insight is called without evidence
        Then the stored entry has evidence = []
        """
        mem.record_insight(
            skill_ref="abstract:test-skill",
            category="strategy_success",
            insight="Works without evidence",
        )
        entry = mem.insights["abstract:test-skill"][0]
        assert entry["evidence"] == []


# ---------------------------------------------------------------------------
# Outcome recording
# ---------------------------------------------------------------------------


class TestRecordImprovementOutcome:
    """Record before/after scores and classify success/failure/neutral."""

    def test_record_improvement_outcome_success(self, mem: ImprovementMemory) -> None:
        """Scenario: after > before is classified as success
        Given a fresh memory store
        When an outcome with after_score > before_score is recorded
        Then outcome_type is 'success' and improvement is positive
        """
        mem.record_improvement_outcome(
            skill_ref="abstract:test-skill",
            outcome=ImprovementOutcome("v1.1", "Added concrete examples", 0.60, 0.80),
        )
        outcome = mem.outcomes["abstract:test-skill"][0]
        assert outcome["outcome_type"] == "success"
        assert outcome["improvement"] == pytest.approx(0.20)

    def test_record_improvement_outcome_failure(self, mem: ImprovementMemory) -> None:
        """Scenario: after < before is classified as failure
        Given a fresh memory store
        When an outcome with after_score < before_score is recorded
        Then outcome_type is 'failure' and improvement is negative
        """
        mem.record_improvement_outcome(
            skill_ref="abstract:test-skill",
            outcome=ImprovementOutcome("v1.2", "Removed section headers", 0.80, 0.60),
        )
        outcome = mem.outcomes["abstract:test-skill"][0]
        assert outcome["outcome_type"] == "failure"
        assert outcome["improvement"] == pytest.approx(-0.20)

    def test_record_improvement_outcome_neutral(self, mem: ImprovementMemory) -> None:
        """Scenario: after == before is classified as neutral
        Given a fresh memory store
        When an outcome with equal scores is recorded
        Then outcome_type is 'neutral' and improvement is 0.0
        """
        mem.record_improvement_outcome(
            skill_ref="abstract:test-skill",
            outcome=ImprovementOutcome("v1.3", "Reformatted whitespace", 0.70, 0.70),
        )
        outcome = mem.outcomes["abstract:test-skill"][0]
        assert outcome["outcome_type"] == "neutral"
        assert outcome["improvement"] == pytest.approx(0.0)

    def test_record_improvement_outcome_stores_hypothesis(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Hypothesis is stored alongside the outcome
        Given a fresh memory store
        When an outcome is recorded with a hypothesis
        Then the stored entry contains that hypothesis
        """
        mem.record_improvement_outcome(
            skill_ref="abstract:test-skill",
            outcome=ImprovementOutcome(
                "v1.4",
                "Clarified output format",
                0.50,
                0.75,
                hypothesis="Explicit format constraints reduce ambiguity",
            ),
        )
        outcome = mem.outcomes["abstract:test-skill"][0]
        assert outcome["hypothesis"] == "Explicit format constraints reduce ambiguity"


# ---------------------------------------------------------------------------
# Retrieval: effective strategies
# ---------------------------------------------------------------------------


class TestGetEffectiveStrategies:
    """Filter and sort outcomes that crossed the improvement threshold."""

    def test_get_effective_strategies(self, mem: ImprovementMemory) -> None:
        """Scenario: Only outcomes meeting min_improvement threshold are returned
        Given outcomes with varying improvements
        When get_effective_strategies is called with default threshold 0.1
        Then only outcomes with improvement >= 0.1 are returned
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "big win", 0.5, 0.8)
        )
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v2", "tiny win", 0.5, 0.55)
        )
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v3", "regression", 0.5, 0.3)
        )

        results = mem.get_effective_strategies(skill_ref="abstract:skill-a")
        assert len(results) == 1
        assert results[0]["change_summary"] == "big win"

    def test_get_effective_strategies_sorted_descending(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Results are sorted by improvement magnitude descending
        Given two successful outcomes with different improvement sizes
        When get_effective_strategies is called
        Then the larger improvement appears first
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "medium", 0.5, 0.7)
        )
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v2", "large", 0.5, 0.9)
        )

        results = mem.get_effective_strategies(skill_ref="abstract:skill-a")
        assert results[0]["change_summary"] == "large"
        assert results[1]["change_summary"] == "medium"

    def test_get_effective_strategies_skill_filter(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: skill_ref filter scopes results to one skill
        Given outcomes for two different skills
        When get_effective_strategies is called with a specific skill_ref
        Then only outcomes for that skill are returned
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "win for A", 0.5, 0.8)
        )
        mem.record_improvement_outcome(
            "abstract:skill-b", ImprovementOutcome("v1", "win for B", 0.5, 0.9)
        )

        results = mem.get_effective_strategies(skill_ref="abstract:skill-a")
        assert len(results) == 1
        assert results[0]["change_summary"] == "win for A"

    def test_get_effective_strategies_cross_skill_no_filter(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Omitting skill_ref returns effective strategies across all skills
        Given outcomes for two different skills
        When get_effective_strategies is called without a skill_ref
        Then results span all skills
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "win for A", 0.5, 0.8)
        )
        mem.record_improvement_outcome(
            "abstract:skill-b", ImprovementOutcome("v1", "win for B", 0.5, 0.9)
        )

        results = mem.get_effective_strategies()
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Retrieval: failed strategies
# ---------------------------------------------------------------------------


class TestGetFailedStrategies:
    """Filter outcomes that caused regression."""

    def test_get_failed_strategies(self, mem: ImprovementMemory) -> None:
        """Scenario: Only regressions (improvement < 0) are returned
        Given mixed outcomes
        When get_failed_strategies is called
        Then only outcomes with negative improvement are returned
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "good change", 0.5, 0.8)
        )
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v2", "bad change", 0.8, 0.5)
        )
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v3", "neutral change", 0.5, 0.5)
        )

        results = mem.get_failed_strategies(skill_ref="abstract:skill-a")
        assert len(results) == 1
        assert results[0]["change_summary"] == "bad change"

    def test_get_failed_strategies_empty_when_no_regressions(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: No regressions returns empty list
        Given only successful outcomes
        When get_failed_strategies is called
        Then an empty list is returned
        """
        mem.record_improvement_outcome(
            "abstract:skill-a", ImprovementOutcome("v1", "good change", 0.5, 0.8)
        )
        assert mem.get_failed_strategies(skill_ref="abstract:skill-a") == []


# ---------------------------------------------------------------------------
# Retrieval: causal hypotheses
# ---------------------------------------------------------------------------


class TestGetCausalHypotheses:
    """Return only causal_hypothesis insights, most recent first."""

    def test_get_causal_hypotheses(self, mem: ImprovementMemory) -> None:
        """Scenario: Only causal_hypothesis category insights are returned
        Given insights of multiple categories
        When get_causal_hypotheses is called
        Then only causal_hypothesis entries are returned
        """
        mem.record_insight("abstract:test-skill", "causal_hypothesis", "Hypothesis A")
        mem.record_insight(
            "abstract:test-skill", "strategy_success", "Not a hypothesis"
        )
        mem.record_insight("abstract:test-skill", "causal_hypothesis", "Hypothesis B")

        results = mem.get_causal_hypotheses("abstract:test-skill")
        assert len(results) == 2
        assert all(r["category"] == "causal_hypothesis" for r in results)

    def test_get_causal_hypotheses_sorted_by_recency(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Results are sorted most recent first
        Given two causal hypotheses recorded in order
        When get_causal_hypotheses is called
        Then the more recently recorded one appears first
        """
        mem.record_insight(
            "abstract:test-skill", "causal_hypothesis", "Older hypothesis"
        )
        mem.record_insight(
            "abstract:test-skill", "causal_hypothesis", "Newer hypothesis"
        )

        results = mem.get_causal_hypotheses("abstract:test-skill")
        assert results[0]["insight"] == "Newer hypothesis"
        assert results[1]["insight"] == "Older hypothesis"

    def test_get_causal_hypotheses_empty_for_unknown_skill(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Unknown skill returns empty list
        Given an empty memory store
        When get_causal_hypotheses is called for a non-existent skill
        Then an empty list is returned
        """
        assert mem.get_causal_hypotheses("abstract:nonexistent") == []


# ---------------------------------------------------------------------------
# Retrieval: insights by category
# ---------------------------------------------------------------------------


class TestGetInsightsByCategory:
    """Filter insights by category, with optional skill scope."""

    def test_get_insights_by_category(self, mem: ImprovementMemory) -> None:
        """Scenario: Insights filtered to a single category
        Given insights of multiple categories for a skill
        When get_insights_by_category is called with a specific category
        Then only matching insights are returned
        """
        mem.record_insight("abstract:test-skill", "strategy_success", "This worked")
        mem.record_insight("abstract:test-skill", "strategy_failure", "This failed")
        mem.record_insight(
            "abstract:test-skill", "strategy_success", "This also worked"
        )

        results = mem.get_insights_by_category(
            "strategy_success", skill_ref="abstract:test-skill"
        )
        assert len(results) == 2
        assert all(r["category"] == "strategy_success" for r in results)

    def test_get_insights_by_category_cross_skill(self, mem: ImprovementMemory) -> None:
        """Scenario: Omitting skill_ref returns matching insights from all skills
        Given insights for two different skills
        When get_insights_by_category is called without skill_ref
        Then matching insights from both skills are returned
        """
        mem.record_insight("abstract:skill-a", "strategy_success", "A worked")
        mem.record_insight("abstract:skill-b", "strategy_success", "B worked")
        mem.record_insight("abstract:skill-b", "strategy_failure", "B failed")

        results = mem.get_insights_by_category("strategy_success")
        assert len(results) == 2

    def test_get_insights_by_category_all_categories(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Each valid category can be retrieved
        Given one insight of each valid category
        When get_insights_by_category is called for each
        Then exactly one result is returned per category
        """
        for category in ImprovementMemory.CATEGORIES:
            mem.record_insight(
                "abstract:test-skill", category, f"Insight for {category}"
            )

        for category in ImprovementMemory.CATEGORIES:
            results = mem.get_insights_by_category(
                category, skill_ref="abstract:test-skill"
            )
            assert len(results) == 1, f"Expected 1 result for {category!r}"


# ---------------------------------------------------------------------------
# Forward plan synthesis
# ---------------------------------------------------------------------------


class TestSynthesizeForwardPlan:
    """Produce a deterministic forward-looking improvement plan."""

    def test_synthesize_forward_plan(self, mem: ImprovementMemory) -> None:
        """Scenario: Plan contains all required keys with appropriate content
        Given a skill with outcomes and hypotheses
        When synthesize_forward_plan is called
        Then the result has all four required keys with non-empty content
        """
        mem.record_improvement_outcome(
            "abstract:test-skill", ImprovementOutcome("v1", "Added examples", 0.5, 0.8)
        )
        mem.record_improvement_outcome(
            "abstract:test-skill", ImprovementOutcome("v2", "Removed headers", 0.8, 0.6)
        )
        mem.record_insight(
            "abstract:test-skill",
            "causal_hypothesis",
            "Examples reduce ambiguity",
        )

        plan = mem.synthesize_forward_plan("abstract:test-skill")

        assert set(plan.keys()) == {
            "effective_strategies",
            "failed_strategies",
            "hypotheses",
            "recommended_approach",
        }
        assert len(plan["effective_strategies"]) == 1
        assert len(plan["failed_strategies"]) == 1
        assert len(plan["hypotheses"]) == 1
        assert isinstance(plan["recommended_approach"], str)
        assert len(plan["recommended_approach"]) > 0

    def test_synthesize_forward_plan_empty(self, mem: ImprovementMemory) -> None:
        """Scenario: Plan for a skill with no data returns sensible defaults
        Given an empty memory store
        When synthesize_forward_plan is called for a non-existent skill
        Then all list values are empty and recommended_approach is a string
        """
        plan = mem.synthesize_forward_plan("abstract:brand-new-skill")

        assert plan["effective_strategies"] == []
        assert plan["failed_strategies"] == []
        assert plan["hypotheses"] == []
        assert isinstance(plan["recommended_approach"], str)
        assert len(plan["recommended_approach"]) > 0

    def test_synthesize_forward_plan_recommends_best_strategy(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Recommended approach references the best effective strategy
        Given a skill with a successful outcome
        When synthesize_forward_plan is called
        Then recommended_approach mentions that change summary
        """
        mem.record_improvement_outcome(
            "abstract:test-skill",
            ImprovementOutcome("v1", "Added concrete examples", 0.5, 0.8),
        )

        plan = mem.synthesize_forward_plan("abstract:test-skill")
        assert "Added concrete examples" in plan["recommended_approach"]

    def test_synthesize_forward_plan_uses_hypothesis_when_no_successes(
        self, mem: ImprovementMemory
    ) -> None:
        """Scenario: Falls back to hypothesis when no successful outcomes exist
        Given only a causal hypothesis (no successful outcomes)
        When synthesize_forward_plan is called
        Then recommended_approach references the hypothesis
        """
        mem.record_insight(
            "abstract:test-skill",
            "causal_hypothesis",
            "Try structured output first",
        )

        plan = mem.synthesize_forward_plan("abstract:test-skill")
        assert "Try structured output first" in plan["recommended_approach"]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    """Data survives instance recreation."""

    def test_persistence(self, tmp_path: Path) -> None:
        """Scenario: Written data is available after a new instance loads the file
        Given a memory store that has recorded insights and outcomes
        When a new ImprovementMemory instance is created from the same file
        Then the previously stored data is present
        """
        memory_file = tmp_path / "improvement_memory.json"

        first = ImprovementMemory(memory_file)
        first.record_insight("abstract:test-skill", "strategy_success", "It worked")
        first.record_improvement_outcome(
            "abstract:test-skill", ImprovementOutcome("v1", "Big change", 0.4, 0.9)
        )

        second = ImprovementMemory(memory_file)
        assert len(second.insights["abstract:test-skill"]) == 1
        assert len(second.outcomes["abstract:test-skill"]) == 1
        assert second.insights["abstract:test-skill"][0]["insight"] == "It worked"

    def test_corrupt_file(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Scenario: Corrupt JSON file is handled gracefully
        Given a memory file containing malformed JSON
        When ImprovementMemory is created
        Then it starts with empty state and emits a warning to stderr
        """
        memory_file = tmp_path / "improvement_memory.json"
        memory_file.write_text("{this is not valid json")

        mem = ImprovementMemory(memory_file)

        assert mem.insights == {}
        assert mem.outcomes == {}
        captured = capsys.readouterr()
        assert "corrupt" in captured.err


# ---------------------------------------------------------------------------
# Pruning
# ---------------------------------------------------------------------------


class TestPruning:
    """Exceeding limits prunes oldest entries."""

    def test_pruning_insights(self, mem: ImprovementMemory) -> None:
        """Scenario: Storing beyond MAX_INSIGHTS_PER_SKILL prunes oldest entries
        Given MAX_INSIGHTS_PER_SKILL + 5 insights recorded
        When insights are retrieved
        Then only MAX_INSIGHTS_PER_SKILL entries remain (the most recent)
        """
        limit = ImprovementMemory.MAX_INSIGHTS_PER_SKILL
        for i in range(limit + 5):
            mem.record_insight(
                "abstract:test-skill",
                "strategy_success",
                f"Insight number {i}",
            )

        stored = mem.insights["abstract:test-skill"]
        assert len(stored) == limit
        # Most recent entries are kept
        assert stored[-1]["insight"] == f"Insight number {limit + 4}"

    def test_pruning_outcomes(self, mem: ImprovementMemory) -> None:
        """Scenario: Storing beyond MAX_OUTCOMES_PER_SKILL prunes oldest entries
        Given MAX_OUTCOMES_PER_SKILL + 5 outcomes recorded
        When outcomes are retrieved
        Then only MAX_OUTCOMES_PER_SKILL entries remain (the most recent)
        """
        limit = ImprovementMemory.MAX_OUTCOMES_PER_SKILL
        for i in range(limit + 5):
            mem.record_improvement_outcome(
                "abstract:test-skill",
                ImprovementOutcome(f"v{i}", f"Change {i}", 0.5, 0.6),
            )

        stored = mem.outcomes["abstract:test-skill"]
        assert len(stored) == limit
        assert stored[-1]["change_summary"] == f"Change {limit + 4}"
