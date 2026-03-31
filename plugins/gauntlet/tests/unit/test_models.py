"""Unit tests for gauntlet data models."""

from __future__ import annotations

import json

from gauntlet.models import (
    AnswerRecord,
    Challenge,
    DeveloperProgress,
    KnowledgeEntry,
    OnboardingProgress,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(**kwargs) -> KnowledgeEntry:
    defaults: dict = {
        "id": "ke-001",
        "category": "business_logic",
        "module": "billing",
        "concept": "Pro-rata calculation",
        "detail": "Charges are pro-rated based on remaining days.",
        "related_files": ["src/billing/proration.py"],
        "difficulty": 2,
        "tags": ["billing"],
        "extracted_at": "2026-01-01T00:00:00",
        "source": "code",
        "consumers": ["billing_service"],
    }
    defaults.update(kwargs)
    return KnowledgeEntry(**defaults)


def _make_answer(result: str, **kwargs) -> AnswerRecord:
    defaults: dict = {
        "challenge_id": "ch-001",
        "knowledge_entry_id": "ke-001",
        "challenge_type": "multiple_choice",
        "category": "business_logic",
        "difficulty": 2,
        "result": result,
        "answered_at": "2026-01-01T00:00:00",
    }
    defaults.update(kwargs)
    return AnswerRecord(**defaults)


# ---------------------------------------------------------------------------
# KnowledgeEntry
# ---------------------------------------------------------------------------


class TestKnowledgeEntry:
    def test_creation(self):
        entry = _make_entry()
        assert entry.id == "ke-001"
        assert entry.category == "business_logic"
        assert entry.module == "billing"
        assert entry.difficulty == 2
        assert entry.tags == ["billing"]
        assert entry.consumers == ["billing_service"]

    def test_to_dict_keys(self):
        entry = _make_entry()
        d = entry.to_dict()
        for key in (
            "id",
            "category",
            "module",
            "concept",
            "detail",
            "related_files",
            "difficulty",
            "tags",
            "extracted_at",
            "source",
            "consumers",
        ):
            assert key in d, f"Missing key: {key}"

    def test_from_dict_roundtrip(self):
        entry = _make_entry()
        restored = KnowledgeEntry.from_dict(entry.to_dict())
        assert restored.id == entry.id
        assert restored.category == entry.category
        assert restored.concept == entry.concept
        assert restored.tags == entry.tags
        assert restored.consumers == entry.consumers

    def test_json_serializable(self):
        entry = _make_entry()
        raw = json.dumps(entry.to_dict())
        data = json.loads(raw)
        assert data["id"] == "ke-001"

    def test_empty_lists_default(self):
        entry = KnowledgeEntry(
            id="ke-x",
            category="architecture",
            module="core",
            concept="Layered design",
            detail="Layers separate concerns.",
            difficulty=1,
            extracted_at="2026-01-01T00:00:00",
            source="code",
        )
        assert entry.related_files == []
        assert entry.tags == []
        assert entry.consumers == []


# ---------------------------------------------------------------------------
# Challenge
# ---------------------------------------------------------------------------


class TestChallenge:
    def test_multiple_choice_creation(self):
        ch = Challenge(
            id="ch-001",
            type="multiple_choice",
            knowledge_entry_id="ke-001",
            difficulty=2,
            prompt="What discount does a gold customer receive?",
            context="See billing/proration.py",
            answer="20%",
            options=["10%", "20%", "30%", "no discount"],
            hints=["Check customer_tier logic"],
            scope_files=["src/billing/proration.py"],
        )
        assert ch.type == "multiple_choice"
        assert ch.options == ["10%", "20%", "30%", "no discount"]
        assert ch.answer == "20%"

    def test_explain_why_creation(self):
        ch = Challenge(
            id="ch-002",
            type="explain_why",
            knowledge_entry_id="ke-003",
            difficulty=3,
            prompt="Why do access tokens expire after 15 minutes?",
            context="Auth module",
            answer="Security audit in Q3 2024 mandated shorter token lifetimes.",
            hints=["Consider the security audit history"],
            scope_files=["src/auth/tokens.py"],
        )
        assert ch.type == "explain_why"
        assert ch.options is None

    def test_to_dict_keys(self):
        ch = Challenge(
            id="ch-001",
            type="multiple_choice",
            knowledge_entry_id="ke-001",
            difficulty=1,
            prompt="Question?",
            context="ctx",
            answer="42",
            options=["42", "43"],
            hints=[],
            scope_files=[],
        )
        d = ch.to_dict()
        for key in (
            "id",
            "type",
            "knowledge_entry_id",
            "difficulty",
            "prompt",
            "context",
            "answer",
            "options",
            "hints",
            "scope_files",
        ):
            assert key in d


# ---------------------------------------------------------------------------
# AnswerRecord
# ---------------------------------------------------------------------------


class TestAnswerRecord:
    def test_creation(self):
        ar = _make_answer("pass")
        assert ar.challenge_id == "ch-001"
        assert ar.result == "pass"

    def test_score_pass(self):
        assert _make_answer("pass").score() == 1.0

    def test_score_fail(self):
        assert _make_answer("fail").score() == 0.0

    def test_score_partial(self):
        assert _make_answer("partial").score() == 0.5

    def test_to_dict_roundtrip(self):
        ar = _make_answer("pass")
        restored = AnswerRecord.from_dict(ar.to_dict())
        assert restored.challenge_id == ar.challenge_id
        assert restored.result == ar.result
        assert restored.score() == 1.0


# ---------------------------------------------------------------------------
# DeveloperProgress
# ---------------------------------------------------------------------------


class TestDeveloperProgress:
    def test_empty_progress(self):
        dp = DeveloperProgress(developer_id="dev-1")
        assert dp.overall_accuracy() == 0.0
        assert dp.category_accuracy("business_logic") == 0.0
        assert dp.type_accuracy("multiple_choice") == 0.0
        assert dp.streak == 0

    def test_overall_accuracy_mixed(self):
        """pass=1.0, fail=0.0, partial=0.5 => mean = 0.5"""
        dp = DeveloperProgress(
            developer_id="dev-1",
            history=[
                _make_answer("pass"),
                _make_answer("fail"),
                _make_answer("partial"),
            ],
        )
        assert abs(dp.overall_accuracy() - 0.5) < 1e-9

    def test_category_accuracy(self):
        dp = DeveloperProgress(
            developer_id="dev-1",
            history=[
                _make_answer("pass", category="business_logic"),
                _make_answer("fail", category="business_logic"),
                _make_answer("pass", category="architecture"),
            ],
        )
        assert abs(dp.category_accuracy("business_logic") - 0.5) < 1e-9
        assert dp.category_accuracy("architecture") == 1.0
        assert dp.category_accuracy("data_flow") == 0.0

    def test_type_accuracy(self):
        dp = DeveloperProgress(
            developer_id="dev-1",
            history=[
                _make_answer("pass", challenge_type="multiple_choice"),
                _make_answer("pass", challenge_type="multiple_choice"),
                _make_answer("fail", challenge_type="explain_why"),
            ],
        )
        assert dp.type_accuracy("multiple_choice") == 1.0
        assert dp.type_accuracy("explain_why") == 0.0

    def test_to_dict_from_dict_roundtrip(self):
        dp = DeveloperProgress(
            developer_id="dev-1",
            history=[_make_answer("pass"), _make_answer("fail")],
            streak=3,
        )
        restored = DeveloperProgress.from_dict(dp.to_dict())
        assert restored.developer_id == "dev-1"
        assert len(restored.history) == 2
        assert restored.streak == 3
        assert abs(restored.overall_accuracy() - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# OnboardingProgress
# ---------------------------------------------------------------------------


class TestOnboardingProgress:
    def test_initial_state(self):
        op = OnboardingProgress(developer_id="dev-1")
        assert op.current_stage == 1
        assert op.graduated is False
        assert op.is_graduated() is False

    def test_can_advance_true(self):
        """80% accuracy across 10+ challenges in stage 1 -> can advance."""
        op = OnboardingProgress(
            developer_id="dev-1",
            stage_scores={1: 0.85},
            stage_challenge_count={1: 12},
        )
        assert op.can_advance() is True

    def test_cannot_advance_low_accuracy(self):
        """Below 80% accuracy -> cannot advance."""
        op = OnboardingProgress(
            developer_id="dev-1",
            stage_scores={1: 0.70},
            stage_challenge_count={1: 15},
        )
        assert op.can_advance() is False

    def test_cannot_advance_few_challenges(self):
        """High accuracy but fewer than 10 challenges -> cannot advance."""
        op = OnboardingProgress(
            developer_id="dev-1",
            stage_scores={1: 0.90},
            stage_challenge_count={1: 7},
        )
        assert op.can_advance() is False

    def test_advance_moves_stage(self):
        op = OnboardingProgress(
            developer_id="dev-1",
            stage_scores={1: 0.85},
            stage_challenge_count={1: 12},
        )
        op.advance()
        assert op.current_stage == 2
        assert op.graduated is False

    def test_graduation(self):
        """Advancing past stage 5 graduates the developer."""
        op = OnboardingProgress(
            developer_id="dev-1",
            current_stage=5,
            stage_scores={5: 0.90},
            stage_challenge_count={5: 10},
        )
        op.advance()
        assert op.graduated is True
        assert op.is_graduated() is True

    def test_to_dict_keys(self):
        op = OnboardingProgress(developer_id="dev-1")
        d = op.to_dict()
        for key in (
            "developer_id",
            "current_stage",
            "stage_scores",
            "stage_challenge_count",
            "entries_mastered",
            "graduated",
        ):
            assert key in d
