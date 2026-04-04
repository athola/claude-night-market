from __future__ import annotations

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.ml import score_answer_quality
from gauntlet.models import (
    AnswerRecord,
    Challenge,
    ChallengeResult,
    ChallengeType,
    DeveloperProgress,
    EdgeKind,
    GraphEdge,
    GraphNode,
    KnowledgeEntry,
    NodeKind,
    OnboardingProgress,
)
from gauntlet.query import (
    get_context_for_files,
    query_knowledge,
    validate_understanding,
)

__version__ = "1.8.1"

__all__ = [
    "AnswerRecord",
    "Challenge",
    "ChallengeResult",
    "ChallengeType",
    "DeveloperProgress",
    "EdgeKind",
    "GraphEdge",
    "GraphNode",
    "KnowledgeEntry",
    "KnowledgeStore",
    "NodeKind",
    "OnboardingProgress",
    "get_context_for_files",
    "query_knowledge",
    "score_answer_quality",
    "validate_understanding",
]
