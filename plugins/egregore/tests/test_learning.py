"""Tests for cross-item learning via decision log analysis."""

from __future__ import annotations

from pathlib import Path

import pytest
from learning import (
    LearnedPattern,
    _categorize_decision,
    build_learning_context,
    extract_patterns,
    load_patterns,
    save_patterns,
    weight_by_recency,
)


class TestExtractPatterns:
    """Feature: Pattern extraction from decision logs.

    As an egregore orchestrator
    I want to extract patterns from completed work items' decisions
    So that future work items benefit from past experience
    """

    def test_empty_items_returns_no_patterns(self) -> None:
        """Scenario: No work items to learn from.

        Given an empty list of work items
        When patterns are extracted
        Then the result is an empty list
        """
        result = extract_patterns([])
        assert result == []

    def test_single_completed_item_with_one_decision(self) -> None:
        """Scenario: One completed item with a single decision.

        Given a completed work item with one decision
        When patterns are extracted
        Then one pattern is returned with 100% success rate
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "started_at": "2026-03-10T00:00:00+00:00",
                "decisions": [
                    {
                        "step": "brainstorm",
                        "chose": "use Flask framework",
                        "why": "lightweight",
                    },
                ],
            }
        ]
        patterns = extract_patterns(items)
        assert len(patterns) == 1
        assert patterns[0].frequency == 1
        assert patterns[0].success_rate == 1.0
        assert "wrk_001" in patterns[0].source_items

    def test_repeated_decision_across_items_increases_frequency(self) -> None:
        """Scenario: Same decision appears in multiple items.

        Given two completed items with the same step+choice
        When patterns are extracted
        Then the pattern frequency is 2
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "decisions": [
                    {"step": "brainstorm", "chose": "use pytest", "why": "standard"},
                ],
            },
            {
                "id": "wrk_002",
                "status": "completed",
                "decisions": [
                    {"step": "brainstorm", "chose": "use pytest", "why": "convention"},
                ],
            },
        ]
        patterns = extract_patterns(items)
        assert len(patterns) == 1
        assert patterns[0].frequency == 2
        assert patterns[0].success_rate == 1.0
        assert set(patterns[0].source_items) == {"wrk_001", "wrk_002"}

    def test_failed_item_lowers_success_rate(self) -> None:
        """Scenario: A failed item uses the same decision as a completed one.

        Given one completed and one failed item with the same decision
        When patterns are extracted
        Then the success rate reflects the mixed outcomes
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "decisions": [
                    {"step": "execute", "chose": "monolith", "why": "simple"},
                ],
            },
            {
                "id": "wrk_002",
                "status": "failed",
                "decisions": [
                    {"step": "execute", "chose": "monolith", "why": "simple"},
                ],
            },
        ]
        patterns = extract_patterns(items)
        assert len(patterns) == 1
        assert patterns[0].frequency == 2
        assert patterns[0].success_rate == pytest.approx(0.5)

    def test_empty_chose_field_is_skipped(self) -> None:
        """Scenario: A decision with an empty 'chose' field.

        Given a work item with a decision that has an empty chose value
        When patterns are extracted
        Then that decision is ignored
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "decisions": [
                    {"step": "brainstorm", "chose": "", "why": ""},
                ],
            }
        ]
        patterns = extract_patterns(items)
        assert patterns == []

    def test_max_patterns_limits_output(self) -> None:
        """Scenario: More patterns than the max limit.

        Given work items producing many distinct patterns
        When extract_patterns is called with max_patterns=2
        Then at most 2 patterns are returned
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "decisions": [
                    {"step": "s1", "chose": "a", "why": ""},
                    {"step": "s2", "chose": "b", "why": ""},
                    {"step": "s3", "chose": "c", "why": ""},
                ],
            }
        ]
        patterns = extract_patterns(items, max_patterns=2)
        assert len(patterns) <= 2

    def test_patterns_sorted_by_weighted_relevance(self) -> None:
        """Scenario: Patterns are ranked by frequency * success_rate.

        Given items where one decision appears twice (completed) and
              another appears once (completed)
        When patterns are extracted
        Then the more frequent pattern ranks first
        """
        items = [
            {
                "id": "wrk_001",
                "status": "completed",
                "decisions": [
                    {"step": "build", "chose": "approach-A", "why": ""},
                    {"step": "build", "chose": "approach-B", "why": ""},
                ],
            },
            {
                "id": "wrk_002",
                "status": "completed",
                "decisions": [
                    {"step": "build", "chose": "approach-A", "why": ""},
                ],
            },
        ]
        patterns = extract_patterns(items)
        # approach-A: freq=2, rate=1.0, score=2.0
        # approach-B: freq=1, rate=1.0, score=1.0
        assert patterns[0].description.startswith("build: approach-A")


class TestCategorizeDecision:
    """Feature: Decision categorization.

    As a learning module
    I want to categorize decisions by their content
    So that patterns are grouped meaningfully
    """

    def test_tech_stack_keywords(self) -> None:
        """Scenario: Decision mentions a framework.

        Given a choice containing 'framework'
        When categorized
        Then the category is 'tech_stack'
        """
        assert _categorize_decision("build", "use Flask framework") == "tech_stack"
        assert _categorize_decision("build", "pick library X") == "tech_stack"
        assert _categorize_decision("build", "choose tool Y") == "tech_stack"

    def test_failure_mode_keywords(self) -> None:
        """Scenario: Decision mentions failure handling.

        Given a choice containing 'retry' or 'error'
        When categorized
        Then the category is 'failure_mode'
        """
        assert _categorize_decision("execute", "retry with backoff") == "failure_mode"
        assert (
            _categorize_decision("execute", "handle error gracefully") == "failure_mode"
        )
        assert _categorize_decision("execute", "skip flaky test") == "failure_mode"

    def test_architecture_keywords(self) -> None:
        """Scenario: Decision mentions architecture.

        Given a choice containing 'pattern' or 'design'
        When categorized
        Then the category is 'architecture'
        """
        assert _categorize_decision("specify", "use observer pattern") == "architecture"
        assert _categorize_decision("specify", "MVC design") == "architecture"

    def test_default_is_approach(self) -> None:
        """Scenario: Decision has no recognized keywords.

        Given a generic choice
        When categorized
        Then the category defaults to 'approach'
        """
        assert _categorize_decision("brainstorm", "just do it") == "approach"


class TestBuildLearningContext:
    """Feature: Context string generation for orchestrator injection.

    As an orchestrator
    I want a formatted summary of learned patterns
    So that I can prepend it to my context for a new work item
    """

    def test_empty_patterns_returns_empty_string(self) -> None:
        """Scenario: No patterns available.

        Given an empty list of patterns
        When building learning context
        Then an empty string is returned
        """
        assert build_learning_context([]) == ""

    def test_context_includes_heading(self) -> None:
        """Scenario: Patterns produce a heading.

        Given at least one pattern
        When building learning context
        Then the output starts with a heading
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="build: do X",
                frequency=5,
                success_count=4,
            )
        ]
        ctx = build_learning_context(patterns)
        assert ctx.startswith("## Learned Patterns from Previous Work Items")

    def test_success_indicator_for_high_rate(self) -> None:
        """Scenario: High success rate gets SUCCESS indicator.

        Given a pattern with success_rate >= 0.5
        When building learning context
        Then the line includes [SUCCESS]
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="build: do X",
                frequency=4,
                success_count=3,
            )
        ]
        ctx = build_learning_context(patterns)
        assert "[SUCCESS]" in ctx

    def test_caution_indicator_for_low_rate(self) -> None:
        """Scenario: Low success rate gets CAUTION indicator.

        Given a pattern with success_rate < 0.5
        When building learning context
        Then the line includes [CAUTION]
        """
        patterns = [
            LearnedPattern(
                category="failure_mode",
                description="execute: retry blindly",
                frequency=3,
                success_count=0,
            )
        ]
        ctx = build_learning_context(patterns)
        assert "[CAUTION]" in ctx

    def test_context_includes_frequency_and_rate(self) -> None:
        """Scenario: Context lines show frequency and success rate.

        Given a pattern with frequency=5 and success_rate=0.8
        When building learning context
        Then the output contains 'seen 5x' and '80% success'
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="build: X",
                frequency=5,
                success_count=4,
            )
        ]
        ctx = build_learning_context(patterns)
        assert "seen 5x" in ctx
        assert "80% success" in ctx


class TestWeightByRecency:
    """Feature: Recency-weighted pattern scoring.

    As a learning module
    I want to weight recent patterns more heavily
    So that stale patterns fade over time
    """

    def test_most_recent_pattern_keeps_full_frequency(self) -> None:
        """Scenario: The most recent pattern is not decayed.

        Given two patterns with different timestamps
        When weighted by recency
        Then the most recent pattern retains its original frequency
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="old",
                frequency=10,
                last_seen="2026-03-01T00:00:00+00:00",
            ),
            LearnedPattern(
                category="approach",
                description="new",
                frequency=10,
                last_seen="2026-03-15T00:00:00+00:00",
            ),
        ]
        result = weight_by_recency(patterns, decay_factor=0.5)
        # Most recent first after sorting
        assert result[0].description == "new"
        assert result[0].frequency == 10  # decay^0 = 1.0, no change

    def test_older_patterns_get_decayed_frequency(self) -> None:
        """Scenario: Older patterns have reduced frequency.

        Given two patterns where one is older
        When weighted with decay_factor=0.5
        Then the older pattern's frequency is halved
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="old",
                frequency=10,
                last_seen="2026-03-01T00:00:00+00:00",
            ),
            LearnedPattern(
                category="approach",
                description="new",
                frequency=10,
                last_seen="2026-03-15T00:00:00+00:00",
            ),
        ]
        result = weight_by_recency(patterns, decay_factor=0.5)
        assert result[1].description == "old"
        assert result[1].frequency == 5  # int(10 * 0.5^1)

    def test_frequency_never_drops_below_one(self) -> None:
        """Scenario: Extreme decay does not produce zero frequency.

        Given a pattern with frequency=1 and heavy decay
        When weighted by recency
        Then frequency stays at minimum of 1
        """
        patterns = [
            LearnedPattern(
                category="approach",
                description="recent",
                frequency=1,
                last_seen="2026-03-15T00:00:00+00:00",
            ),
            LearnedPattern(
                category="approach",
                description="ancient",
                frequency=1,
                last_seen="2026-01-01T00:00:00+00:00",
            ),
        ]
        result = weight_by_recency(patterns, decay_factor=0.01)
        for p in result:
            assert p.frequency >= 1


class TestLearnedPatternSerialization:
    """Feature: Pattern persistence via JSON serialization.

    As a learning module
    I want to save and load patterns to/from disk
    So that learning persists across sessions
    """

    def test_to_dict_roundtrip(self) -> None:
        """Scenario: Serialize and deserialize a pattern.

        Given a LearnedPattern with all fields set
        When serialized to dict and back
        Then all fields are preserved
        """
        original = LearnedPattern(
            category="tech_stack",
            description="build: use Flask framework (lightweight)",
            frequency=4,
            last_seen="2026-03-10T00:00:00+00:00",
            success_count=3,
            source_items=["wrk_001", "wrk_002", "wrk_003"],
        )
        d = original.to_dict()
        restored = LearnedPattern.from_dict(d)
        assert restored.category == original.category
        assert restored.description == original.description
        assert restored.frequency == original.frequency
        assert restored.last_seen == original.last_seen
        assert restored.success_count == original.success_count
        assert restored.success_rate == original.success_rate
        assert restored.source_items == original.source_items

    def test_from_dict_backward_compat_with_success_rate(self) -> None:
        """Scenario: Deserialize old format that has success_rate but no success_count.

        Given a dict with success_rate but no success_count
        When deserialized
        Then success_count is reconstructed from success_rate * frequency
        """
        d = {
            "category": "approach",
            "description": "test",
            "frequency": 4,
            "last_seen": "",
            "success_rate": 0.75,
            "source_items": [],
        }
        pattern = LearnedPattern.from_dict(d)
        assert pattern.success_count == 3  # round(0.75 * 4)
        assert pattern.success_rate == 0.75

    def test_from_dict_ignores_unknown_fields(self) -> None:
        """Scenario: Extra fields in dict are ignored.

        Given a dict with an unknown key
        When deserialized
        Then the unknown key is silently dropped
        """
        d = {
            "category": "approach",
            "description": "test",
            "frequency": 2,
            "last_seen": "",
            "success_count": 1,
            "source_items": [],
            "unknown_field": "should be ignored",
        }
        pattern = LearnedPattern.from_dict(d)
        assert pattern.category == "approach"
        assert not hasattr(pattern, "unknown_field")

    def test_save_and_load_patterns(self, tmp_path: Path) -> None:
        """Scenario: Save patterns to disk and reload them.

        Given a list of patterns
        When saved to a file and loaded back
        Then the loaded patterns match the originals
        """
        patterns = [
            LearnedPattern(
                category="tech_stack",
                description="use X",
                frequency=2,
                success_count=2,
                source_items=["wrk_001"],
            ),
            LearnedPattern(
                category="approach",
                description="try Y",
                frequency=2,
                success_count=1,
                source_items=["wrk_002"],
            ),
        ]
        path = tmp_path / "subdir" / "patterns.json"
        save_patterns(patterns, path)
        assert path.exists()

        loaded = load_patterns(path)
        assert len(loaded) == 2
        assert loaded[0].category == "tech_stack"
        assert loaded[0].frequency == 2
        assert loaded[1].description == "try Y"

    def test_load_patterns_from_nonexistent_file(self, tmp_path: Path) -> None:
        """Scenario: Loading from a missing file.

        Given a path that does not exist
        When load_patterns is called
        Then an empty list is returned
        """
        result = load_patterns(tmp_path / "nope.json")
        assert result == []

    def test_load_patterns_from_corrupt_file(self, tmp_path: Path) -> None:
        """Scenario: Loading from a corrupt JSON file.

        Given a file with invalid JSON
        When load_patterns is called
        Then an empty list is returned
        """
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all {{{")
        result = load_patterns(bad_file)
        assert result == []
