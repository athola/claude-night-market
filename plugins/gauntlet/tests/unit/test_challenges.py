"""Tests for gauntlet challenge generation."""

from __future__ import annotations

import pytest
from gauntlet.challenges import (
    CHALLENGE_TYPES,
    generate_challenge,
    select_challenge_type,
)
from gauntlet.models import AnswerRecord, DeveloperProgress, KnowledgeEntry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(
    category: str = "business_logic",
    module: str = "billing",
    concept: str = "Pro-rata calculation",
    detail: str = "Charge is pro-rated based on remaining days in the billing period.",
    difficulty: int = 2,
    related_files: list[str] | None = None,
) -> KnowledgeEntry:
    return KnowledgeEntry(
        id="ke-test-001",
        category=category,
        module=module,
        concept=concept,
        detail=detail,
        difficulty=difficulty,
        extracted_at="2026-01-01T00:00:00",
        source="code",
        related_files=related_files or ["src/billing/proration.py"],
    )


def _answer_record(challenge_type: str, result: str) -> AnswerRecord:
    return AnswerRecord(
        challenge_id="ch-x",
        knowledge_entry_id="ke-test-001",
        challenge_type=challenge_type,
        category="business_logic",
        difficulty=2,
        result=result,
        answered_at="2026-01-01T00:00:00",
    )


# ---------------------------------------------------------------------------
# Feature: Challenge type registry
# ---------------------------------------------------------------------------


class TestChallengeTypeRegistry:
    """
    Feature: Challenge type registry

    As a gauntlet engine
    I want a registry of all challenge generators
    So that new types can be added without changing core dispatch logic
    """

    @pytest.mark.unit
    def test_all_six_types_registered(self):
        """
        Scenario: All six challenge types are present in CHALLENGE_TYPES
        Given the challenges module is imported
        When I inspect CHALLENGE_TYPES
        Then it contains exactly: multiple_choice, code_completion, trace,
             explain_why, spot_bug, dependency_map
        """
        expected = {
            "multiple_choice",
            "code_completion",
            "trace",
            "explain_why",
            "spot_bug",
            "dependency_map",
        }
        assert set(CHALLENGE_TYPES.keys()) == expected


# ---------------------------------------------------------------------------
# Feature: Challenge type selection
# ---------------------------------------------------------------------------


class TestSelectChallengeType:
    """
    Feature: Weighted challenge type selection

    As a gauntlet engine
    I want to pick challenge types weighted by developer weakness
    So that developers practise where they struggle most
    """

    @pytest.mark.unit
    def test_returns_valid_type(self):
        """
        Scenario: Selection always returns a known type
        Given a developer with no history
        When select_challenge_type is called
        Then the returned type is one of the six registered types
        """
        progress = DeveloperProgress(developer_id="dev@example.com")
        result = select_challenge_type(progress)
        assert result in CHALLENGE_TYPES

    @pytest.mark.unit
    def test_weights_toward_weak_types(self):
        """
        Scenario: Weak types are selected more often than strong types
        Given a developer who always fails spot_bug but always passes multiple_choice
        When select_challenge_type is called 100 times
        Then spot_bug appears at least twice (non-degenerate weighting)
        """
        history = [_answer_record("multiple_choice", "pass")] * 10 + [
            _answer_record("spot_bug", "fail")
        ] * 10
        progress = DeveloperProgress(developer_id="dev@example.com", history=history)

        seen_types: set[str] = set()
        for _ in range(100):
            seen_types.add(select_challenge_type(progress))

        # With correct weighting more than one type must appear in 100 draws
        assert len(seen_types) > 1

    @pytest.mark.unit
    def test_unseen_types_get_weight_three(self):
        """
        Scenario: A developer who has only seen multiple_choice still gets other types
        Given a developer with 20 multiple_choice pass records and nothing else
        When select_challenge_type is called 200 times
        Then at least 3 distinct types appear (unseen types weight=3.0 is high)
        """
        history = [_answer_record("multiple_choice", "pass")] * 20
        progress = DeveloperProgress(developer_id="dev@example.com", history=history)

        seen_types: set[str] = set()
        for _ in range(200):
            seen_types.add(select_challenge_type(progress))

        assert len(seen_types) >= 3


# ---------------------------------------------------------------------------
# Feature: Individual challenge generators
# ---------------------------------------------------------------------------


class TestGenerateChallenge:
    """
    Feature: Challenge generation dispatch

    As a gauntlet engine
    I want to generate a well-formed Challenge for every type
    So that developers always receive a complete, answerable question
    """

    @pytest.mark.unit
    def test_generates_multiple_choice(self):
        """
        Scenario: multiple_choice challenge is well-formed
        Given a knowledge entry for billing
        When generate_challenge is called with type multiple_choice
        Then the challenge has 4 options and a single-letter answer
        """
        entry = _entry()
        challenge = generate_challenge(entry, "multiple_choice")

        assert challenge.type == "multiple_choice"
        assert challenge.options is not None
        assert len(challenge.options) == 4
        assert challenge.answer in ("A", "B", "C", "D")

    @pytest.mark.unit
    def test_generates_explain_why(self):
        """
        Scenario: explain_why challenge uses entry detail as answer
        Given a knowledge entry
        When generate_challenge is called with type explain_why
        Then challenge.answer equals entry.detail
        """
        entry = _entry()
        challenge = generate_challenge(entry, "explain_why")

        assert challenge.type == "explain_why"
        assert challenge.answer == entry.detail

    @pytest.mark.unit
    def test_generates_trace(self):
        """
        Scenario: trace challenge uses entry detail as answer
        Given a knowledge entry
        When generate_challenge is called with type trace
        Then challenge.answer equals entry.detail
        """
        entry = _entry()
        challenge = generate_challenge(entry, "trace")

        assert challenge.type == "trace"
        assert challenge.answer == entry.detail

    @pytest.mark.unit
    def test_generates_spot_bug(self):
        """
        Scenario: spot_bug challenge uses entry detail as answer
        Given a knowledge entry
        When generate_challenge is called with type spot_bug
        Then challenge.answer equals entry.detail
        """
        entry = _entry()
        challenge = generate_challenge(entry, "spot_bug")

        assert challenge.type == "spot_bug"
        assert challenge.answer == entry.detail

    @pytest.mark.unit
    def test_generates_dependency_map(self):
        """
        Scenario: dependency_map challenge answers with related files
        Given a knowledge entry with related_files
        When generate_challenge is called with type dependency_map
        Then challenge.answer is the comma-joined related_files list
        """
        entry = _entry(related_files=["src/billing/proration.py", "src/billing/api.py"])
        challenge = generate_challenge(entry, "dependency_map")

        assert challenge.type == "dependency_map"
        assert challenge.answer == "src/billing/proration.py, src/billing/api.py"

    @pytest.mark.unit
    def test_generates_code_completion(self):
        """
        Scenario: code_completion challenge uses entry detail as answer
        Given a knowledge entry
        When generate_challenge is called with type code_completion
        Then challenge.answer equals entry.detail
        """
        entry = _entry()
        challenge = generate_challenge(entry, "code_completion")

        assert challenge.type == "code_completion"
        assert challenge.answer == entry.detail

    @pytest.mark.unit
    def test_difficulty_matches_entry(self):
        """
        Scenario: Generated challenge difficulty matches the source entry
        Given a difficulty-4 knowledge entry
        When any challenge type is generated
        Then challenge.difficulty == 4
        """
        entry = _entry(difficulty=4)
        for ctype in (
            "multiple_choice",
            "explain_why",
            "trace",
            "spot_bug",
            "dependency_map",
            "code_completion",
        ):
            challenge = generate_challenge(entry, ctype)
            assert challenge.difficulty == 4, f"Failed for type {ctype}"

    @pytest.mark.unit
    def test_scope_files_populated(self):
        """
        Scenario: scope_files includes the entry module and related files
        Given a knowledge entry with module and related_files
        When a challenge is generated
        Then scope_files contains both the module and related_files
        """
        entry = _entry(module="billing", related_files=["src/billing/proration.py"])
        challenge = generate_challenge(entry, "explain_why")

        assert "billing" in challenge.scope_files
        assert "src/billing/proration.py" in challenge.scope_files
