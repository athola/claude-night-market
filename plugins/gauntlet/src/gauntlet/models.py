"""Data models for the gauntlet plugin."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Graph enums
# ---------------------------------------------------------------------------

_MAX_QUALIFIED_NAME_LEN = 255


class NodeKind(str, Enum):
    """Kinds of structural nodes in the code graph."""

    FILE = "File"
    CLASS = "Class"
    FUNCTION = "Function"
    TYPE = "Type"
    TEST = "Test"

    def __str__(self) -> str:
        return self.value


class EdgeKind(str, Enum):
    """Relationship types between graph nodes."""

    CALLS = "CALLS"
    IMPORTS_FROM = "IMPORTS_FROM"
    INHERITS = "INHERITS"
    CONTAINS = "CONTAINS"
    IMPLEMENTS = "IMPLEMENTS"
    TESTED_BY = "TESTED_BY"

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Graph data models
# ---------------------------------------------------------------------------


def _sanitize_name(name: str) -> str:
    """Strip control characters and enforce max length."""
    cleaned = "".join(ch for ch in name if ord(ch) >= 0x20)
    return cleaned[:_MAX_QUALIFIED_NAME_LEN]


@dataclass
class GraphNode:
    """A structural code entity (file, class, function, type, test)."""

    kind: NodeKind
    qualified_name: str
    file_path: str
    line_start: int
    line_end: int
    language: str = ""
    parent_name: str = ""
    params: dict[str, str] = field(default_factory=dict)
    return_type: str = ""
    modifiers: list[str] = field(default_factory=list)
    is_test: bool = False
    file_hash: str = ""

    def __post_init__(self) -> None:
        self.qualified_name = _sanitize_name(self.qualified_name)
        if self.line_start < 0 or self.line_end < self.line_start:
            msg = f"invalid line range: {self.line_start}-{self.line_end}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "kind": str(self.kind),
            "qualified_name": self.qualified_name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "language": self.language,
            "parent_name": self.parent_name,
            "params": self.params,
            "return_type": self.return_type,
            "modifiers": self.modifiers,
            "is_test": self.is_test,
            "file_hash": self.file_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        """Deserialize from a dictionary."""
        return cls(
            kind=NodeKind(data["kind"]),
            qualified_name=data["qualified_name"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data.get("language", ""),
            parent_name=data.get("parent_name", ""),
            params=data.get("params", {}),
            return_type=data.get("return_type", ""),
            modifiers=data.get("modifiers", []),
            is_test=data.get("is_test", False),
            file_hash=data.get("file_hash", ""),
        )

    def params_json(self) -> str:
        """Return params as JSON string for SQLite storage."""
        return json.dumps(self.params) if self.params else ""

    def modifiers_json(self) -> str:
        """Return modifiers as JSON string for SQLite storage."""
        return json.dumps(self.modifiers) if self.modifiers else ""


@dataclass
class GraphEdge:
    """A relationship between two graph nodes."""

    kind: EdgeKind
    source_qn: str
    target_qn: str
    file_path: str = ""
    line: int = 0

    def __post_init__(self) -> None:
        self.source_qn = _sanitize_name(self.source_qn)
        self.target_qn = _sanitize_name(self.target_qn)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "kind": str(self.kind),
            "source_qn": self.source_qn,
            "target_qn": self.target_qn,
            "file_path": self.file_path,
            "line": self.line,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEdge:
        """Deserialize from a dictionary."""
        return cls(
            kind=EdgeKind(data["kind"]),
            source_qn=data["source_qn"],
            target_qn=data["target_qn"],
            file_path=data.get("file_path", ""),
            line=data.get("line", 0),
        )


class ChallengeResult(str, Enum):
    """Possible outcomes of evaluating a challenge answer."""

    PASS = "pass"  # nosec B105
    PARTIAL = "partial"
    FAIL = "fail"

    def __str__(self) -> str:
        return self.value


class ChallengeType(str, Enum):
    """Fixed set of challenge exercise types."""

    MULTIPLE_CHOICE = "multiple_choice"
    EXPLAIN_WHY = "explain_why"
    TRACE = "trace"
    SPOT_BUG = "spot_bug"
    DEPENDENCY_MAP = "dependency_map"
    CODE_COMPLETION = "code_completion"
    IMPACT_PREDICTION = "impact_prediction"
    DEPENDENCY_TRACE = "dependency_trace"

    def __str__(self) -> str:
        return self.value


@dataclass
class KnowledgeEntry:
    """A single unit of knowledge extracted from the codebase."""

    id: str
    category: str
    module: str
    concept: str
    detail: str
    difficulty: int  # 1-5
    extracted_at: str
    source: str
    related_files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    consumers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            msg = f"difficulty must be 1-5, got {self.difficulty}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "module": self.module,
            "concept": self.concept,
            "detail": self.detail,
            "related_files": self.related_files,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "extracted_at": self.extracted_at,
            "source": self.source,
            "consumers": self.consumers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeEntry:
        """Deserialize from a dictionary."""
        return cls(
            id=data["id"],
            category=data["category"],
            module=data["module"],
            concept=data["concept"],
            detail=data["detail"],
            related_files=data.get("related_files", []),
            difficulty=data["difficulty"],
            tags=data.get("tags", []),
            extracted_at=data["extracted_at"],
            source=data["source"],
            consumers=data.get("consumers", []),
        )


@dataclass
class Challenge:
    """A single challenge question generated from a KnowledgeEntry."""

    id: str
    type: ChallengeType
    knowledge_entry_id: str
    difficulty: int  # 1-5
    prompt: str
    context: str
    answer: str
    hints: list[str] = field(default_factory=list)
    scope_files: list[str] = field(default_factory=list)
    options: list[str] | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            msg = f"difficulty must be 1-5, got {self.difficulty}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "knowledge_entry_id": self.knowledge_entry_id,
            "difficulty": self.difficulty,
            "prompt": self.prompt,
            "context": self.context,
            "answer": self.answer,
            "options": self.options,
            "hints": self.hints,
            "scope_files": self.scope_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Challenge:
        """Deserialize from a dictionary."""
        return cls(
            id=data["id"],
            type=ChallengeType(data["type"]),
            knowledge_entry_id=data["knowledge_entry_id"],
            difficulty=data["difficulty"],
            prompt=data["prompt"],
            context=data["context"],
            answer=data["answer"],
            hints=data.get("hints", []),
            scope_files=data.get("scope_files", []),
            options=data.get("options"),
        )


@dataclass
class AnswerRecord:
    """A record of a developer's answer to a challenge."""

    challenge_id: str
    knowledge_entry_id: str
    challenge_type: ChallengeType
    category: str
    difficulty: int  # 1-5
    result: ChallengeResult
    answered_at: str

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            msg = f"difficulty must be 1-5, got {self.difficulty}"
            raise ValueError(msg)

    def score(self) -> float:
        """Return a numeric score: pass=1.0, partial=0.5, fail=0.0."""
        if self.result == "pass":
            return 1.0
        if self.result == "partial":
            return 0.5
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "challenge_id": self.challenge_id,
            "knowledge_entry_id": self.knowledge_entry_id,
            "challenge_type": self.challenge_type,
            "category": self.category,
            "difficulty": self.difficulty,
            "result": self.result,
            "answered_at": self.answered_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnswerRecord:
        """Deserialize from a dictionary."""
        return cls(
            challenge_id=data["challenge_id"],
            knowledge_entry_id=data["knowledge_entry_id"],
            challenge_type=ChallengeType(data["challenge_type"]),
            category=data["category"],
            difficulty=data["difficulty"],
            result=ChallengeResult(data["result"]),
            answered_at=data["answered_at"],
        )


@dataclass
class DeveloperProgress:
    """Tracks a developer's challenge history and performance metrics."""

    developer_id: str
    history: list[AnswerRecord] = field(default_factory=list)
    last_seen: dict[str, str] = field(default_factory=dict)
    streak: int = 0

    def overall_accuracy(self) -> float:
        """Return mean score across all answer records."""
        if not self.history:
            return 0.0
        return sum(r.score() for r in self.history) / len(self.history)

    def category_accuracy(self, category: str) -> float:
        """Return mean score for a specific knowledge category."""
        records = [r for r in self.history if r.category == category]
        if not records:
            return 0.0
        return sum(r.score() for r in records) / len(records)

    def type_accuracy(self, challenge_type: str) -> float:
        """Return mean score for a specific challenge type."""
        records = [r for r in self.history if r.challenge_type == challenge_type]
        if not records:
            return 0.0
        return sum(r.score() for r in records) / len(records)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "developer_id": self.developer_id,
            "history": [r.to_dict() for r in self.history],
            "last_seen": self.last_seen,
            "streak": self.streak,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeveloperProgress:
        """Deserialize from a dictionary."""
        return cls(
            developer_id=data["developer_id"],
            history=[AnswerRecord.from_dict(r) for r in data.get("history", [])],
            last_seen=data.get("last_seen", {}),
            streak=data.get("streak", 0),
        )


_MAX_STAGE = 5


@dataclass
class OnboardingProgress:
    """Tracks a developer's progress through the five onboarding stages."""

    developer_id: str
    current_stage: int = 1
    stage_scores: dict[int, float] = field(default_factory=dict)
    stage_challenge_count: dict[int, int] = field(default_factory=dict)
    entries_mastered: list[str] = field(default_factory=list)
    graduated: bool = False

    def can_advance(self) -> bool:
        """Return True when accuracy >= 80% across 10+ challenges in the current stage."""
        score = self.stage_scores.get(self.current_stage, 0.0)
        count = self.stage_challenge_count.get(self.current_stage, 0)
        return score >= 0.8 and count >= 10

    def advance(self) -> None:
        """Move to the next stage, or graduate if already on the final stage.

        Raises ValueError if can_advance() precondition is not met.
        """
        if not self.can_advance():
            msg = (
                f"Cannot advance from stage {self.current_stage}: requirements not met"
            )
            raise ValueError(msg)
        if self.current_stage >= _MAX_STAGE:
            self.graduated = True
        else:
            self.current_stage += 1

    def is_graduated(self) -> bool:
        """Return True if the developer has completed all onboarding stages."""
        return self.graduated

    def __post_init__(self) -> None:
        if not 1 <= self.current_stage <= _MAX_STAGE:
            msg = f"current_stage must be 1-{_MAX_STAGE}, got {self.current_stage}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "developer_id": self.developer_id,
            "current_stage": self.current_stage,
            "stage_scores": self.stage_scores,
            "stage_challenge_count": self.stage_challenge_count,
            "entries_mastered": self.entries_mastered,
            "graduated": self.graduated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OnboardingProgress:
        """Deserialize from a dictionary."""
        return cls(
            developer_id=data["developer_id"],
            current_stage=data.get("current_stage", 1),
            stage_scores={int(k): v for k, v in data.get("stage_scores", {}).items()},
            stage_challenge_count={
                int(k): v for k, v in data.get("stage_challenge_count", {}).items()
            },
            entries_mastered=data.get("entries_mastered", []),
            graduated=data.get("graduated", False),
        )
