from __future__ import annotations

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.ml import score_answer_quality
from gauntlet.models import (
    AnswerRecord,
    BankProblem,
    Challenge,
    ChallengeResult,
    ChallengeType,
    DeveloperProgress,
    Difficulty,
    EdgeKind,
    GraphEdge,
    GraphNode,
    KnowledgeEntry,
    NodeKind,
    OnboardingProgress,
)
from gauntlet.problem_bank import load_bank
from gauntlet.query import (
    get_context_for_files,
    query_knowledge,
    validate_understanding,
)

__version__ = "1.9.4"

__all__ = [
    "AnswerRecord",
    "BankProblem",
    "Challenge",
    "ChallengeResult",
    "ChallengeType",
    "DeveloperProgress",
    "Difficulty",
    "EdgeKind",
    "GraphEdge",
    "GraphNode",
    "KnowledgeEntry",
    "KnowledgeStore",
    "NodeKind",
    "OnboardingProgress",
    "get_context_for_files",
    "load_bank",
    "query_knowledge",
    "score_answer_quality",
    "validate_understanding",
]
